"""Service for lexical richness, LancsBox-X metrics, and Zipf rank-frequency analysis."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np

from corpus_toolkit.diversity import (
    diversity_metrics,
    mattr_series,
    rank_frequency,
)
from SPA.models.view_params_dto import CorpusScopeDTO, TokenViewParamsDTO
from SPA.repositories.corpus_repository import CorpusRepository


def masked_mattr_series(seq: Sequence[str | None], window: int) -> np.ndarray:
    """Slide positional window W over seq (where masked slots are None) and compute V_non_null / N_non_null."""
    n = len(seq)
    if n == 0:
        return np.asarray([], dtype=float)
    if n < window:
        valid = [s for s in seq if s is not None]
        return np.asarray([len(set(valid)) / len(valid) if valid else np.nan], dtype=float)

    counts: dict[str, int] = {}
    distinct = 0
    non_null = 0
    out = np.empty(n - window + 1, dtype=float)
    for i, tok in enumerate(seq):
        if tok is not None:
            non_null += 1
            c = counts.get(tok, 0)
            if c == 0:
                distinct += 1
            counts[tok] = c + 1
        if i >= window:
            old = seq[i - window]
            if old is not None:
                non_null -= 1
                counts[old] -= 1
                if counts[old] == 0:
                    distinct -= 1
        if i >= window - 1:
            out[i - window + 1] = (distinct / non_null) if non_null > 0 else np.nan
    return out


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
        vp_key = view_params.cache_key()
        is_masked = bool(view_params.filter_function_words and view_params.mode == "mask")

        records: list[dict[str, Any]] = []
        for t in texts:
            view = self._repo.get_token_view(t, view_params)
            text_code = getattr(t, "code", getattr(getattr(t, "record", None), "code", str(t)))
            analysed = [str(x) for x in view.analysed()]
            cache_key = (text_code, *vp_key, len(analysed), len(view.forms))
            if cache_key not in self._metrics_cache:
                metrics = diversity_metrics(analysed)
                if is_masked:
                    masked_seq = [
                        str(f) if elig else None
                        for f, elig in zip(view.forms, view.eligible)
                    ]
                    for w in (50, 100, 500):
                        s_m = masked_mattr_series(masked_seq, w)
                        valid_s = s_m[~np.isnan(s_m)]
                        metrics[f"MATTR_{w}"] = float(valid_s.mean()) if len(valid_s) else float("nan")
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
        text = self._repo.get_text_by_code(text_code) or self._repo.loader.load_text(text_code)
        view = self._repo.get_token_view(text, view_params)
        if view_params.filter_function_words and view_params.mode == "mask":
            masked_seq = [
                str(f) if elig else None
                for f, elig in zip(view.forms, view.eligible)
            ]
            series = masked_mattr_series(masked_seq, window=window)
        else:
            series = mattr_series([str(x) for x in view.analysed()], window=window)

        if len(series) == 0:
            return {"text_code": text_code, "window": window, "points": []}

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
        text = self._repo.get_text_by_code(text_code) or self._repo.loader.load_text(text_code)
        view = self._repo.get_token_view(text, view_params)
        forms = [str(x) for x in view.analysed()]

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

