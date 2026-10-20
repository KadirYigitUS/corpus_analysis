"""Lexical richness and diversity (the LancsBox-X metric family) — implemented from scratch.

All functions take ``forms``: a 1-D sequence of *already filtered and case-folded* strings
(see :class:`corpus_toolkit.tokenview.TokenView`).  Notation: ``N`` tokens, ``V`` types,
``V_m`` number of types occurring exactly ``m`` times (the *frequency spectrum*), ``V1`` hapax
legomena.  Formulas and citations are listed in :data:`METRIC_INFO` and ``docs/METRICS.md``.

.. warning:: Raw TTR falls as texts grow (Heaps' law).  Compare texts of different length only
   with length-robust measures (STTR, MATTR, MTLD) — exactly the lesson of Chapter 9.
"""

import math
import warnings
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats as sps

StrSeq = Sequence[str] | np.ndarray

NAN = float("nan")



@dataclass(frozen=True)
class MetricInfo:
    label: str
    formula: str
    higher_means: str
    length_robust: bool
    citation: str


METRIC_INFO: dict[str, MetricInfo] = {
    "N": MetricInfo("Tokens", "N", "longer text", False, "—"),
    "V": MetricInfo("Types", "V", "more distinct word forms", False, "—"),
    "TTR": MetricInfo("Type-Token Ratio", "V / N", "more diverse (but falls with N)", False,
                      "Johnson 1944; Templin 1957"),
    "Guiraud_R": MetricInfo("Guiraud's R (root TTR)", "V / √N", "more diverse", False,
                            "Guiraud 1954"),
    "CTTR": MetricInfo("Corrected TTR (Carroll)", "V / √(2N)", "more diverse", False,
                       "Carroll 1964"),
    "Herdan_C": MetricInfo("Herdan's C", "ln V / ln N", "more diverse", False, "Herdan 1960"),
    "Dugast_U": MetricInfo("Dugast's Uber index", "ln²N / (ln N − ln V)", "more diverse", False,
                           "Dugast 1979"),
    "Maas_a2": MetricInfo("Maas a²", "(ln N − ln V) / ln²N", "LESS diverse", False,
                          "Maas 1972"),
    "Yule_K": MetricInfo("Yule's K", "10⁴ · (Σ m²·V_m − N) / N²", "LESS diverse (repetitive)",
                         True, "Yule 1944"),
    "Simpson_D": MetricInfo("Simpson's D", "Σ n(n−1) / (N(N−1))", "LESS diverse", True,
                            "Simpson 1949"),
    "Honore_R": MetricInfo("Honoré's R", "100 · ln N / (1 − V1/V)", "richer vocabulary", False,
                           "Honoré 1979"),
    "Hapax_types_pct": MetricInfo("Hapax % of types", "100 · V1 / V", "many one-off words", False,
                                  "Tweedie & Baayen 1998"),
    "Hapax_tokens_pct": MetricInfo("Hapax % of tokens", "100 · V1 / N", "many one-off words",
                                   False, "Tweedie & Baayen 1998"),
    "STTR": MetricInfo("Standardised TTR (L=1000)", "mean TTR of consecutive 1000-token blocks",
                       "more diverse", True, "Scott 2004 (WordSmith)"),
    "MATTR_50": MetricInfo("Moving-Average TTR (w=50)", "mean TTR over all 50-token windows",
                           "more diverse", True, "Covington & McFall 2010"),
    "MATTR_100": MetricInfo("Moving-Average TTR (w=100)", "mean TTR over all 100-token windows",
                            "more diverse", True, "Covington & McFall 2010"),
    "MATTR_500": MetricInfo("Moving-Average TTR (w=500)", "mean TTR over all 500-token windows",
                            "more diverse", True, "Covington & McFall 2010"),
    "MTLD": MetricInfo("Measure of Textual Lexical Diversity", "N / #factors (TTR≤0.72), "
                       "mean of forward & backward", "more diverse", True,
                       "McCarthy & Jarvis 2010"),
    "HD_D": MetricInfo("HD-D (vocd-D replacement)", "Σ (1 − C(N−f, 42)/C(N, 42)) / 42",
                       "more diverse", True, "McCarthy & Jarvis 2007, 2010"),
}


#: Metrics shown on the radar chart (z-scored across texts) — all length-robust or ratio-free.
RADAR_METRICS = ("MATTR_100", "MTLD", "STTR", "Herdan_C", "Maas_a2", "Hapax_types_pct")


def _ids(forms: StrSeq) -> np.ndarray:
    """Map strings to dense integer ids (fast counting)."""
    _, inv = np.unique(np.asarray(forms, dtype=object).astype(str), return_inverse=True)
    return inv.astype(np.int64)


def _spectrum(counts: np.ndarray) -> Counter:
    """Frequency spectrum: {m: V_m}."""
    return Counter(counts.tolist())


def ttr(forms: StrSeq) -> float:
    n = len(forms)
    return len(set(forms)) / n if n else NAN


def sttr(forms: StrSeq, block: int = 1000) -> float:
    """Mean TTR over consecutive blocks of ``block`` tokens (trailing partial block dropped).

    Falls back to plain TTR (with a warning) when the text is shorter than one block.
    """
    n = len(forms)
    if n < block:
        warnings.warn(f"STTR: N={n} < block={block}; falling back to TTR.", stacklevel=2)
        return ttr(forms)
    ids = _ids(forms)
    vals = [len(np.unique(ids[i:i + block])) / block for i in range(0, n - block + 1, block)]
    return float(np.mean(vals))


