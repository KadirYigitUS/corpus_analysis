"""Service providing GraphColl 2D scatter, sensitivity comparisons, and NLTK checks."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from corpus_toolkit import TokenView, collocation, nltk_adapter
from SPA.models.view_params_dto import TokenViewParamsDTO
from SPA.repositories.corpus_repository import CorpusRepository
from SPA.services.payload_cache import global_payload_cache
from SPA.services.payload_utils import df_to_table_payload


class CollocationVizService:
    def __init__(self, corpus_repo: CorpusRepository | None = None) -> None:
        self._repo = corpus_repo or CorpusRepository()
        self.repo = self._repo

    def get_graphcoll_scatter(
        self,
        code: str = "BR-SM",
        node: str = "robot",
        view_params: TokenViewParamsDTO | None = None,
        left: int = 5,
        right: int = 5,
        min_freq: int = 3,
    ) -> dict[str, Any]:
        vp = view_params or TokenViewParamsDTO(field="lem", filter_function_words=False, mode="drop", punct="drop")
        cache_key = global_payload_cache.build_key(
            "colloc:scatter", view=vp, code=code, node=node, left=left, right=right, min_freq=min_freq
        )
        if cached := global_payload_cache.get(cache_key):
            return cached

        text = self.repo.get_text_by_code(code) or self.repo.loader.load_text(code)
        try:
            view = self.repo.get_token_view(text, vp)
            tab = collocation.collocates(view, node, left=left, right=right, min_freq=min_freq, sort_by="G2")
            d = tab[tab["G2"] > 0].copy() if not tab.empty else tab
            top15_labels = set(d.sort_values("G2", ascending=False)["collocate"].head(15)) if not d.empty else set()

            points = []
            for _, r in d.head(300).iterrows():
                points.append({
                    "x": round(float(r["MI"]), 2),
                    "y": round(float(np.log10(max(1.0, float(r["G2"])))), 2),
                    "r": round(float(2.0 + 1.5 * np.sqrt(max(1.0, float(r["O11"])))), 1),
                    "label": str(r["collocate"]) if str(r["collocate"]) in top15_labels else None,
                })
            payload = {
                "title": f"'{node}' Eşdizimlileri: Çekim Gücü (MI) vs Kanıt (log10 G2)",
                "series": [{"name": node, "points": points}],
            }
            global_payload_cache.put(cache_key, payload)
            return payload
        finally:
            text.evict()

    def get_measure_and_window_sensitivity(
        self,
        code: str = "BR-SM",
        node: str = "robot",
        view_params: TokenViewParamsDTO | None = None,
        min_freq: int = 3,
    ) -> dict[str, Any]:
        vp = view_params or TokenViewParamsDTO(field="lem", filter_function_words=False, mode="drop", punct="drop")
        cache_key = global_payload_cache.build_key(
            "colloc:sens", view=vp, code=code, node=node, min_freq=min_freq
        )
        if cached := global_payload_cache.get(cache_key):
            return cached

        text = self.repo.get_text_by_code(code) or self.repo.loader.load_text(code)
        try:
            v_cur = self.repo.get_token_view(text, vp)
            tab = collocation.collocates(v_cur, node, left=5, right=5, min_freq=min_freq)

            top_measures = {
                m: (tab.sort_values(m, ascending=False)["collocate"].head(8).tolist() if not tab.empty else [])
                for m in ("MI", "MI2", "MI3", "T", "LogDice", "G2")
            }
            max_len = max((len(v) for v in top_measures.values()), default=0)
            for m in top_measures:
                top_measures[m] = top_measures[m] + [""] * (max_len - len(top_measures[m]))
            meas_df = pd.DataFrame(top_measures)

            v_raw = TokenView(text, vp.field, False, "drop", punct=vp.punct)  # type: ignore[arg-type]
            v_drop = TokenView(text, vp.field, True, "drop", punct=vp.punct)  # type: ignore[arg-type]
            v_mask = TokenView(text, vp.field, True, "mask", punct=vp.punct)  # type: ignore[arg-type]
            w_rows = {
                "Pencere": ["Ham ±2", "Ham ±10", "İçerik Drop ±5", "İçerik Mask ±5"],
                "En Üst Eşdizimler": [
                    ", ".join(collocation.collocates(v_raw, node, 2, 2, min_freq=min_freq)["collocate"].head(6)),
                    ", ".join(collocation.collocates(v_raw, node, 10, 10, min_freq=min_freq)["collocate"].head(6)),
                    ", ".join(collocation.collocates(v_drop, node, 5, 5, min_freq=min_freq)["collocate"].head(6)),
                    ", ".join(collocation.collocates(v_mask, node, 5, 5, min_freq=min_freq)["collocate"].head(6)),
                ],
            }
            payload = {
                "measures_table": df_to_table_payload(meas_df, title="Ölçüt Karşılaştırması (Top 8)"),
                "window_table": df_to_table_payload(pd.DataFrame(w_rows), title="Pencere ve Görünüm Duyarlılığı"),
            }
            global_payload_cache.put(cache_key, payload)
            return payload
        finally:
            text.evict()

    def get_nltk_bigrams(
        self,
        code: str = "BR-SM",
        view_params: TokenViewParamsDTO | None = None,
    ) -> dict[str, Any]:
        vp = view_params or TokenViewParamsDTO(field="lem", filter_function_words=True, mode="drop", punct="drop")
        cache_key = global_payload_cache.build_key("colloc:nltk", view=vp, code=code)
        if cached := global_payload_cache.get(cache_key):
            return cached

        text = self.repo.get_text_by_code(code) or self.repo.loader.load_text(code)
        try:
            v = self.repo.get_token_view(text, vp)
            collocs_df = nltk_adapter.nltk_collocations(v, n=10, min_freq=4, measure="likelihood_ratio")
            ngrams_df = nltk_adapter.top_ngrams(v, n=2, top=10)
            payload = {
                "collocations": df_to_table_payload(collocs_df, title="NLTK Bigram Eşdizimleri (Likelihood Ratio)"),
                "ngrams": df_to_table_payload(ngrams_df, title="En Sık Geçen 2-Gramlar"),
            }
            global_payload_cache.put(cache_key, payload)
            return payload
        finally:
            text.evict()

