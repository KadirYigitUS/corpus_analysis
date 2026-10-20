"""Part-of-speech comparative statistics for single texts, parallel pairs and text groups.

Why POS?  Grammatical profiles are a *norm-sensitive* window on translation: translated Turkish
may pattern differently from the same translator's own indigenous prose (Toury 2012's
*interference* / *standardisation* hypotheses; Baker 1993's translation universals) and English
and Turkish differ typologically (analytic vs. agglutinative), so cross-language comparisons are
read as *profiles*, never as 'better/worse'.  All shares use **non-punctuation tokens**.
"""

from collections.abc import Iterable, Sequence
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats as sps

from .filters import CONTENT, PUNCT
from .lazy import LazyCorpusText
from .stats import bootstrap_ci

UPOS_ORDER = ("NOUN", "VERB", "ADJ", "ADV", "PROPN", "NUM", "PRON", "DET", "ADP", "AUX",
              "CCONJ", "SCONJ", "PART", "INTJ", "SYM", "X")
OPEN_CLASS = ("NOUN", "VERB", "ADJ", "ADV")
DEVERBAL_MARKERS = ("+Inf", "Part")  # Oflazer tags: Inf1/2/3, PastPart, FutPart, PresPart, ...



def pos_counts(text: LazyCorpusText, content_only: bool = False) -> pd.Series:
    """UPOS counts over non-punctuation tokens (``content_only`` drops function-class tokens)."""
    tab = text.tokens
    fcl = tab["fcl"].to_numpy()
    keep = (fcl == CONTENT) if content_only else (fcl != PUNCT)
    counts = tab["pos"][keep].astype(str).value_counts()
    return counts.reindex(list(UPOS_ORDER), fill_value=0).astype(int).rename(text.record.code)


def pos_percentages(text: LazyCorpusText, content_only: bool = False) -> pd.Series:
    c = pos_counts(text, content_only)
    return (100 * c / c.sum()).rename(text.record.code) if c.sum() else c.astype(float)


def text_profile(text: LazyCorpusText) -> dict[str, float]:
    """Scalar grammatical descriptors of one text."""
    tab = text.tokens
    fcl = tab["fcl"].to_numpy()
    nonp = fcl != PUNCT
    n = int(nonp.sum())
    counts = pos_counts(text)
    open_n = int(counts[list(OPEN_CLASS)].sum())
    prof = {
        "tokens_nonpunct": float(n),
        "lexical_density": 100 * open_n / n if n else np.nan,
        "lexical_density_propn": 100 * (open_n + counts["PROPN"]) / n if n else np.nan,
        "function_share": 100 * int((fcl == 1).sum()) / n if n else np.nan,
        "noun_verb_ratio": counts["NOUN"] / counts["VERB"] if counts["VERB"] else np.nan,
    }
    if text.record.language == "tr":
        morph = tab["morph"][nonp].astype(str)
        mask = np.zeros(len(morph), dtype=bool)
        for m in DEVERBAL_MARKERS:
            mask |= morph.str.contains(m, regex=False).to_numpy()
        prof["deverbal_share"] = 100 * mask.sum() / n if n else np.nan
    return prof


class PosComparativeAnalyzer:
    """Build comparison tables; figures live in :mod:`corpus_toolkit.viz`."""

    def profile_table(self, texts: Iterable[LazyCorpusText], content_only: bool = False
                      ) -> pd.DataFrame:
        """One row per text: UPOS % columns + scalar descriptors (+ metadata columns)."""
        rows = []
        for t in texts:
            row: dict[str, Any] = {"code": t.record.code, "title": t.record.title,
                   "language": t.record.language, "type": t.record.corpus_type,
                   "focal": t.record.focal_name}
            row.update(pos_percentages(t, content_only).to_dict())
            row.update(text_profile(t))
            rows.append(row)
            t.evict()
        return pd.DataFrame(rows)

    def pair_comparison(self, eng: LazyCorpusText, tur: LazyCorpusText,
                        content_only: bool = False) -> pd.DataFrame:
        """UPOS % English vs Turkish with the difference (Turkish − English, in pp)."""
        e, t = pos_percentages(eng, content_only), pos_percentages(tur, content_only)
        return pd.DataFrame({"English %": e, "Turkish %": t, "Δ (TR−EN) pp": t - e})

    def lexical_density(self, text: LazyCorpusText) -> float:
        """Lexical density percentage of content words excluding punctuation."""
        return float(text_profile(text)["lexical_density"])

    def noun_verb_ratio(self, text: LazyCorpusText) -> float:
        """Noun-to-verb ratio of the text."""
        return float(text_profile(text)["noun_verb_ratio"])

    def group_comparison(self, group_a: Sequence[LazyCorpusText],
                         group_b: Sequence[LazyCorpusText], labels: tuple[str, str],
                         content_only: bool = False,
                         n_bootstrap: int = 2000) -> pd.DataFrame:
        """Translation-vs-indigenous style comparison with uncertainty.

        For every UPOS: mean of per-text percentages per group, percentile bootstrap CI of the
        mean difference, and (pooled counts) χ² contribution.  With only 3–5 texts per group the
        result is **descriptive**; the notebook says so explicitly.
        """
        pa = np.array([pos_percentages(t, content_only).to_numpy() for t in group_a])
        pb = np.array([pos_percentages(t, content_only).to_numpy() for t in group_b])
        rng = np.random.default_rng(13)
        rows = []
        for j, tag in enumerate(UPOS_ORDER):
            diffs = [rng.choice(pa[:, j], len(pa)).mean() - rng.choice(pb[:, j], len(pb)).mean()
                     for _ in range(n_bootstrap)]
            lo, hi = np.percentile(diffs, [2.5, 97.5])
            rows.append({"UPOS": tag, f"{labels[0]} mean %": pa[:, j].mean(),
                         f"{labels[1]} mean %": pb[:, j].mean(),
                         "mean diff pp": pa[:, j].mean() - pb[:, j].mean(),
                         "CI95 low": lo, "CI95 high": hi})
        out = pd.DataFrame(rows)
        ca = np.sum([pos_counts(t, content_only).to_numpy() for t in group_a], axis=0)
        cb = np.sum([pos_counts(t, content_only).to_numpy() for t in group_b], axis=0)
        table = np.vstack([ca, cb])
        table = table[:, table.sum(axis=0) > 0]
        chi2, p, _, _ = sps.chi2_contingency(table)
        cramer = float(np.sqrt(chi2 / (table.sum() * (min(table.shape) - 1))))
        out.attrs.update({"chi2": float(chi2), "p": float(p), "cramers_v": cramer,
                          "n_a": len(group_a), "n_b": len(group_b)})
        return out

    @staticmethod
    def bootstrap_density(values: Sequence[float]) -> tuple[float, float, float]:
        return bootstrap_ci(values)