def mattr_series(forms: StrSeq, window: int) -> np.ndarray:
    """TTR of every window of ``window`` consecutive tokens (O(N) sliding update)."""
    n = len(forms)
    if n < window:
        return np.asarray([ttr(forms)]) if n else np.asarray([])
    ids = _ids(forms)
    counts: dict[int, int] = {}
    distinct = 0
    out = np.empty(n - window + 1, dtype=float)
    for i, t in enumerate(ids.tolist()):
        c = counts.get(t, 0)
        if c == 0:
            distinct += 1
        counts[t] = c + 1
        if i >= window:
            old = int(ids[i - window])
            counts[old] -= 1
            if counts[old] == 0:
                distinct -= 1
        if i >= window - 1:
            out[i - window + 1] = distinct / window
    return out


def mattr(forms: StrSeq, window: int = 100) -> float:
    """Moving-Average TTR; falls back to TTR if the text is shorter than ``window``."""
    if len(forms) < window:
        warnings.warn(f"MATTR: N={len(forms)} < window={window}; falling back to TTR.",
                      stacklevel=2)
    s = mattr_series(forms, window)
    return float(s.mean()) if len(s) else NAN


def _mtld_pass(seq: StrSeq, threshold: float) -> float:
    factors, types, n = 0.0, set(), 0
    for tok in seq:
        n += 1
        types.add(tok)
        if len(types) / n <= threshold:
            factors += 1.0
            types, n = set(), 0
    if n > 0:  # partial factor for the unfinished tail
        factors += (1.0 - len(types) / n) / (1.0 - threshold)
    return len(seq) / factors if factors > 0 else NAN


def mtld(forms: StrSeq, threshold: float = 0.72) -> float:
    """MTLD (McCarthy & Jarvis 2010): mean of forward and backward passes."""
    seq = list(forms)
    if len(seq) < 2:
        return NAN
    f, b = _mtld_pass(seq, threshold), _mtld_pass(seq[::-1], threshold)
    vals = [v for v in (f, b) if not math.isnan(v)]
    return float(np.mean(vals)) if vals else NAN


def hdd(forms: StrSeq, sample_size: int = 42) -> float:
    """HD-D (McCarthy & Jarvis 2007, 2010): expected sample TTR via hypergeometric distribution."""
    seq = list(forms)
    n = len(seq)
    if n < sample_size:
        return NAN
    counts = np.unique(np.asarray(seq, dtype=object).astype(str), return_counts=True)[1]
    p_present = 1.0 - sps.hypergeom.pmf(0, n, counts, sample_size)
    return float(np.sum(p_present) / sample_size)


def diversity_metrics(forms: StrSeq) -> dict[str, float]:
    """Compute the full LancsBox-X-style metric set for one token sequence."""
    forms = list(forms)
    n = len(forms)
    if n == 0:
        return {k: NAN for k in METRIC_INFO}
    counts = np.unique(np.asarray(forms, dtype=object).astype(str), return_counts=True)[1]
    v = int(len(counts))
    spec = _spectrum(counts)
    v1 = spec.get(1, 0)
    ln_n, ln_v = math.log(n), math.log(v)
    denom_u = ln_n - ln_v
    m = {
        "N": float(n), "V": float(v), "TTR": v / n, "Guiraud_R": v / math.sqrt(n),
        "CTTR": v / math.sqrt(2 * n),
        "Herdan_C": ln_v / ln_n if ln_n > 0 else NAN,
        "Dugast_U": ln_n ** 2 / denom_u if denom_u > 0 else NAN,
        "Maas_a2": denom_u / ln_n ** 2 if ln_n > 0 else NAN,
        "Yule_K": 1e4 * (sum(k * k * c for k, c in spec.items()) - n) / n ** 2,
        "Simpson_D": float((counts * (counts - 1)).sum()) / (n * (n - 1)) if n > 1 else NAN,
        "Honore_R": 100 * ln_n / (1 - v1 / v) if v1 < v else NAN,
        "Hapax_types_pct": 100 * v1 / v, "Hapax_tokens_pct": 100 * v1 / n,
    }
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # short-text fallbacks are reported in 'notes'
        m["STTR"] = sttr(forms)
        for w in (50, 100, 500):
            m[f"MATTR_{w}"] = mattr(forms, w)
        m["MTLD"] = mtld(forms)
        m["HD_D"] = hdd(forms)
    return m



def diversity_table(rows: dict[str, StrSeq]) -> pd.DataFrame:
    """``{label: forms}`` -> DataFrame (one row per label, one column per metric)."""
    return pd.DataFrame({k: diversity_metrics(v) for k, v in rows.items()}).T


def rank_frequency(forms: StrSeq) -> pd.DataFrame:
    """Zipf data: rank, frequency (for log-log plots)."""
    counts = np.sort(np.unique(np.asarray(forms, dtype=object).astype(str),
                               return_counts=True)[1])[::-1]
    return pd.DataFrame({"rank": np.arange(1, len(counts) + 1), "freq": counts})
