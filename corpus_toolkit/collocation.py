"""Collocation statistics (GraphColl / LancsBox style) — implemented from scratch.

Setting.  Pick a **node** word and a window of ``left`` positions before and ``right`` after each
occurrence.  Let

* ``N``   – number of eligible running words in the text,
* ``R1``  – number of eligible positions covered by any node window (the node's own position
  excluded), i.e. the number of "slots" in which a collocate can appear,
* ``C1``  – corpus frequency of the candidate collocate,
* ``O11`` – occurrences of the collocate inside the windows,
* ``E11 = R1·C1/N`` – the count expected if words were scattered at random.

The contingency table is ``[[O11, R1-O11], [C1-O11, N-R1-C1+O11]]``.  Counting *union* slots
(each text position once, even if two node windows overlap) guarantees ``O11 ≤ C1`` and
``R1 ≤ N`` so no cell is negative.  Measures: MI, MI², MI³ (Church & Hanks 1990; Daille 1994),
T-score (Church et al. 1991), Dunning's log-likelihood G² (Dunning 1993; signed, χ²₁ p-value) and
Log-Dice (Rychlý 2008).
"""

import numpy as np
import pandas as pd

from .stats import chi2_sf1, xlogx_ratio
from .tokenview import TokenView

MEASURES = ("MI", "MI2", "MI3", "T", "G2", "LogDice")


def window_slots(n: int, node_pos: np.ndarray, left: int, right: int,
                 lo_bound: np.ndarray | None = None, hi_bound: np.ndarray | None = None
                 ) -> np.ndarray:
    """Boolean array: is position ``j`` inside the window of some *other-or-same* node?

    The node's own position is excluded from its *own* window, but a node that falls inside a
    neighbouring node's window counts as a slot (so ``very very`` collocates with itself).
    ``lo_bound``/``hi_bound`` (per-position sentence limits) implement sentence clamping.
    """
    diff = np.zeros(n + 1, dtype=np.int64)
    own = np.zeros(n, dtype=np.int64)
    for i in node_pos.tolist():
        lo = max(i - left, int(lo_bound[i]) if lo_bound is not None else 0)
        hi = min(i + right, int(hi_bound[i]) if hi_bound is not None else n - 1)
        diff[lo] += 1
        diff[hi + 1] -= 1
        own[i] += 1  # a node sits inside its own window; remove that self-membership
    cover = np.cumsum(diff[:n]) - own
    return cover > 0


def association_table(o11: np.ndarray, c1: np.ndarray, r1: int, n: int, f_node: int
                      ) -> pd.DataFrame:
    """Compute all association measures for vectors of ``O11`` / ``C1``."""
    o11 = np.asarray(o11, dtype=float)
    c1 = np.asarray(c1, dtype=float)
    e11 = r1 * c1 / n
    o12, o21 = r1 - o11, c1 - o11
    o22 = n - r1 - c1 + o11
    e12, e21, e22 = r1 * (n - c1) / n, (n - r1) * c1 / n, (n - r1) * (n - c1) / n
    with np.errstate(divide="ignore", invalid="ignore"):
        mi = np.where(o11 > 0, np.log2(o11 / e11), np.nan)
        mi2 = np.where(o11 > 0, np.log2(o11 ** 2 / e11), np.nan)
        mi3 = np.where(o11 > 0, np.log2(o11 ** 3 / e11), np.nan)
        t = np.where(o11 > 0, (o11 - e11) / np.sqrt(o11), np.nan)
        g2 = 2 * (xlogx_ratio(o11, e11) + xlogx_ratio(o12, e12)
                  + xlogx_ratio(o21, e21) + xlogx_ratio(o22, e22))
        log_dice = np.where(o11 > 0, 14 + np.log2(2 * o11 / (f_node + c1)), np.nan)
    signed_g2 = np.where(o11 >= e11, g2, -g2)
    return pd.DataFrame({
        "O11": o11.astype(int), "C1": c1.astype(int), "E11": e11, "MI": mi, "MI2": mi2,
        "MI3": mi3, "T": t, "G2": signed_g2, "p_G2": chi2_sf1(g2), "LogDice": log_dice,
    })



def collocates(view: TokenView, nodes: str | list[str], left: int = 5, right: int = 5,
               sentence_clamped: bool = True, min_freq: int = 3,
               sort_by: str = "G2") -> pd.DataFrame:
    """Collocates of ``nodes`` in ``view`` with all association measures.

    Returns an empty frame (and attribute ``attrs['f_node']==0``) when the node is absent.
    ``attrs`` also carries ``N``, ``R1``, ``f_node`` for the report.
    """
    node_list = [nodes] if isinstance(nodes, str) else list(nodes)
    node_pos = view.occurrences(node_list)
    n = len(view)
    forms = view.forms
    if len(node_pos) == 0 or n == 0:
        out = pd.DataFrame(columns=["collocate", "O11", "C1", "E11", *MEASURES, "p_G2"])
        out.attrs.update({"f_node": 0, "N": n, "R1": 0, "view": view.label})
        return out
    lo, hi = view.sentence_bounds() if sentence_clamped else (None, None)
    slots = window_slots(len(forms), node_pos, left, right, lo, hi) & view.eligible
    r1 = int(slots.sum())
    f_node = int(len(node_pos))
    vals, o11 = np.unique(forms[slots].astype(str), return_counts=True)
    keep = o11 >= min_freq
    vals, o11 = vals[keep], o11[keep]
    glob_vals, glob_counts = np.unique(view.analysed().astype(str), return_counts=True)
    c1 = glob_counts[np.searchsorted(glob_vals, vals)]
    table = association_table(o11, c1, r1, n, f_node)
    table.insert(0, "collocate", vals)
    table = table.sort_values(sort_by, ascending=False, kind="mergesort").reset_index(drop=True)
    table.attrs.update({"f_node": f_node, "N": n, "R1": r1, "view": view.label,
                        "left": left, "right": right, "sentence_clamped": sentence_clamped})
    return table
