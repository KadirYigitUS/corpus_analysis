"""Service for part-of-speech distributions and comparative morphosyntax."""

from __future__ import annotations

from typing import Any

import numpy as np

from corpus_toolkit.pos import PosComparativeAnalyzer
from SPA.models.view_params_dto import CorpusScopeDTO, TokenViewParamsDTO
from SPA.repositories.corpus_repository import CorpusRepository
from SPA.services.pos_comparison_service import PosComparisonService


class PosService:
    """Manages Tab 4 UPOS distributions, delta-pp profiles, and per-author/pair bootstrap CIs."""

    def __init__(
        self,
        corpus_repo: CorpusRepository,
        comp_service: PosComparisonService | None = None,
    ) -> None:
        self._repo = corpus_repo
        self._analyzer = PosComparativeAnalyzer()
        self._comp = comp_service or PosComparisonService(corpus_repo)

    def get_pos_profile_table(
        self,
        scope_dto: CorpusScopeDTO,
        content_only: bool = False,
        view_params: TokenViewParamsDTO | None = None,
    ) -> list[dict[str, Any]]:
        """Compute full UPOS percentage table + scalar descriptors for texts in scope."""
        eff_content = content_only or bool(view_params and view_params.filter_function_words)
        texts = self._repo.get_texts_by_scope(scope_dto)
        df = self._analyzer.profile_table(texts, content_only=eff_content)
        df = df.replace({np.nan: None})
        return df.to_dict(orient="records")

    def get_pair_delta_pp(
        self,
        pair_code: str,
        content_only: bool = False,
        view_params: TokenViewParamsDTO | None = None,
    ) -> dict[str, Any]:
        """Compute Figure 2B translation-pair divergence (Turkish - English in pp)."""
        eff_content = content_only or bool(view_params and view_params.filter_function_words)
        pairs = self._repo.loader.load_translation_pairs().items
        pair = None
        parts = {pair_code, *pair_code.split("_")}
        if "TSP-JL" in parts:
            parts.add("SP-JL")
        for spec, eng, tur in pairs:
            if parts & {
                spec.pair_id,
                f"{spec.eng.code}_{spec.tur.code}",
                spec.tur.code,
                spec.eng.code,
            }:
                pair = (spec, eng, tur)
                break
        if not pair:
            return {"error": f"Pair not found: {pair_code}"}

        df = self._analyzer.pair_comparison(pair[1], pair[2], content_only=eff_content)
        records = []
        for tag, row in df.iterrows():
            records.append({
                "upos": str(tag),
                "eng_pct": round(float(row["English %"]), 2),
                "tur_pct": round(float(row["Turkish %"]), 2),
                "delta_pp": round(float(row["Δ (TR−EN) pp"]), 2),
            })
        return {"pair_code": pair_code, "items": records}

    def get_author_summary_table(
        self,
        content_only: bool = False,
        view_params: TokenViewParamsDTO | None = None,
    ) -> list[dict[str, Any]]:
        """Return per-author-translator (SM, ZB, OK) and per-pair UPOS comparison summary."""
        eff_content = content_only or bool(view_params and view_params.filter_function_words)
        return self._comp.get_author_summary_table(content_only=eff_content)

    def get_group_comparison_figure2c(
        self,
        group_a_scope: str = "trans_tr",
        group_b_scope: str = "indig_tr",
        comparison_key: str = "ALL",
        content_only: bool = False,
        n_bootstrap: int = 800,
        view_params: TokenViewParamsDTO | None = None,
    ) -> dict[str, Any]:
        """Compute Figure 2C Translated TR vs. Indigenous TR comparison per author/pair."""
        eff_content = content_only or bool(view_params and view_params.filter_function_words)
        res = self._comp.get_comparison(
            comparison_key=comparison_key,
            content_only=eff_content,
            n_bootstrap=n_bootstrap,
        )
        if "error" in res:
            return res
        res["group_a"] = group_a_scope
        res["group_b"] = group_b_scope
        return res

