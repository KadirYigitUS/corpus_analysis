"""Service providing GraphColl 2D scatter, sensitivity comparisons, and NLTK checks."""

from typing import Any

import numpy as np
import pandas as pd

from corpus_toolkit import TokenView, collocation, nltk_adapter
from SPA.repositories.corpus_repository import CorpusRepository
from SPA.services.payload_utils import df_to_table_payload


class CollocationVizService:
    def __init__(self, corpus_repo: CorpusRepository | None = None) -> None:
        self.repo = corpus_repo or CorpusRepository()

    def get_graphcoll_scatter(self, code: str = "BR-SM", node: str = "robot") -> dict[str, Any]:
        text = self.repo.loader.load_text(code)
        try:
            view = TokenView(text, "lem", False, "drop")
            tab = collocation.collocates(view, node, left=5, right=5, min_freq=3, sort_by="G2")
            d = tab[tab["G2"] > 0].copy()
            top15_labels = set(d.sort_values("G2", ascending=False)["collocate"].head(15))

            points = []
            for _, r in d.head(300).iterrows():
                points.append({
                    "x": round(float(r["MI"]), 2),
                    "y": round(float(np.log10(max(1.0, float(r["G2"])))), 2),
                    "r": round(float(2.0 + 1.5 * np.sqrt(max(1.0, float(r["O11"])))), 1),
                    "label": str(r["collocate"]) if str(r["collocate"]) in top15_labels else None,
                })
            return {
                "title": f"'{node}' Eşdizimlileri: Çekim Gücü (MI) vs Kanıt (log10 G2)",
                "series": [{"name": node, "points": points}],
            }
        finally:
            text.evict()

    def get_measure_and_window_sensitivity(self, code: str = "BR-SM", node: str = "robot") -> dict[str, Any]:
        text = self.repo.loader.load_text(code)
        try:
            v_raw = TokenView(text, "lem", False, "drop")
            tab = collocation.collocates(v_raw, node, left=5, right=5, min_freq=3)

            top_measures = {
                m: tab.sort_values(m, ascending=False)["collocate"].head(8).tolist()
                for m in ("MI", "T", "LogDice", "G2")
            }
            meas_df = pd.DataFrame(top_measures)

            # Window sensitivity
            w_rows = {
                "Pencere": ["Ham ±2", "Ham ±10", "İçerik Drop ±5", "İçerik Mask ±5"],
                "En Üst Eşdizimler": [
                    ", ".join(collocation.collocates(v_raw, node, 2, 2, min_freq=3)["collocate"].head(6)),
                    ", ".join(collocation.collocates(v_raw, node, 10, 10, min_freq=3)["collocate"].head(6)),
                    ", ".join(collocation.collocates(TokenView(text, "lem", True, "drop"), node, 5, 5, min_freq=3)["collocate"].head(6)),
                    ", ".join(collocation.collocates(TokenView(text, "lem", True, "mask"), node, 5, 5, min_freq=3)["collocate"].head(6)),
                ],
            }
            return {
                "measures_table": df_to_table_payload(meas_df, title="Ölçüt Karşılaştırması (Top 8)"),
                "window_table": df_to_table_payload(pd.DataFrame(w_rows), title="Pencere ve Görünüm Duyarlılığı"),
            }
        finally:
            text.evict()

    def get_nltk_bigrams(self, code: str = "BR-SM") -> dict[str, Any]:
        text = self.repo.loader.load_text(code)
        try:
            v = TokenView(text, "lem", True)
            collocs_df = nltk_adapter.nltk_collocations(v, n=10, min_freq=4, measure="likelihood_ratio")
            ngrams_df = nltk_adapter.top_ngrams(v, n=2, top=10)
            return {
                "collocations": df_to_table_payload(collocs_df, title="NLTK Bigram Eşdizimleri (Likelihood Ratio)"),
                "ngrams": df_to_table_payload(ngrams_df, title="En Sık Geçen 2-Gramlar"),
            }
        finally:
            text.evict()
