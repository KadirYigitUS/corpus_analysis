"""Service computing semantic group counts, dispersion curves, and correlation matrices."""

from __future__ import annotations

from typing import Any

import numpy as np

from corpus_toolkit import batch_kwic
from SPA.models.view_params_dto import CorpusScopeDTO, TokenViewParamsDTO
from SPA.repositories.corpus_repository import CorpusRepository
from SPA.services.payload_cache import global_payload_cache
from SPA.services.payload_utils import df_to_table_payload


class DispersionMatrixService:
    def __init__(self, corpus_repo: CorpusRepository | None = None) -> None:
        self._repo = corpus_repo or CorpusRepository()
        self.repo = self._repo

    def analyze_dispersion(
        self,
        raw_input: str,
        field: str = "lem",
        is_content: bool = False,
        scope: CorpusScopeDTO | None = None,
        view_params: TokenViewParamsDTO | None = None,
    ) -> dict[str, Any]:
        sc = scope or CorpusScopeDTO(scope="all_tr")
        vp = view_params or TokenViewParamsDTO(
            field=field, filter_function_words=is_content, mode="drop", punct="drop"
        )
        eff_field = vp.field if view_params else field
        eff_fw = vp.filter_function_words if view_params else is_content
        cache_key = global_payload_cache.build_key(
            "disp:matrices",
            scope=sc,
            view=vp,
            raw_input=raw_input,
            eff_field=eff_field,
            eff_fw=eff_fw,
        )
        if cached := global_payload_cache.get(cache_key):
            return cached

        bk = batch_kwic.BatchKwicAnalyzer()
        texts = self.repo.get_texts_by_scope(sc) or list(self.repo.loader.load_all_turkish())

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

        out = bk.analyze(
            terms_or_dict,
            texts,
            field=eff_field,  # type: ignore[arg-type]
            filter_function_words=eff_fw,
            mode=vp.mode,  # type: ignore[arg-type]
            punct=vp.punct,  # type: ignore[arg-type]
        )

        counts_table = df_to_table_payload(out.counts, title="Ham Bulgu Sayımları")
        rates_table = df_to_table_payload(out.rates.round(1), title="10 Bin Sözcük Başına Sıklık (Per10k)")
        summary_table = df_to_table_payload(out.summary().round(3), title="Yayılım Özeti (Juilland D)")

        rates_matrix = {
            "title": "Şekil 3A: 10 000 Akan Sözcük Başına Sıklık (Per10k)",
            "rows": list(out.rates.index),
            "cols": list(out.rates.columns),
            "values": [[round(float(v), 1) for v in row] for row in out.rates.to_numpy()],
            "fmt": ".0f",
            "scale": "seq",
        }

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

        payload = {
            "counts": counts_table,
            "rates": rates_table,
            "summary": summary_table,
            "rates_matrix": rates_matrix,
            "corr_matrix": corr_matrix,
            "chunk_series": chunk_series,
            "label_name": first_label,
        }
        global_payload_cache.put(cache_key, payload)
        return payload

