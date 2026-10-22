"""Service for batch KWIC, narrative dispersion, and correlation matrices."""

from __future__ import annotations

from typing import Any

import numpy as np

from corpus_toolkit.batch_kwic import BatchKwicAnalyzer
from SPA.models.view_params_dto import CorpusScopeDTO, TokenViewParamsDTO
from SPA.repositories.corpus_repository import CorpusRepository


class BatchDispersionService:
    """Manages Tab 7 multi-term dispersion profiles, Juilland's D, and BH-FDR correlations."""

    def __init__(self, corpus_repo: CorpusRepository) -> None:
        self._repo = corpus_repo
        self._analyzer = BatchKwicAnalyzer()

    def analyze_batch(
        self,
        terms: list[str],
        view_params: TokenViewParamsDTO,
        scope_dto: CorpusScopeDTO,
        n_chunks: int = 10,
    ) -> dict[str, Any]:
        """Perform batch analysis across texts in scope and return summary, heatmap, and correlations."""
        clean_terms: list[str] = []
        for item in terms:
            for chunk in str(item).split("|"):
                part = chunk.split(":", 1)[1] if ":" in chunk else chunk
                for w in part.split(","):
                    wt = w.strip()
                    if wt and wt not in clean_terms:
                        clean_terms.append(wt)
        if not clean_terms:
            return {"error": "No valid terms provided"}

        texts = self._repo.get_texts_by_scope(scope_dto)
        if not texts:
            return {"error": "No texts found for given scope"}

        result = self._analyzer.analyze(
            terms=clean_terms,
            texts=texts,
            field=view_params.field,  # type: ignore[arg-type]
            match="exact",
            filter_function_words=view_params.filter_function_words,
            mode=view_params.mode,  # type: ignore[arg-type]
            punct=view_params.punct,  # type: ignore[arg-type]
            n_chunks=n_chunks,
        )

        # 1. Summary table (Juilland's D across and within texts)
        summary_df = result.summary().replace({np.nan: None})
        summary_records = summary_df.to_dict(orient="records")

        # 2. Text x Term heatmap rates (per 10k)
        rates_df = result.rates.replace({np.nan: None})
        rates_matrix: dict[str, dict[str, float | None]] = {}
        for lab in result.labels:
            rates_matrix[lab] = {
                code: (round(float(val), 2) if val is not None else None)
                for code, val in rates_df.loc[lab].items()
            }

        # 3. Pairwise correlations + BH-FDR
        pairwise_records: list[dict[str, Any]] = []
        if len(clean_terms) >= 2:
            pw_df = result.pairwise().replace({np.nan: None})
            for _, r in pw_df.iterrows():
                pairwise_records.append(
                    {
                        "term_a": str(r["a"]),
                        "term_b": str(r["b"]),
                        "pearson_r": (
                            round(float(r["pearson_r"]), 3)
                            if r["pearson_r"] is not None
                            else None
                        ),
                        "q_pearson": (
                            round(float(r["q_pearson(BH)"]), 4)
                            if r.get("q_pearson(BH)") is not None
                            else None
                        ),
                        "spearman_rho": (
                            round(float(r["spearman_rho"]), 3)
                            if r["spearman_rho"] is not None
                            else None
                        ),
                        "q_spearman": (
                            round(float(r["q_spearman(BH)"]), 4)
                            if r.get("q_spearman(BH)") is not None
                            else None
                        ),
                        "cosine": (
                            round(float(r["cosine"]), 3)
                            if r["cosine"] is not None
                            else None
                        ),
                    }
                )

        return {
            "labels": result.labels,
            "codes": result.codes,
            "summary": summary_records,
            "rates_matrix": rates_matrix,
            "pairwise": pairwise_records,
        }
