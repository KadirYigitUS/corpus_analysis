"""Service for Union-Slot collocation statistics and GraphColl radial networks."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from corpus_toolkit.collocation import collocates
from SPA.models.stats_dto import CollocationParamsDTO
from SPA.models.view_params_dto import TokenViewParamsDTO
from SPA.repositories.corpus_repository import CorpusRepository


class CollocationService:
    """Manages Tab 9 Union-Slot collocation calculations and GraphColl radial networks."""

    def __init__(self, corpus_repo: CorpusRepository) -> None:
        self._repo = corpus_repo

    def get_collocations(
        self,
        colloc_params: CollocationParamsDTO,
        view_params: TokenViewParamsDTO,
    ) -> dict[str, Any]:
        """Compute collocation table and GraphColl network nodes for the requested parameters."""
        text_code = colloc_params.text_code
        if not text_code:
            # Default to first available text if none specified
            inv = self._repo.get_inventory_table()
            text_code = inv[0]["text_code"] if inv else ""

        if not text_code:
            return {"error": "No text available"}

        text = self._repo.loader.load_text(text_code)
        view = self._repo.get_token_view(text, view_params)

        df = collocates(
            view=view,
            nodes=colloc_params.node_query,
            left=colloc_params.left_span,
            right=colloc_params.right_span,
            sentence_clamped=colloc_params.sentence_clamped,
            min_freq=colloc_params.min_freq,
            sort_by=colloc_params.stat_metric,
        )

        attrs = df.attrs
        f_node = int(attrs.get("f_node", 0))
        n_tokens = int(attrs.get("N", 0))
        r1_slots = int(attrs.get("R1", 0))

        records: list[dict[str, Any]] = []
        graphcoll_nodes: list[dict[str, Any]] = []

        # GraphColl central node
        graphcoll_nodes.append({
            "id": colloc_params.node_query,
            "label": colloc_params.node_query,
            "is_center": True,
            "radius": 0,
            "angle": 0,
            "size": 25,
            "freq": f_node,
        })

        if not df.empty:
            clean_df = df.replace({np.nan: None})
            # Take top 50 for the table and graph
            top_df = clean_df.head(50)
            max_score = float(top_df[colloc_params.stat_metric].max() or 1.0)
            min_score = float(top_df[colloc_params.stat_metric].min() or 0.0)
            score_range = max(0.001, max_score - min_score)

            for idx, r in top_df.iterrows():
                val = r[colloc_params.stat_metric]
                val_num = float(val) if val is not None else 0.0

                records.append({
                    "collocate": str(r["collocate"]),
                    "O11": int(r["O11"]),
                    "C1": int(r["C1"]),
                    "E11": round(float(r["E11"]), 2),
                    "MI": round(float(r["MI"]), 3) if r["MI"] is not None else None,
                    "MI2": round(float(r["MI2"]), 3) if r["MI2"] is not None else None,
                    "MI3": round(float(r["MI3"]), 3) if r["MI3"] is not None else None,
                    "T": round(float(r["T"]), 3) if r["T"] is not None else None,
                    "G2": round(float(r["G2"]), 3) if r["G2"] is not None else None,
                    "LogDice": round(float(r["LogDice"]), 3) if r["LogDice"] is not None else None,
                })

                # Radial placement: higher association = closer to center (smaller radius)
                norm_dist = 1.0 - ((val_num - min_score) / score_range)
                radius = 60 + norm_dist * 200  # radius between 60px and 260px
                angle = (idx * (360.0 / max(1, len(top_df)))) * (math.pi / 180.0)

                graphcoll_nodes.append({
                    "id": str(r["collocate"]),
                    "label": str(r["collocate"]),
                    "is_center": False,
                    "radius": round(radius, 1),
                    "angle": round(angle, 3),
                    "x": round(radius * math.cos(angle), 1),
                    "y": round(radius * math.sin(angle), 1),
                    "size": min(20, max(6, int(math.log2(int(r["O11"]) + 1) * 3))),
                    "freq": int(r["O11"]),
                    "score": round(val_num, 3),
                })

        return {
            "text_code": text_code,
            "node": colloc_params.node_query,
            "f_node": f_node,
            "N": n_tokens,
            "R1": r1_slots,
            "metric": colloc_params.stat_metric,
            "items": records,
            "graphcoll_nodes": graphcoll_nodes,
        }
