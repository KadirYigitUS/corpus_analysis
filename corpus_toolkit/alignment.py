"""Sentence-alignment structure of the parallel corpus (Chapter 3).

Sentence aligners (here Bleualign/LASER-style, stored as ``*_alignment.pickle``) pair *groups*
of sentences.  The group shape reveals translator decisions (Toury 2012; Baker 1993):

========  ========================  ===============================================
type      shape (English, Turkish)  translational reading
========  ========================  ===============================================
1:1       (1, 1)                    sentence kept intact
1:N       (1, n≥2)                  English sentence **split** in Turkish
N:1       (n≥2, 1)                  English sentences **merged** in Turkish
N:M       (n≥2, m≥2)                restructuring
omission  (n, 0)                    English material with no Turkish counterpart
addition  (0, m)                    Turkish material with no English counterpart
========  ========================  ===============================================

Cardinality comes from the ``sentence_map_*`` pickles: ``len(map[ai])`` sentences on each side.
``R_sent`` = Turkish sentences / English sentences (>1 means Turkish uses more sentences).
"""

import pickle
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .cache import CorpusCacheManager, file_signature
from .errors import CorpusDataError
from .registry import PairSpec

ALIGN_TYPES = ("1:1", "1:N", "N:1", "N:M", "omission", "addition")


def alignment_type(n_eng: int, n_tur: int) -> str:
    """Classify an alignment group by its (English, Turkish) sentence counts."""
    if n_eng == 0 and n_tur == 0:
        return "empty"
    if n_tur == 0:
        return "omission"
    if n_eng == 0:
        return "addition"
    if n_eng == 1 and n_tur == 1:
        return "1:1"
    if n_eng == 1:
        return "1:N"
    if n_tur == 1:
        return "N:1"
    return "N:M"


def _load_pickle(path: Path) -> Any:
    if not path.is_file():
        raise CorpusDataError(f"Missing alignment artifact: {path}")
    with open(path, "rb") as fh:
        return pickle.load(fh)  # noqa: S301 - trusted local thesis data


@dataclass
class AlignmentIndex:
    """Coordinates ⇄ alignment-id lookups for one pair (small: a few thousand entries)."""

    pair: PairSpec

    @cached_property
    def frame(self) -> pd.DataFrame:
        return _load_pickle(self.pair.artifact("alignment"))

    @cached_property
    def map_eng(self) -> dict[int, list[tuple[int, int, int]]]:
        return _load_pickle(self.pair.artifact("map_eng"))

    @cached_property
    def map_tur(self) -> dict[int, list[tuple[int, int, int]]]:
        return _load_pickle(self.pair.artifact("map_tur"))

    @cached_property
    def _reverse(self) -> dict[str, dict[tuple[int, int, int], int]]:
        rev: dict[str, dict[tuple[int, int, int], int]] = {"en": {}, "tr": {}}
        for lang, mp in (("en", self.map_eng), ("tr", self.map_tur)):
            for ai, coords in mp.items():
                for c in coords:
                    rev[lang][(int(c[0]), int(c[1]), int(c[2]))] = ai
        return rev

    def ai_of(self, language: str, coord: tuple[int, int, int]) -> int | None:
        """Alignment id containing sentence ``(ch_no, p_no, s_no)`` (None if unaligned)."""
        return self._reverse[language].get((int(coord[0]), int(coord[1]), int(coord[2])))

    def texts(self, ai: int) -> tuple[str, str]:
        """(English, Turkish) text of an alignment group."""
        row = self.frame.xs(ai, level="ai")
        if row.empty:
            return "", ""
        return str(row.iloc[0]["eng"]), str(row.iloc[0]["tur"])

    def coords(self, ai: int) -> tuple[list[tuple[int, int, int]], list[tuple[int, int, int]]]:
        return list(self.map_eng.get(ai, [])), list(self.map_tur.get(ai, []))

    def table(self) -> pd.DataFrame:
        """Alignment pairs as a DataFrame with 'file_no' and 'ai' columns."""
        return self.frame.reset_index()


class AlignmentStructureAnalyzer:
    """Counts and ratios of alignment types per pair (Figures 1A/1B)."""

    def __init__(self, cache: CorpusCacheManager) -> None:
        self.cache = cache

    def cardinality_table(self, pair: PairSpec) -> pd.DataFrame:
        """One row per alignment group: ids, counts, type, token/char lengths."""
        sig = "|".join(file_signature(pair.artifact(k))
                       for k in ("alignment", "map_eng", "map_tur"))
        key = self.cache.key("align", pair.pair_id, sig)
        hit = self.cache.load_frame(key)
        if hit is not None:
            return hit
        idx = AlignmentIndex(pair)
        frame = idx.frame.reset_index()
        n_eng = frame["ai"].map(lambda a: len(idx.map_eng.get(a, []))).astype(int)
        n_tur = frame["ai"].map(lambda a: len(idx.map_tur.get(a, []))).astype(int)
        eng_txt = frame["eng"].fillna("").astype(str)
        tur_txt = frame["tur"].fillna("").astype(str)
        out = pd.DataFrame({
            "ai": frame["ai"].astype(int), "n_eng": n_eng, "n_tur": n_tur,
            "type": [alignment_type(a, b) for a, b in zip(n_eng, n_tur)],
            "eng_words": eng_txt.str.split().str.len().astype(int),
            "tur_words": tur_txt.str.split().str.len().astype(int),
            "eng_chars": eng_txt.str.len().astype(int),
            "tur_chars": tur_txt.str.len().astype(int),
        })
        self.cache.save_frame(key, out)
        return out

    def summary(self, pairs: list[PairSpec]) -> pd.DataFrame:
        """Per-pair counts, percentages and ratios (``R_sent``, word- and char-ratio)."""
        rows = []
        for p in pairs:
            t = self.cardinality_table(p)
            counts = t["type"].value_counts()
            n = len(t)
            row: dict[str, Any] = {
                "pair": f"{p.eng.title} → {p.tur.title}",
                "translator": p.tur.focal_name, "alignments": n,
                "eng_sentences": int(t["n_eng"].sum()), "tur_sentences": int(t["n_tur"].sum()),
            }
            for ty in ALIGN_TYPES:
                row[f"{ty}_n"] = int(counts.get(ty, 0))
                row[f"{ty}_pct"] = 100 * counts.get(ty, 0) / n if n else np.nan
            row["R_sent"] = row["tur_sentences"] / row["eng_sentences"]
            row["word_ratio"] = t["tur_words"].sum() / t["eng_words"].sum()
            row["char_ratio"] = t["tur_chars"].sum() / t["eng_chars"].sum()
            rows.append(row)
        return pd.DataFrame(rows)
