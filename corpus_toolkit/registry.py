"""Corpus registry: *which* texts exist, who wrote/translated them, and where they live.

The registry is pure metadata (no pickle is opened here).  It is built from the two thesis
TSVs, restricted to the focal author-translators, and resolves pickle paths with the same
rules as ``passim_analysis`` (exact ``{code}.pickle.xz``, else the newest
``{code}*.pickle.xz``; stale absolute paths in the TSV are re-based under the configured
data root).

Everything user-facing goes through :meth:`CorpusRegistry.display`, which always prints the
**full author name and full book title** next to the short code.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .config import CorpusPathConfig
from .errors import CorpusDataError, CorpusSelectionError
from .textutil import LANG_EN, LANG_TR, loose_key

SOURCE = "source"  # English original of a translation pair
TRANSLATION = "translation"  # Turkish translation
INDIGENOUS = "indigenous"  # Turkish original SF by the same author-translator
CORPUS_TYPES = (SOURCE, TRANSLATION, INDIGENOUS)


@dataclass(frozen=True)
class TextRecord:
    """Metadata of one text (one pickle)."""

    code: str
    language: str
    corpus_type: str
    title: str
    creator: str  # author (English sources) or translator/author (Turkish texts)
    year: int
    focal_code: str  # code of the author-translator this text belongs to
    focal_name: str  # full name of the author-translator
    pickle_path: Path
    pair_id: str = ""  # alignment folder id (translations & sources only)

    @property
    def label(self) -> str:
        return f"{self.title} [{self.code}]"


@dataclass(frozen=True)
class PairSpec:
    """One English-source / Turkish-translation pair with its alignment artifacts."""

    pair_id: str
    folder: Path
    eng: TextRecord
    tur: TextRecord

    def artifact(self, kind: str) -> Path:
        """``kind`` in ``alignment`` | ``dict_eng`` | ``dict_tur`` | ``map_eng`` | ``map_tur``."""
        names = {
            "alignment": f"{self.folder.name}_alignment.pickle",
            "dict_eng": f"{self.folder.name}_sentence_dict_eng.pickle",
            "dict_tur": f"{self.folder.name}_sentence_dict_tur.pickle",
            "map_eng": f"{self.folder.name}_sentence_map_eng.pickle",
            "map_tur": f"{self.folder.name}_sentence_map_tur.pickle",
        }
        if kind not in names:
            raise CorpusSelectionError(f"Unknown alignment artifact '{kind}'.")
        return self.folder / names[kind]


def _rebase_dir(raw: str, root: Path, fallback_name: str = "") -> Path:
    """Resolve a (possibly stale) directory from the TSV against ``root``."""
    candidates = [Path(raw).name] if raw else []
    if fallback_name:
        candidates.append(fallback_name)
    if raw and Path(raw).is_dir():
        return Path(raw).resolve()
    for name in candidates:
        direct = root / name
        if direct.is_dir():
            return direct.resolve()
        if root.is_dir():
            for child in sorted(root.iterdir()):
                if child.is_dir() and child.name.lower() == name.lower():
                    return child.resolve()
    raise CorpusDataError(f"Cannot resolve directory '{raw}' under '{root}'.")


def _select_pickle(directory: Path, code: str) -> Path:
    """Exact ``{code}.pickle.xz`` else newest ``{code}*.pickle.xz`` (``.bak`` never matches)."""
    exact = directory / f"{code}.pickle.xz"
    if exact.is_file():
        return exact.resolve()
    matches = sorted(directory.glob(f"{code}*.pickle.xz"))
    if matches:
        return matches[-1].resolve()
    raise CorpusDataError(f"No '{code}*.pickle.xz' in '{directory}'.")


class CorpusRegistry:
    """Metadata catalogue of the focal sub-corpus (5 pairs + 3 indigenous = 13 texts)."""

    def __init__(self, texts: Iterable[TextRecord], pairs: Iterable[PairSpec],
                 author_names: dict[str, str]) -> None:
        self.texts: dict[str, TextRecord] = {t.code: t for t in texts}
        self.pairs: dict[str, PairSpec] = {p.pair_id: p for p in pairs}
        self.author_names = dict(author_names)  # code -> full name

    # ------------------------------------------------------------------ build
    @classmethod
    def from_config(cls, config: CorpusPathConfig | None = None) -> "CorpusRegistry":
        cfg = config or CorpusPathConfig.from_env()
        for tsv in (cfg.translation_tsv, cfg.indigenous_tsv):
            if not tsv.is_file():
                raise CorpusDataError(f"Metadata file not found: {tsv}")
        allowed = set(cfg.author_codes)
        trans = pd.read_csv(cfg.translation_tsv, sep="\t", dtype=str).fillna("")
        indig = pd.read_csv(cfg.indigenous_tsv, sep="\t", dtype=str).fillna("")
        trans = trans[trans["tur_author_code"].str.strip().isin(allowed)]
        indig = indig[indig["tur_author_code"].str.strip().isin(allowed)]

        texts: list[TextRecord] = []
        pairs: list[PairSpec] = []
        names: dict[str, str] = {}
        for _, r in trans.iterrows():
            focal, focal_name = r["tur_author_code"].strip(), r["tur_author"].strip()
            names[focal] = focal_name
            folder = _rebase_dir(r["processed_aligned_files_loc"], cfg.aligned_root,
                                 r["alignment_code"].strip())
            pid = folder.name
            eng = TextRecord(
                code=r["eng_file_code"].strip(), language=LANG_EN, corpus_type=SOURCE,
                title=r["eng_book_title"].strip(), creator=r["eng_author"].strip(),
                year=int(r["eng_year"]), focal_code=focal, focal_name=focal_name,
                pickle_path=_select_pickle(folder, r["eng_file_code"].strip()), pair_id=pid)
            tur = TextRecord(
                code=r["tur_file_code"].strip(), language=LANG_TR, corpus_type=TRANSLATION,
                title=r["tur_book_title"].strip(), creator=focal_name,
                year=int(r["tur_year"]), focal_code=focal, focal_name=focal_name,
                pickle_path=_select_pickle(folder, r["tur_file_code"].strip()), pair_id=pid)
            texts.extend([eng, tur])
            pairs.append(PairSpec(pid, folder, eng, tur))
        for _, r in indig.iterrows():
            focal, focal_name = r["tur_author_code"].strip(), r["tur_author"].strip()
            names[focal] = focal_name
            code = r["tur_file_code"].strip()
            folder = _rebase_dir(r["processed_indigenous_files"], cfg.indigenous_root, code)
            texts.append(TextRecord(
                code=code, language=LANG_TR, corpus_type=INDIGENOUS,
                title=r["tur_book_title"].strip(), creator=focal_name, year=int(r["tur_year"]),
                focal_code=focal, focal_name=focal_name,
                pickle_path=_select_pickle(folder, code)))
        return cls(texts, pairs, names)

    # ----------------------------------------------------------------- lookup
    def resolve_author(self, query: str) -> str:
        """Accept a code (``'SM'``) or a full/loosely typed name (``'selma mine'``)."""
        q = query.strip()
        if q.upper() in self.author_names:
            return q.upper()
        key = loose_key(q)
        for code, name in self.author_names.items():
            if loose_key(name) == key or (key and key in loose_key(name)):
                return code
        raise CorpusSelectionError(
            f"Unknown author '{query}'. Choose one of: "
            + ", ".join(f"{n} ({c})" for c, n in self.author_names.items()))

    def resolve_text(self, query: str) -> TextRecord:
        """Accept a code (``'BR-SM'``) or a (partial, diacritic-free) title."""
        q = query.strip()
        if q in self.texts:
            return self.texts[q]
        if q.upper() in self.texts:
            return self.texts[q.upper()]
        key = loose_key(q)
        hits = [t for t in self.texts.values() if key and key in loose_key(t.title)]
        exact = [t for t in hits if loose_key(t.title) == key]
        hits = exact or hits
        if len(hits) == 1:
            return hits[0]
        if not hits:
            raise CorpusSelectionError(f"Unknown text '{query}'. Run `registry.inventory()`.")
        raise CorpusSelectionError(
            f"'{query}' is ambiguous: " + "; ".join(self.display(t) for t in hits))

    def title_of(self, query: str) -> str:
        """Resolve a code or title query and return its full canonical title."""
        try:
            return self.resolve_text(query).title
        except Exception:
            return str(query)

    def select(self, *, language: str | None = None, corpus_type: str | None = None,
               author: str | None = None) -> list[TextRecord]:
        """Filter texts; ``author`` is resolved to a focal author-translator code."""
        focal = self.resolve_author(author) if author else None
        out = [t for t in self.texts.values()
               if (language is None or t.language == language)
               and (corpus_type is None or t.corpus_type == corpus_type)
               and (focal is None or t.focal_code == focal)]
        return sorted(out, key=lambda t: (t.focal_code, t.corpus_type, t.code))

    def pair_for(self, code: str) -> PairSpec:
        rec = self.resolve_text(code)
        if not rec.pair_id:
            raise CorpusSelectionError(f"{self.display(rec)} is not part of a translation pair.")
        return self.pairs[rec.pair_id]

    # ---------------------------------------------------------------- display
    _TYPE_LABEL = {SOURCE: "English source", TRANSLATION: "Turkish translation",
                   INDIGENOUS: "Turkish indigenous"}

    def display(self, rec: "TextRecord | object") -> str:
        """Human string with full names, e.g. ``Selma Mine — Ben, Robot… [BR-SM] (1983, …)``.

        Accepts a :class:`TextRecord` or anything carrying one in ``.record`` (a lazy text).
        """
        rec = getattr(rec, "record", rec)  # type: ignore[assignment]
        assert isinstance(rec, TextRecord)
        who = rec.creator if rec.corpus_type == SOURCE else rec.focal_name
        extra = (f"; source author: {rec.creator}; related to {rec.focal_name}"
                 if rec.corpus_type == SOURCE else "")
        return (f"{who} — {rec.title} [{rec.code}] "
                f"({rec.year}, {self._TYPE_LABEL[rec.corpus_type]}{extra})")

    def display_pair(self, pair: PairSpec) -> str:
        return (f"{pair.eng.title} ({pair.eng.creator}, {pair.eng.year}) → "
                f"{pair.tur.title} ({pair.tur.focal_name}, {pair.tur.year}) "
                f"[{pair.eng.code} ⇄ {pair.tur.code}]")

    def inventory(self) -> pd.DataFrame:
        """One row per text with full names; the first thing a student should look at."""
        rows = [{
            "author_translator": t.focal_name, "focal_code": t.focal_code,
            "title": t.title, "code": t.code, "language": t.language,
            "type": self._TYPE_LABEL[t.corpus_type], "year": t.year,
            "creator": t.creator, "pair": t.pair_id,
        } for t in self.select()]
        return pd.DataFrame(rows)

    def verify_files(self) -> pd.DataFrame:
        """Check that every pickle (and alignment artifact) exists on disk."""
        rows = [{"code": t.code, "file": t.pickle_path.name, "exists": t.pickle_path.is_file(),
                 "size_mb": round(t.pickle_path.stat().st_size / 1e6, 2)
                 if t.pickle_path.is_file() else 0.0} for t in self.select()]
        return pd.DataFrame(rows)
