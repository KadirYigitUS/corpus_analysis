"""Service providing parallel alignment structure summary and downsampled scatter data."""

from typing import Any

from corpus_toolkit import alignment
from SPA.repositories.corpus_repository import CorpusRepository
from SPA.services.payload_cache import global_payload_cache
from SPA.services.payload_utils import df_to_table_payload


class AlignmentStructureService:
    def __init__(self, corpus_repo: CorpusRepository | None = None) -> None:
        self.repo = corpus_repo or CorpusRepository()

    def get_structure_summary(self) -> dict[str, Any]:
        cache_key = "align:structure_summary"
        cached = global_payload_cache.get(cache_key)
        if cached:
            return cached

        loader = self.repo.loader
        pairs = [p for p, _, _ in loader.load_translation_pairs()]
        ana = alignment.AlignmentStructureAnalyzer(loader.cache)
        summary_df = ana.summary(pairs)

        types = list(alignment.ALIGN_TYPES)
        stacked_map: dict[str, list[float]] = {}
        for ty in types:
            col_name = f"{ty}_pct"
            if col_name in summary_df.columns:
                stacked_map[ty] = [round(float(v), 1) for v in summary_df[col_name]]
            else:
                stacked_map[ty] = [0.0] * len(summary_df)

        payload = {
            "table": df_to_table_payload(summary_df.round(2), title="Paralel Hizalama Yapısı Özeti"),
            "stacked": {
                "pairs": [str(p) for p in summary_df["pair"]],
                "types": types,
                "pct": stacked_map,
                "colors": dict(alignment.ALIGN_TYPES and {
                    "1:1": "#34d399", "1:N": "#38bdf8", "N:1": "#fbbf24",
                    "N:M": "#a78bfa", "omission": "#fb7185", "addition": "#94a3b8"
                }),
            },
        }
        global_payload_cache.put(cache_key, payload)
        return payload

    def get_scatter_data(self, selected_pairs: list[str] | None = None, max_points: int = 1500) -> dict[str, Any]:
        loader = self.repo.loader
        pairs = [p for p, _, _ in loader.load_translation_pairs()]
        ana = alignment.AlignmentStructureAnalyzer(loader.cache)

        series_list = []
        for _i, pair in enumerate(pairs):
            pair_code = f"{pair.eng.code}_{pair.tur.code}"
            label = f"{pair.tur.title[:24]}"
            if selected_pairs and pair_code not in selected_pairs and label not in selected_pairs:
                continue

            card_table = ana.cardinality_table(pair)
            one = card_table[card_table["type"] == "1:1"]
            if len(one) == 0:
                continue

            # Compute true slope over all 1:1 points
            full_eng = one["eng_words"].to_numpy(dtype=float)
            full_tur = one["tur_words"].to_numpy(dtype=float)
            slope = float((full_eng * full_tur).sum() / max((full_eng ** 2).sum(), 1.0))

            # Sample points for light client rendering
            if len(one) > max_points:
                one = one.sample(max_points, random_state=13)

            points = []
            for _, r in one.iterrows():
                points.append({
                    "x": float(r["eng_words"]),
                    "y": float(r["tur_words"]),
                    "r": 2.5,
                })

            series_list.append({
                "name": f"{label} (slope {slope:.2f})",
                "pair_code": pair_code,
                "points": points,
                "slope": round(slope, 2),
            })

        return {
            "title": "Length Relation in 1:1 Alignments",
            "series": series_list,
        }
