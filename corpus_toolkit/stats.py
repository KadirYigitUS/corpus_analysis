"""Elementary statistics used across chapters (small, dependency-light, unit-tested).

Everything here is deliberately transparent: each function is a few lines that a student can
read and verify by hand against the worked examples in the notebook.
"""

import math
from collections.abc import Callable, Sequence

import numpy as np
import pandas as pd
from scipy import stats as sps

NumSeq = Sequence[float] | Sequence[int] | np.ndarray | pd.Series | pd.DataFrame

NAN = float("nan")


def per10k(count: float, total: float) -> float:
    """Normalised frequency per 10,000 running words (``per10k``)."""
    return 1e4 * count / total if total else NAN


def pearson(x: NumSeq, y: NumSeq) -> tuple[float, float]:
    """Pearson r and two-sided p; ``(nan, nan)`` when an input is constant or n<3."""
    xa, ya = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if len(xa) < 3 or np.ptp(xa) == 0 or np.ptp(ya) == 0:
        return NAN, NAN
    r, p = sps.pearsonr(xa, ya)
    return float(r), float(p)


def spearman(x: NumSeq, y: NumSeq) -> tuple[float, float]:
    """Spearman ρ (average ranks for ties) and two-sided p."""
    xa, ya = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if len(xa) < 3 or np.ptp(xa) == 0 or np.ptp(ya) == 0:
        return NAN, NAN
    rho, p = sps.spearmanr(xa, ya)
    return float(rho), float(p)


def cosine(x: NumSeq, y: NumSeq) -> float:
    """Cosine similarity of two non-negative vectors (0 when either is all zero)."""
    xa, ya = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    d = np.linalg.norm(xa) * np.linalg.norm(ya)
    return float(xa @ ya / d) if d else 0.0


def juilland_d(parts: NumSeq) -> float:
    """Juilland's D dispersion: ``1 − V/√(n−1)``, ``V = σ/μ`` (population σ).

    1 = perfectly even across the ``n`` corpus parts, 0 = concentrated in a single part.
    """
    a = np.asarray(parts, dtype=float)
    n = len(a)
    if n < 2 or a.sum() == 0:
        return NAN
    v = a.std() / a.mean()
    return float(1.0 - v / math.sqrt(n - 1))


def chunk_counts(positions: NumSeq, n_items: int, n_parts: int = 10) -> np.ndarray:
    """Count ``positions`` (0-based) falling in each of ``n_parts`` equal-width chunks."""
    if n_items <= 0:
        return np.zeros(n_parts)
    idx = np.minimum((np.asarray(positions, dtype=np.int64) * n_parts) // n_items, n_parts - 1)
    return np.bincount(idx, minlength=n_parts).astype(float)


def benjamini_hochberg(pvalues: NumSeq) -> np.ndarray:
    """BH false-discovery-rate adjusted q-values (NaNs are passed through)."""
    p = np.asarray(pvalues, dtype=float)
    q = np.full(p.shape, np.nan)
    ok = ~np.isnan(p)
    pv = p[ok]
    m = len(pv)
    if m == 0:
        return q
    order = np.argsort(pv)
    ranked = pv[order] * m / np.arange(1, m + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(m)
    out[order] = np.minimum(ranked, 1.0)
    q[ok] = out
    return q


def bootstrap_ci(values: Sequence[float], stat: Callable[[np.ndarray], float] = np.mean,
                 n_boot: int = 1000, alpha: float = 0.05, seed: int = 13
                 ) -> tuple[float, float, float]:
    """Percentile bootstrap: ``(estimate, lower, upper)``; deterministic via ``seed``."""
    a = np.asarray(values, dtype=float)
    a = a[~np.isnan(a)]
    if len(a) == 0:
        return NAN, NAN, NAN
    rng = np.random.default_rng(seed)
    boots = np.array([stat(rng.choice(a, size=len(a), replace=True)) for _ in range(n_boot)])
    lo, hi = np.percentile(boots, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return float(stat(a)), float(lo), float(hi)


def chi2_sf1(g: np.ndarray) -> np.ndarray:
    """Upper-tail p of a χ² (df=1) statistic, vectorised."""
    return sps.chi2.sf(np.maximum(g, 0.0), df=1)


def xlogx_ratio(o: np.ndarray, e: np.ndarray) -> np.ndarray:
    """``o·ln(o/e)`` with the convention ``0·ln 0 = 0``."""
    o = np.asarray(o, dtype=float)
    e = np.asarray(e, dtype=float)
    out = np.zeros_like(o)
    mask = (o > 0) & (e > 0)
    out[mask] = o[mask] * np.log(o[mask] / e[mask])
    return out
