"""Service generating live research report preview, structured cards, and top/bottom evidence summaries."""

from __future__ import annotations

from typing import Any

import pandas as pd

from corpus_toolkit import analysis, reporter
from SPA.models.view_params_dto import CorpusScopeDTO, TokenViewParamsDTO
from SPA.repositories.corpus_repository import CorpusRepository
from SPA.services.payload_cache import global_payload_cache
from SPA.services.payload_utils import df_to_table_payload


class ReporterPreviewService:
    def __init__(self, corpus_repo: CorpusRepository | None = None) -> None:
        self._repo = corpus_repo or CorpusRepository()
        self.repo = self._repo

    def get_live_markdown_and_summary(
        self,
        scope: CorpusScopeDTO | None = None,
        view_params: TokenViewParamsDTO | None = None,
    ) -> dict[str, Any]:
        sc = scope or CorpusScopeDTO(scope="all")
        vp = view_params or TokenViewParamsDTO(field="lem", filter_function_words=False)
        cache_key = global_payload_cache.build_key("rep:preview", scope=sc, view=vp)
        if cached := global_payload_cache.get(cache_key):
            return cached

        loader = self.repo.loader
        texts = self.repo.get_texts_by_scope(sc) or list(loader.load_all())
        div_raw = analysis.diversity_for(
            loader,
            texts,
            field=vp.field,  # type: ignore[arg-type]
            filter_function_words=vp.filter_function_words,
            mode=vp.mode,  # type: ignore[arg-type]
            punct=vp.punct,  # type: ignore[arg-type]
        )
        d = div_raw.reset_index()[["index", "MTLD"]].dropna()
        if not d.empty:
            hi = d.loc[d["MTLD"].idxmax()]
            lo = d.loc[d["MTLD"].idxmin()]
            top_id, top_val = str(hi["index"]), round(float(hi["MTLD"]), 1)
            bot_id, bot_val = str(lo["index"]), round(float(lo["MTLD"]), 1)
            mean_val = round(float(d["MTLD"].mean()), 1)
            std_val = round(float(d["MTLD"].std(ddof=0)), 1) if len(d) > 1 else 0.0
        else:
            top_id, top_val = "-", 0.0
            bot_id, bot_val = "-", 0.0
            mean_val, std_val = 0.0, 0.0

        summary_sentence = reporter.top_bottom_summary(div_raw.reset_index(), "MTLD", "index")
        view_label = f"field={vp.field}, fw={vp.filter_function_words}, mode={vp.mode}, punct={vp.punct}"

        markdown_text = f"""# 📊 Türk Bilimkurgu Yazar-Çevirmenleri Derlem Raporu

**Tarih:** 2026-10-22 | **Kapsam:** {sc.scope} ({len(texts)} Metin) | **Görünüm:** `{view_label}`

## 1. Sözcüksel Zenginlik & Çeşitlilik Özeti
- **En Yüksek MTLD (Zengin Çeşitlilik):** {top_id} ({top_val})
- **En Düşük MTLD (Yoğun Tekrar):** {bot_id} ({bot_val})
- **Ortalama MTLD:** {mean_val} (std: {std_val})
- **Otomatik Özet:** {summary_sentence}

## 2. Metodolojik Çerçeve ve Doğruluk
Bu rapor, üç düzeyli veri-kanıt sözleşmesi (Data-Evidence Contract) uyarınca doğrudan Parquet tablolarından derlenmiştir.
"""
        sections = [
            {
                "title": "1. Sözcüksel Zenginlik & Çeşitlilik Özeti (MTLD_0.72)",
                "items": [
                    f"<b>En Yüksek MTLD (Zengin Çeşitlilik):</b> {top_id} (<code>{top_val}</code>)",
                    f"<b>En Düşük MTLD (Yoğun Tekrar):</b> {bot_id} (<code>{bot_val}</code>)",
                    f"<b>Ortalama MTLD (&mu; &pm; &sigma;):</b> <code>{mean_val} &pm; {std_val}</code>",
                    f"<b>Otomatik Özet:</b> {summary_sentence}",
                ],
            },
            {
                "title": "2. Metodolojik Çerçeve ve Veri-Kanıt Sözleşmesi",
                "items": [
                    f"<b>Aktif Kapsam:</b> <code>{sc.scope}</code> ({len(texts)} metin)",
                    f"<b>TokenView Matrisi:</b> <code>{view_label}</code>",
                    "Üç düzeyli veri-kanıt sözleşmesi (Data-Evidence Contract) uyarınca doğrudan Parquet v3 tablolarından derlenmiştir.",
                ],
            },
        ]
        summary_rows = [
            {"Metrik": "MTLD En Yüksek", "Değer": str(top_val), "Metin": str(top_id)},
            {"Metrik": "MTLD En Düşük", "Değer": str(bot_val), "Metin": str(bot_id)},
            {"Metrik": "MTLD Ortalama (μ ± σ)", "Değer": f"{mean_val} ± {std_val}", "Metin": f"Kapsam ({sc.scope}: {len(texts)} metin)"},
        ]
        payload = {
            "markdown": markdown_text,
            "kpis": {
                "scope": sc.scope,
                "text_count": len(texts),
                "view_label": view_label,
                "top_id": top_id,
                "top_val": top_val,
                "bot_id": bot_id,
                "bot_val": bot_val,
                "mean_val": mean_val,
                "std_val": std_val,
            },
            "sections": sections,
            "summary_table": df_to_table_payload(pd.DataFrame(summary_rows), title="Veri-Kanıt Özeti (Top/Bottom Summary)"),
        }
        global_payload_cache.put(cache_key, payload)
        return payload
