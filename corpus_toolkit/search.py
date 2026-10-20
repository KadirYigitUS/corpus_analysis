"""The search engine (Chapter 6): find *nodes* by token, lemma, pattern, POS and context.

A :class:`SearchQuery` bundles every option the student can set; :class:`CorpusSearchEngine`
applies it to any selection of texts and returns a :class:`SearchResult` (a tidy hit table).
Hits then feed the concordancer (:mod:`corpus_toolkit.kwic`), batch statistics
(:mod:`corpus_toolkit.batch_kwic`) and collocation analysis.

========================  =====================================================================
option                    meaning
========================  =====================================================================
``terms``                 words to find (one or many → aggregated "KWIC list")
``field``                 ``'tok'`` surface form or ``'lem'`` lemma
``match``                 ``'exact'``, ``'glob'`` (``gel*``, ``?ldu``) or ``'regex'``
``case_sensitive``        default off; Turkish ``İ/I`` handled correctly
``pos``                   keep only nodes whose UPOS is in this set (e.g. ``{'NOUN'}``)
``collocate``             require one of these words within ``collocate_span`` of the node
``filter_function_words`` search the *content* view (see :mod:`corpus_toolkit.filters`)
``mode``                  ``'drop'`` or ``'mask'`` – how spans count removed function words
========================  =====================================================================
"""

import fnmatch
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Literal

import numpy as np
import pandas as pd

from .lazy import LazyCorpusText
from .textutil import LANG_TR, clean_lemma, fold, split_in_token_punct, strip_in_token_punct
from .tokenview import Field, Mode, PunctMode, TokenView

Match = Literal["exact", "glob", "regex"]



@dataclass
class SearchQuery:
    """All search options in one object (``dataclasses.replace`` makes variants cheaply)."""

    terms: list[str]
    field: Field = "lem"
    match: Match = "exact"
    case_sensitive: bool = False
    pos: set[str] | None = None
    collocate: list[str] | None = None
    collocate_span: tuple[int, int] = (5, 5)
    sentence_clamped: bool = True
    filter_function_words: bool = False
    mode: Mode = "drop"
    punct: PunctMode | bool = "drop"

    def __post_init__(self) -> None:
        if isinstance(self.terms, str):  # forgiving: a bare string is one term
            self.terms = [self.terms]
        if self.match not in ("exact", "glob", "regex"):
            raise ValueError("match must be 'exact', 'glob' or 'regex'")
        if isinstance(self.punct, bool):
            self.punct = "keep" if self.punct else "drop"
        if self.punct not in ("keep", "drop", "strip", "split"):
            raise ValueError("punct must be 'keep', 'drop', 'strip', or 'split'")

    def describe(self) -> str:
        parts = [f"terms={self.terms}", f"field={'lemma' if self.field == 'lem' else 'token'}",
                 f"match={self.match}", f"view={'content' if self.filter_function_words else 'raw'}"
                 + (f"/{self.mode}" if self.filter_function_words else "")]
        if self.punct != "drop":
            parts.append(f"punct={self.punct}")
        if self.pos:
            parts.append(f"UPOS∈{sorted(self.pos)}")
        if self.collocate:
            parts.append(f"with {self.collocate} within −{self.collocate_span[0]}/+"
                         f"{self.collocate_span[1]}")
        return "; ".join(parts)


def _pattern_mask(forms_unique: np.ndarray, terms: list[str], match: Match, language: str,
                  case_sensitive: bool, punct: str = "drop", field: str = "tok") -> np.ndarray:
    """Boolean mask over *unique* forms matching any term (cheap: |types| ≪ |tokens|)."""
    if field == "lem" and language == LANG_TR and match != "regex":
        norm_terms = [clean_lemma(t, language) for t in terms]
    else:
        norm_terms = terms

    if match == "exact":
        if punct == "strip":
            wanted = {strip_in_token_punct(t if case_sensitive else fold(t, language)) for t in norm_terms}
            wanted.discard("")
        elif punct == "split":
            wanted = set()
            for t in norm_terms:
                target = t if case_sensitive else fold(t, language)
                for part in split_in_token_punct(target):
                    wanted.add(part)
        else:
            wanted = {t if case_sensitive else fold(t, language) for t in norm_terms}
        return np.isin(forms_unique, list(wanted))

    flags = 0 if case_sensitive else re.IGNORECASE
    pats = []
    for t in norm_terms:
        if match == "glob":
            pats.append(re.compile(fnmatch.translate(t if case_sensitive else fold(t, language)),
                                   flags))
        else:
            pats.append(re.compile(t, flags))
    return np.array([any(p.search(str(u)) for p in pats) for u in forms_unique], dtype=bool)


