"""Service generating live Markdown report preview and top/bottom evidence summaries."""

from typing import Any

import pandas as pd

from corpus_toolkit import analysis, reporter
from SPA.repositories.corpus_repository import CorpusRepository
from SPA.services.payload_utils import df_to_table_payload


class ReporterPreviewService:
    def __init__(self, corpus_repo: CorpusRepository | None = None) -> None:
        self._repo = corpus_repo or CorpusRepository()
        self.repo = self._repo

    def get_live_markdown_and_summary(self) -> dict[str, Any]:
        loader = self.repo.loader
        div_raw = analysis.diversity_for(loader, loader.load_all(), field="lem", filter_function_words=False)
        d = div_raw.reset_index()[["index", "MTLD"]].dropna()
        if not d.empty:
            hi = d.loc[d["MTLD"].idxmax()]
            lo = d.loc[d["MTLD"].idxmin()]
            top_id, top_val = str(hi["index"]), round(float(hi["MTLD"]), 1)
            bot_id, bot_val = str(lo["index"]), round(float(lo["MTLD"]), 1)
            mean_val, std_val = round(float(d["MTLD"].mean()), 1), round(float(d["MTLD"].std()), 1)
        else:
            top_id, top_val = "-", 0.0
            bot_id, bot_val = "-", 0.0
            mean_val, std_val = 0.0, 0.0

        summary_sentence = reporter.top_bottom_summary(div_raw.reset_index(), "MTLD", "index")

        markdown_text = f"""# 📊 Türk Bilimkurgu Yazar-Çevirmenleri Derlem Raporu

**Tarih:** 2026-10-21 | **Kapsam:** 13 Odak Metin (Selma MİNE, Zühtü BAYAR, Özlem KURDOĞLU)

## 1. Sözcüksel Zenginlik & Çeşitlilik Özeti
- **En Yüksek MTLD (Zengin Çeşitlilik):** {top_id} ({top_val})
- **En Düşük MTLD (Yoğun Tekrar):** {bot_id} ({bot_val})
- **Ortalama MTLD:** {mean_val} (std: {std_val})
- **Otomatik Özet:** {summary_sentence}

## 2. Metodolojik Çerçeve ve Doğruluk
Bu rapor, üç düzeyli veri-kanıt sözleşmesi (Data-Evidence Contract) uyarınca doğrudan Parquet tablolarından derlenmiştir.
"""
        summary_rows = [
            {"Metrik": "MTLD En Yüksek", "Değer": str(top_val), "Metin": str(top_id)},
            {"Metrik": "MTLD En Düşük", "Değer": str(bot_val), "Metin": str(bot_id)},
            {"Metrik": "MTLD Ortalama", "Değer": str(mean_val), "Metin": "Tüm Derlem"},
        ]
        return {
            "markdown": markdown_text,
            "summary_table": df_to_table_payload(pd.DataFrame(summary_rows), title="Veri-Kanıt Özeti (Top/Bottom Summary)"),
        }
