"""Lazy, memory-preserving access to one text.

``LazyCorpusText`` never opens a pickle until a column is requested, and when it does, it
converts the sentence-per-row DataFrame (list columns stored as *strings*) into a compact
**token table** (one row per token, ``category`` dtypes, ``int8``/``int16`` where possible)
that is cached as Parquet.  Subsequent sessions read the cache (<0.2 s) instead of parsing.

Token table columns
-------------------
``sid``  sentence index in the text (0-based)   ``ti``    token position in sentence (0-based)
``tok``  surface form                           ``lem``   lemma
``pos``  UPOS tag                               ``morph`` morphological analysis string
``head`` 1-based head index (0 = root)          ``rel``   dependency relation
``fcl``  0 content / 1 function / 2 punct       (see :mod:`corpus_toolkit.filters`)

Sentence table columns: ``sid, ch_no, p_no, s_no, sentence, ntok, start``  (``start`` is the
row offset of the sentence's first token, so a sentence slice is ``tokens.iloc[start:start+ntok]``).
"""

import ast
import gc
import lzma
import pickle
from typing import Any

import numpy as np
import pandas as pd

from .cache import CorpusCacheManager, file_signature
from .errors import CorpusDataError
from .filters import classify_arrays
from .registry import TextRecord
from .textutil import LANG_TR, clean_lemma

_LIST_COLS = ("tokens", "lemma", "pos", "morph", "dep")



def rss_mb() -> float:
    """Resident memory of this process in MB (0.0 when psutil is unavailable)."""
    try:
        import psutil

        return psutil.Process().memory_info().rss / 1e6
    except Exception:  # pragma: no cover - psutil is optional
        return 0.0


def _as_list(value: Any) -> list[Any]:
    """Cells are stringified lists in the stored pickles; accept real lists too."""
    if isinstance(value, str):
        return list(ast.literal_eval(value))
    if isinstance(value, (list, tuple, np.ndarray)):
        return list(value)
    raise CorpusDataError(f"Unparseable list cell of type {type(value).__name__}")


def _dep_pair(elem: Any) -> tuple[int, str]:
    """Normalise a dep element to ``(head, rel)`` (handles 2-tuples, 4-tuples and dicts)."""
    if isinstance(elem, dict):
        return int(elem["head_idx"]), str(elem["rel"])
    if len(elem) == 4:
        return int(elem[2]), str(elem[3])
    return int(elem[0]), str(elem[1])


