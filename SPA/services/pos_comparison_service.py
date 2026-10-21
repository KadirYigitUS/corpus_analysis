"""Service for per-author-translator and per-pair UPOS chunk comparison (Tab 4)."""

from __future__ import annotations

from typing import Any

import numpy as np
from scipy import stats as sps

from corpus_toolkit.filters import CONTENT, PUNCT
from corpus_toolkit.lazy import LazyCorpusText
from corpus_toolkit.pos import UPOS_ORDER, pos_counts, text_profile
from SPA.repositories.corpus_repository import CorpusRepository

AUTHOR_COMPARISON_SPECS: dict[str, dict[str, Any]] = {
    "ALL": {
        "label": "All Pioneer Authors Pooled (5 Trans TR vs 3 Indig TR)",
        "author": "ALL", "trans_codes": ["BR-SM", "A-ZB", "YG-ZB", "KS-ZB", "KT-OK"],
        "indig_codes": ["O-SM", "SU-ZB", "SCS-OK"],
    },
    "SM": {
        "label": "Selma MİNE [SM]: BR-SM (Ben, Robot) vs O-SM (OnaBirİsimVer)",
        "author": "SM", "trans_codes": ["BR-SM"], "indig_codes": ["O-SM"],
    },
    "ZB": {
        "label": "Zühtü BAYAR [ZB] Pooled: A-ZB + YG-ZB + KS-ZB vs SU-ZB (Sahte Uygarlık)",
        "author": "ZB", "trans_codes": ["A-ZB", "YG-ZB", "KS-ZB"], "indig_codes": ["SU-ZB"],
    },
    "ZB_A": {
        "label": "Zühtü BAYAR [ZB_A]: A-ZB (Aydınlık) vs SU-ZB (Sahte Uygarlık)",
        "author": "ZB", "trans_codes": ["A-ZB"], "indig_codes": ["SU-ZB"],
    },
    "ZB_YG": {
        "label": "Zühtü BAYAR [ZB_YG]: YG-ZB (Yalnız Gezegen) vs SU-ZB (Sahte Uygarlık)",
        "author": "ZB", "trans_codes": ["YG-ZB"], "indig_codes": ["SU-ZB"],
    },
    "ZB_KS": {
        "label": "Zühtü BAYAR [ZB_KS]: KS-ZB (Kızıl Veba) vs SU-ZB (Sahte Uygarlık)",
        "author": "ZB", "trans_codes": ["KS-ZB"], "indig_codes": ["SU-ZB"],
    },
    "OK": {
        "label": "Özlem KURDOĞLU [OK]: KT-OK (Karanlığı Taramak) vs SCS-OK (Son Çıkan Işığı Söndürsün)",
        "author": "OK", "trans_codes": ["KT-OK"], "indig_codes": ["SCS-OK"],
    },
}


