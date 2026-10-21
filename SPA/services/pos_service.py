"""Service for part-of-speech distributions and comparative morphosyntax."""

from __future__ import annotations

from typing import Any

import numpy as np

from corpus_toolkit.pos import PosComparativeAnalyzer
from SPA.models.view_params_dto import CorpusScopeDTO
from SPA.repositories.corpus_repository import CorpusRepository


class PosService:
    """Manages Tab 4 UPOS distributions, delta-pp profiles, and bootstrap CIs."""

    def __init__(self, corpus_repo: CorpusRepository) -> None:
        self._repo = corpus_repo
        self._analyzer = PosComparativeAnalyzer()

    def get_pos_profile_table(
        self, scope_dto: CorpusScopeDTO, content_only: bool = False
    ) -> list[dict[str, Any]]:
        """Compute full UPOS percentage table + scalar descriptors for texts in scope."""
        texts = self._repo.get_texts_by_scope(scope_dto)
        df = self._analyzer.profile_table(texts, content_only=content_only)
        # Convert NaNs to None for clean JSON serialization
        df = df.replace({np.nan: None})
        return df.to_dict(orient="records")

    def get_pair_delta_pp(
        self, pair_code: str, content_only: bool = False
    ) -> dict[str, Any]:
        """Compute Figure 2B translation-pair divergence (Turkish - English in pp)."""
        pairs = self._repo.loader.load_translation_pairs().items
        pair = None
        for spec, eng, tur in pairs:
            if pair_code in (
                spec.pair_id,
                f"{spec.eng.code}_{spec.tur.code}",
                spec.tur.code,
                spec.eng.code,
            ):
                pair = (spec, eng, tur)
                break
        if not pair:
            return {"error": f"Pair not found: {pair_code}"}

        df = self._analyzer.pair_comparison(pair[1], pair[2], content_only=content_only)
        records = []
        for tag, row in df.iterrows():
            records.append({
                "upos": str(tag),
                "eng_pct": round(float(row["English %"]), 2),
                "tur_pct": round(float(row["Turkish %"]), 2),
                "delta_pp": round(float(row["Δ (TR−EN) pp"]), 2),
            })
        return {"pair_code": pair_code, "items": records}

    def get_group_comparison_figure2c(
        self,
        group_a_scope: str = "trans_tr",
        group_b_scope: str = "indig_tr",
        n_bootstrap: int = 1500,
    ) -> dict[str, Any]:
        """Compute Figure 2C Translated TR vs. Indigenous TR comparison with bootstrap 95% CIs."""
        texts_a = self._repo.get_texts_by_scope(CorpusScopeDTO(scope=group_a_scope))
        texts_b = self._repo.get_texts_by_scope(CorpusScopeDTO(scope=group_b_scope))

        if not texts_a or not texts_b:
            return {"error": "Insufficient texts for group comparison"}

        df = self._analyzer.group_comparison(
            texts_a,
            texts_b,
            labels=("Translated_TR", "Indigenous_TR"),
            n_bootstrap=n_bootstrap,
        )

        items = []
        for _, r in df.iterrows():
            items.append({
                "upos": str(r["UPOS"]),
                "group_a_mean": round(float(r["Translated_TR mean %"]), 2),
                "group_b_mean": round(float(r["Indigenous_TR mean %"]), 2),
                "mean_diff_pp": round(float(r["mean diff pp"]), 2),
                "ci_low": round(float(r["CI95 low"]), 2),
                "ci_high": round(float(r["CI95 high"]), 2),
            })

        attrs = df.attrs
        return {
            "group_a": group_a_scope,
            "group_b": group_b_scope,
            "chi2": round(float(attrs.get("chi2", 0.0)), 2),
            "p_value": float(attrs.get("p", 1.0)),
            "cramers_v": round(float(attrs.get("cramers_v", 0.0)), 3),
            "items": items,
        }