def build_tables(raw: pd.DataFrame, language: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Flatten a sentence-level DataFrame into (tokens, sentences) tables."""
    missing = [c for c in ("ch_no", "p_no", "s_no", "sentence", *_LIST_COLS) if c not in raw]
    if missing:
        raise CorpusDataError(f"Pickle lacks required columns: {missing}")
    raw = raw.sort_values(["ch_no", "p_no", "s_no"], kind="mergesort").reset_index(drop=True)

    sid: list[int] = []
    ti: list[int] = []
    head: list[int] = []
    rel: list[str] = []
    tok, lem, pos, morph = ([] for _ in range(4))
    ntoks: list[int] = []
    for i, row in enumerate(raw.itertuples(index=False)):
        t, lm, p, m = (_as_list(getattr(row, c)) for c in ("tokens", "lemma", "pos", "morph"))
        d = [_dep_pair(e) for e in _as_list(row.dep)]
        n = len(t)
        if not (n == len(lm) == len(p) == len(m) == len(d)):
            raise CorpusDataError(
                f"Sentence {i} (ch,p,s)=({row.ch_no},{row.p_no},{row.s_no}) has misaligned "
                f"columns: {n},{len(lm)},{len(p)},{len(m)},{len(d)}")
        if language == LANG_TR:
            lm = [clean_lemma(x, LANG_TR) if isinstance(x, str) else x for x in lm]
        ntoks.append(n)
        sid.extend([i] * n)
        ti.extend(range(n))
        tok.extend(t)
        lem.extend(lm)
        pos.extend(p)

        morph.extend(m)
        head.extend(h for h, _ in d)
        rel.extend(r for _, r in d)

    pos_arr, morph_arr = np.asarray(pos, dtype=object), np.asarray(morph, dtype=object)
    tokens = pd.DataFrame({
        "sid": np.asarray(sid, dtype=np.int32),
        "ti": np.asarray(ti, dtype=np.int16),
        "tok": pd.Categorical(tok),
        "lem": pd.Categorical(lem),
        "pos": pd.Categorical(pos),
        "morph": pd.Categorical(morph),
        "head": np.asarray(head, dtype=np.int16),
        "rel": pd.Categorical(rel),
        "fcl": classify_arrays(pos_arr, morph_arr, language),
    })
    starts = np.concatenate([[0], np.cumsum(ntoks)[:-1]]).astype(np.int64)
    sentences = pd.DataFrame({
        "sid": np.arange(len(raw), dtype=np.int32),
        "ch_no": raw["ch_no"].astype(np.int32).to_numpy(),
        "p_no": raw["p_no"].astype(np.int32).to_numpy(),
        "s_no": raw["s_no"].astype(np.int32).to_numpy(),
        "sentence": raw["sentence"].astype(str).to_numpy(),
        "ntok": np.asarray(ntoks, dtype=np.int32),
        "start": starts,
    })
    return tokens, sentences


def read_pickle_xz(path: Any) -> pd.DataFrame:
    """Load a ``.pickle.xz`` DataFrame (lzma-compressed pickle)."""
    with lzma.open(path, "rb") as fh:
        obj = pickle.load(fh)  # noqa: S301 - trusted local thesis data
    if not isinstance(obj, pd.DataFrame):
        raise CorpusDataError(f"{path} does not contain a DataFrame.")
    return obj


class LazyCorpusText:
    """One text whose tables are materialised on first use and can be :meth:`evict`-ed."""

    def __init__(self, record: TextRecord, cache: CorpusCacheManager) -> None:
        self.record = record
        self.cache = cache
        self._tokens: pd.DataFrame | None = None
        self._sentences: pd.DataFrame | None = None

    # ----------------------------------------------------------------- keys
    @property
    def _sig(self) -> str:
        return file_signature(self.record.pickle_path)

    def _key(self, kind: str) -> str:
        return self.cache.key(kind, self.record.code, self._sig)

    # ---------------------------------------------------------------- loading
    def _ensure(self) -> None:
        if self._tokens is not None and self._sentences is not None:
            return
        tk, sk = self._key("tok"), self._key("sent")
        tokens, sentences = self.cache.load_frame(tk), self.cache.load_frame(sk)
        if tokens is None or sentences is None:
            raw = read_pickle_xz(self.record.pickle_path)
            tokens, sentences = build_tables(raw, self.record.language)
            del raw
            gc.collect()
            self.cache.save_frame(tk, tokens)
            self.cache.save_frame(sk, sentences)
            self.cache.save_json(self._key("meta"), {
                "code": self.record.code, "n_tokens": int(len(tokens)),
                "n_sentences": int(len(sentences))})
        self._tokens, self._sentences = tokens, sentences

    @property
    def tokens(self) -> pd.DataFrame:
        self._ensure()
        assert self._tokens is not None
        return self._tokens

    @property
    def sentences(self) -> pd.DataFrame:
        self._ensure()
        assert self._sentences is not None
        return self._sentences

    @property
    def loaded(self) -> bool:
        return self._tokens is not None

    def is_loaded(self) -> bool:
        """Alias method for ``self.loaded``."""
        return self.loaded

    def summary(self) -> dict[str, Any]:
        """Cheap counts; read from the cached meta file when the tables are not in RAM."""
        meta = self.cache.load_json(self._key("meta"))
        if meta is None:
            self._ensure()
            meta = self.cache.load_json(self._key("meta")) or {}
        return {"code": self.record.code, "title": self.record.title,
                "n_tokens": meta.get("n_tokens"), "n_sentences": meta.get("n_sentences")}

    # ----------------------------------------------------------------- memory
    def memory_mb(self) -> float:
        if not self.loaded:
            return 0.0
        return float(self.tokens.memory_usage(deep=True).sum()
                     + self.sentences.memory_usage(deep=True).sum()) / 1e6

    def evict(self, *, verbose: bool = False) -> None:
        """Drop the in-memory tables (the Parquet cache is untouched)."""
        before = rss_mb()
        self._tokens = self._sentences = None
        gc.collect()
        if verbose:
            print(f"♻️  evicted {self.record.code}: RSS {before:.0f} → {rss_mb():.0f} MB")

    def __enter__(self) -> "LazyCorpusText":
        self._ensure()
        return self

    def __exit__(self, *exc: object) -> None:
        self.evict()

    def __repr__(self) -> str:
        state = "in RAM" if self.loaded else "lazy"
        return f"<LazyCorpusText {self.record.code} '{self.record.title}' ({state})>"