def find_nodes(view: TokenView, query: SearchQuery) -> np.ndarray:
    """Positions (in ``view``) of every hit of ``query``."""
    lang = view.text.record.language
    uniq, inv = np.unique(view.forms.astype(str), return_inverse=True)
    good = _pattern_mask(uniq, query.terms, query.match, lang, query.case_sensitive,
                         punct=str(query.punct), field=str(query.field))
    mask = good[inv] & view.eligible
    if query.pos:
        tags = view.text.tokens["pos"].to_numpy()[view.rows].astype(str)
        mask &= np.isin(tags, list(query.pos))

    pos = np.flatnonzero(mask)
    if query.collocate and len(pos):
        col = view.occurrences(query.collocate)
        ind = np.zeros(len(view.forms) + 1, dtype=np.int64)
        ind[col + 1] = 1
        cum = np.cumsum(ind)  # cum[k] = number of collocates at positions < k
        left, right = query.collocate_span
        lo_b, hi_b = view.sentence_bounds() if query.sentence_clamped else (None, None)
        lo = np.maximum(pos - left, lo_b[pos] if lo_b is not None else 0)
        hi = np.minimum(pos + right, hi_b[pos] if hi_b is not None else len(view.forms) - 1)
        inside = cum[hi + 1] - cum[lo]
        self_is_col = np.isin(pos, col).astype(np.int64)  # a node does not collocate with itself
        pos = pos[(inside - self_is_col) > 0]
    return pos


@dataclass
class SearchResult:
    """Hit table plus the query that produced it."""

    query: SearchQuery
    hits: pd.DataFrame
    totals: pd.DataFrame = field(default_factory=pd.DataFrame)

    def __len__(self) -> int:
        return len(self.hits)

    def positions(self, code: str) -> np.ndarray:
        h = self.hits[self.hits["code"] == code]
        return h["pos_in_view"].to_numpy()

    def summary(self) -> pd.DataFrame:
        """Hits per text with ``per10k`` (hits / eligible running words × 10 000)."""
        return self.totals


class CorpusSearchEngine:
    """Run a :class:`SearchQuery` over lazy texts, evicting each from RAM after use."""

    def search(self, query: SearchQuery, texts: Iterable[LazyCorpusText],
               evict: bool = True) -> SearchResult:
        frames, totals = [], []
        for text in texts:
            view = TokenView(text, query.field, query.filter_function_words, query.mode,
                             case_fold=not query.case_sensitive, punct=query.punct)
            pos = find_nodes(view, query)
            rec = text.record
            rows = view.rows[pos]
            tab = text.tokens
            sent = text.sentences
            sids = view.sid[pos]
            ch = sent["ch_no"].to_numpy()[sids]
            pa = sent["p_no"].to_numpy()[sids]
            sn = sent["s_no"].to_numpy()[sids]
            frames.append(pd.DataFrame({
                "code": rec.code, "title": rec.title, "language": rec.language,
                "type": rec.corpus_type, "pos_in_view": pos, "row": rows, "sid": sids,
                "ch_no": ch, "p_no": pa, "s_no": sn,
                "ti": tab["ti"].to_numpy()[rows] + 1,
                "token": tab["tok"].to_numpy()[rows].astype(str),
                "lemma": tab["lem"].to_numpy()[rows].astype(str),
                "form": view.forms[pos].astype(str),
                "upos": tab["pos"].to_numpy()[rows].astype(str),
            }))
            n = len(view)
            totals.append({"code": rec.code, "title": rec.title, "language": rec.language,
                           "type": rec.corpus_type, "hits": int(len(pos)), "running_words": n,
                           "per10k": 1e4 * len(pos) / n if n else np.nan})
            if evict:
                text.evict()
        hits = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        return SearchResult(query, hits, pd.DataFrame(totals))
