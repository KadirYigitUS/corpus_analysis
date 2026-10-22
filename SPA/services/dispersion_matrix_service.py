"""Service computing semantic group counts, dispersion curves, and correlation matrices."""

from typing import Any

import numpy as np

from corpus_toolkit import batch_kwic
from SPA.repositories.corpus_repository import CorpusRepository
from SPA.services.payload_utils import df_to_table_payload


class DispersionMatrixService:
    def __init__(self, corpus_repo: CorpusRepository | None = None) -> None:
        self._repo = corpus_repo or CorpusRepository()
        self.repo = self._repo

    def analyze_dispersion(self, raw_input: str, field: str = "lem", is_content: bool = False) -> dict[str, Any]:
        bk = batch_kwic.BatchKwicAnalyzer()
        turkish_texts = list(self.repo.loader.load_all_turkish())

        # Parse either named groups ("makine: robot, makine | insan: insan") or comma terms
        terms_or_dict: Any
        if ":" in raw_input and "|" in raw_input:
            groups_dict = {}
            for chunk in raw_input.split("|"):
                if ":" in chunk:
                    name, words_part = chunk.split(":", 1)
                    groups_dict[name.strip()] = [w.strip() for w in words_part.split(",") if w.strip()]
            terms_or_dict = groups_dict
        elif ":" in raw_input:
            name, words_part = raw_input.split(":", 1)
            terms_or_dict = {name.strip(): [w.strip() for w in words_part.split(",") if w.strip()]}
        else:
            terms_or_dict = [w.strip() for w in raw_input.split(",") if w.strip()]

        out = bk.analyze(terms_or_dict, turkish_texts, field=field, filter_function_words=is_content)

        # 1. Counts and Rates Tables
        counts_table = df_to_table_payload(out.counts, title="Ham Bulgu Sayımları")
        rates_table = df_to_table_payload(out.rates.round(1), title="10 Bin Sözcük Başına Sıklık (Per10k)")
        summary_table = df_to_table_payload(out.summary().round(3), title="Yayılım Özeti (Juilland D)")

        # 2. Şekil 3A: Rates Heatmap Matrix
        rates_matrix = {
            "title": "Şekil 3A: 10 000 Akan Sözcük Başına Sıklık (Per10k)",
            "rows": list(out.rates.index),
            "cols": list(out.rates.columns),
            "values": [[round(float(v), 1) for v in row] for row in out.rates.to_numpy()],
            "fmt": ".0f",
            "scale": "seq",
        }

        # 3. Şekil 3B: Pearson r Correlation Matrix
        corr_df = out.matrix("pearson_r")
        corr_matrix = {
            "title": "Şekil 3B: Sözcük Profilleri Arasında Pearson r Bağıntısı",
            "rows": list(corr_df.index),
            "cols": list(corr_df.columns),
            "values": [[(round(float(v), 2) if not np.isnan(v) else 0.0) for v in row] for row in corr_df.to_numpy()],
            "fmt": ".2f",
            "scale": "div",
            "center": 0.0,
        }

        # 4. Şekil 3C: 10-Chunk Dispersion Series
        labels = list(out.chunks.keys())
        first_label = labels[0] if labels else ""
        first_chunks = out.chunks[first_label] if first_label else np.zeros((len(out.codes), 10))

        chunk_series = []
        for i, code in enumerate(out.codes):
            chunk_series.append({
                "name": code,
                "x": list(range(1, 11)),
                "y": [round(float(v), 1) for v in first_chunks[i]],
            })

        return {
            "counts": counts_table,
            "rates": rates_table,
            "summary": summary_table,
            "rates_matrix": rates_matrix,
            "corr_matrix": corr_matrix,
            "chunk_series": chunk_series,
            "label_name": first_label,
        }
