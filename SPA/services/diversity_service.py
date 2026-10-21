"""Service for lexical richness, LancsBox-X metrics, and Zipf rank-frequency analysis."""

from __future__ import annotations

from typing import Any

import numpy as np

from corpus_toolkit.diversity import (
    diversity_metrics,
    mattr_series,
    rank_frequency,
)
from SPA.models.view_params_dto import CorpusScopeDTO, TokenViewParamsDTO
from SPA.repositories.corpus_repository import CorpusRepository


class DiversityService:
    """Manages Tab 8 lexical diversity calculations, MATTR curves, and Zipf plots."""

    def __init__(self, corpus_repo: CorpusRepository) -> None:
        self._repo = corpus_repo
        self._metrics_cache: dict[tuple[Any, ...], dict[str, Any]] = {}

    def get_diversity_table(
        self,
        view_params: TokenViewParamsDTO,
        scope_dto: CorpusScopeDTO,
    ) -> list[dict[str, Any]]:
        """Calculate the full LancsBox-X diversity metrics for all texts in scope."""
        texts = self._repo.get_texts_by_scope(scope_dto)
        tokens_map = self._repo.get_text_tokens_matrix(texts, view_params)
        vp_key = (
            view_params.field,
            view_params.filter_function_words,
            view_params.mode,
            view_params.punct,
        )

        records: list[dict[str, Any]] = []
        for text_code, forms in tokens_map.items():
            cache_key = (text_code, *vp_key, len(forms))
            if cache_key not in self._metrics_cache:
                metrics = diversity_metrics(forms)
                clean_metrics: dict[str, Any] = {"text_code": text_code}
                for k, val in metrics.items():
                    if val is None or np.isnan(val):
                        clean_metrics[k] = None
                    else:
                        clean_metrics[k] = round(float(val), 4)
                self._metrics_cache[cache_key] = clean_metrics
            records.append(self._metrics_cache[cache_key])

        return records

    def get_mattr_trajectory(
        self,
        text_code: str,
        view_params: TokenViewParamsDTO,
        window: int = 500,
        subsample_step: int = 50,
    ) -> dict[str, Any]:
        """Compute sliding-window MATTR curve with step subsampling for efficient charting."""
        text = self._repo.loader.load_text(text_code)
        view = self._repo.get_token_view(text, view_params)
        forms = view.forms

        series = mattr_series(forms, window=window)
        if len(series) == 0:
            return {"text_code": text_code, "window": window, "points": []}

        # Subsample to keep JSON payload lightweight
        points = []
        for i in range(0, len(series), subsample_step):
            val = series[i]
            points.append({
                "window_idx": int(i),
                "ttr": round(float(val), 4) if val is not None and not np.isnan(val) else None,
            })

        return {
            "text_code": text_code,
            "window": window,
            "total_windows": len(series),
            "points": points,
        }


    def get_zipf_rank_frequency(
        self,
        text_code: str,
        view_params: TokenViewParamsDTO,
        max_ranks: int = 500,
    ) -> dict[str, Any]:
        """Compute Zipf rank-frequency pairs for log10-log10 plotting."""
        text = self._repo.loader.load_text(text_code)
        view = self._repo.get_token_view(text, view_params)
        forms = view.forms

        df = rank_frequency(forms).head(max_ranks)
        ranks = df["rank"].tolist()
        freqs = df["freq"].tolist()

        return {
            "text_code": text_code,
            "total_types": len(df),
            "data": [
                {"rank": int(r), "freq": int(f)}
                for r, f in zip(ranks, freqs)
            ],
        }