class PosComparisonService:
    """Computes chunk-level UPOS statistical comparisons per author-translator & pair."""

    def __init__(self, corpus_repo: CorpusRepository) -> None:
        self._repo = corpus_repo
        self._chunk_cache: dict[tuple[str, bool], np.ndarray] = {}
        self._comp_cache: dict[tuple[str, bool, int], dict[str, Any]] = {}
        self._summary_cache: dict[bool, list[dict[str, Any]]] = {}

    def get_author_summary_table(self, content_only: bool = False) -> list[dict[str, Any]]:
        """Return the 7-row summary matrix across ALL, SM, ZB, ZB_A, ZB_YG, ZB_KS, and OK."""
        if content_only in self._summary_cache:
            return self._summary_cache[content_only]
        rows: list[dict[str, Any]] = []
        for key in ("ALL", "SM", "ZB", "ZB_A", "ZB_YG", "ZB_KS", "OK"):
            c = self.get_comparison(key, content_only=content_only, n_bootstrap=600)
            if "error" not in c:
                rows.append({
                    "key": key, "author": c["author"], "label": c["label"],
                    "trans_codes": ", ".join(c["trans_codes"]),
                    "indig_codes": ", ".join(c["indig_codes"]),
                    "n_chunks_a": c["n_chunks_a"], "n_chunks_b": c["n_chunks_b"],
                    "chi2": c["chi2"], "cramers_v": c["cramers_v"],
                    "p_value": c["p_value"], "perm_p_value": c["perm_p_value"],
                    "delta_lex_density": c["delta_lex_density"],
                    "delta_nv_ratio": c["delta_nv_ratio"],
                    "top_divergent_upos": c["top_divergent_upos"],
                })
        self._summary_cache[content_only] = rows
        return rows

    def get_comparison(
        self, comparison_key: str = "ALL", content_only: bool = False, n_bootstrap: int = 800
    ) -> dict[str, Any]:
        """Compute Figure 2C comparison for a specific author-translator or pair."""
        key = comparison_key if comparison_key in AUTHOR_COMPARISON_SPECS else "ALL"
        cache_k = (key, content_only, int(n_bootstrap))
        if cache_k in self._comp_cache:
            return self._comp_cache[cache_k]

        spec = AUTHOR_COMPARISON_SPECS[key]
        texts_a = [t for c in spec["trans_codes"] if (t := self._repo.get_text_by_code(c)) is not None]
        texts_b = [t for c in spec["indig_codes"] if (t := self._repo.get_text_by_code(c)) is not None]
        if not texts_a or not texts_b:
            return {"error": f"Insufficient texts for comparison key: {key}"}

        chunks_a = np.vstack([self._text_chunks(t, content_only) for t in texts_a])
        chunks_b = np.vstack([self._text_chunks(t, content_only) for t in texts_b])
        ca = np.sum([pos_counts(t, content_only).to_numpy() for t in texts_a], axis=0)
        cb = np.sum([pos_counts(t, content_only).to_numpy() for t in texts_b], axis=0)
        table = np.vstack([ca, cb])
        valid = table.sum(axis=0) > 0
        chi2, chi2_p, _, _ = sps.chi2_contingency(table[:, valid])
        cramer = float(np.sqrt(chi2 / (table.sum() * (min(table[:, valid].shape) - 1))))

        rng = np.random.default_rng(42 + sum(ord(ch) for ch in key))
        na, nb = len(chunks_a), len(chunks_b)
        idx_a = rng.integers(0, na, size=(n_bootstrap, na))
        idx_b = rng.integers(0, nb, size=(n_bootstrap, nb))
        boot_diffs = chunks_a[idx_a].mean(axis=1) - chunks_b[idx_b].mean(axis=1)
        perm_p = self._perm_pvalue(chunks_a, chunks_b, rng)

        raw_pvals, items = [], []
        for j, tag in enumerate(UPOS_ORDER):
            va, vb = chunks_a[:, j], chunks_b[:, j]
            mean_a, mean_b = float(va.mean()), float(vb.mean())
            lo, hi = np.percentile(boot_diffs[:, j], [2.5, 97.5])
            zero_var = float(va.max() - va.min()) == 0.0 and float(vb.max() - vb.min()) == 0.0 and mean_a == mean_b
            u_stat, p_val = (0.0, 1.0) if zero_var else sps.mannwhitneyu(va, vb, alternative="two-sided")
            raw_pvals.append(float(p_val))
            items.append({
                "upos": str(tag), "group_a_mean": round(mean_a, 2), "group_b_mean": round(mean_b, 2),
                "mean_diff_pp": round(mean_a - mean_b, 2), "ci_low": round(float(lo), 2),
                "ci_high": round(float(hi), 2), "u_stat": round(float(u_stat), 1), "p_val": round(float(p_val), 4),
            })

        for it, qv in zip(items, self._bh_fdr(raw_pvals)):
            it["q_val"] = round(float(qv), 4)

        pa, pb = [text_profile(t) for t in texts_a], [text_profile(t) for t in texts_b]
        lex_diff = float(np.mean([p["lexical_density"] for p in pa]) - np.mean([p["lexical_density"] for p in pb]))
        nv_diff = float(np.mean([p["noun_verb_ratio"] for p in pa]) - np.mean([p["noun_verb_ratio"] for p in pb]))
        top_u = max(items, key=lambda x: abs(x["mean_diff_pp"]))
        open_p = round(float(np.median(raw_pvals[:4])), 4)

        res = {
            "comparison_key": key, "author": spec["author"], "label": spec["label"],
            "trans_codes": spec["trans_codes"], "indig_codes": spec["indig_codes"],
            "n_chunks_a": na, "n_chunks_b": nb, "chi2": round(float(chi2), 2),
            "chi2_p_value": float(chi2_p), "p_value": open_p, "perm_p_value": perm_p,
            "cramers_v": round(cramer, 4), "delta_lex_density": round(lex_diff, 2),
            "delta_nv_ratio": round(nv_diff, 2),
            "top_divergent_upos": f"{top_u['upos']} ({top_u['mean_diff_pp']:+.2f} pp, p={top_u['p_val']:.4f})",
            "items": items,
        }
        self._comp_cache[cache_k] = res
        return res

    @staticmethod
    def _perm_pvalue(chunks_a: np.ndarray, chunks_b: np.ndarray, rng: np.random.Generator) -> float:
        na, nb = len(chunks_a), len(chunks_b)
        pooled = np.vstack([chunks_a, chunks_b])
        obs = float(np.abs(chunks_a.mean(axis=0) - chunks_b.mean(axis=0)).sum())
        exceed = sum(
            1 for _ in range(1000)
            if float(np.abs(pooled[(p := rng.permutation(na + nb))[:na]].mean(axis=0) - pooled[p[na:]].mean(axis=0)).sum()) >= obs
        )
        return round((exceed + 1) / 1001.0, 4)

    def _text_chunks(self, text: LazyCorpusText, content_only: bool) -> np.ndarray:
        ck = (text.record.code, content_only)
        if ck in self._chunk_cache:
            return self._chunk_cache[ck]
        tab = text.tokens
        fcl = tab["fcl"].to_numpy()
        keep = (fcl == CONTENT) if content_only else (fcl != PUNCT)
        pos_arr = tab["pos"][keep].astype(str).to_numpy()
        splits = np.array_split(pos_arr, max(2, len(pos_arr) // (200 if len(pos_arr) < 4000 else 500)))
        mat = np.zeros((len(splits), len(UPOS_ORDER)), dtype=float)
        t2i = {t: i for i, t in enumerate(UPOS_ORDER)}
        for r_i, sp in enumerate(splits):
            if len(sp):
                vals, cnts = np.unique(sp, return_counts=True)
                tot = float(cnts.sum())
                for v, c in zip(vals, cnts):
                    if v in t2i:
                        mat[r_i, t2i[v]] = 100.0 * float(c) / tot
        text.evict()
        self._chunk_cache[ck] = mat
        return mat

    @staticmethod
    def _bh_fdr(pvals: list[float]) -> list[float]:
        m = len(pvals)
        order = np.argsort(pvals)
        q, prev = np.zeros(m, dtype=float), 1.0
        for rank in range(m - 1, -1, -1):
            idx = order[rank]
            prev = min(prev, pvals[idx] * m / (rank + 1))
            q[idx] = prev
        return q.tolist()
