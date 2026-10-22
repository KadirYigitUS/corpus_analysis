"""Service providing search frequency summary, view comparisons, and NLTK checks."""

from typing import Any

import pandas as pd

from corpus_toolkit import nltk_adapter, search
from SPA.repositories.corpus_repository import CorpusRepository
from SPA.services.payload_utils import df_to_table_payload


class SearchSummaryService:
    def __init__(self, corpus_repo: CorpusRepository | None = None) -> None:
        self._repo = corpus_repo or CorpusRepository()
        self.repo = self._repo

    def get_search_summary_and_bars(self, term: str, field: str = "lem", match: str = "exact") -> dict[str, Any]:
        engine = search.CorpusSearchEngine()
        texts = list(self.repo.loader.load_all())
        q = search.SearchQuery([term], field=field, match=match)
        res = engine.search(q, texts)

        summary_df = res.summary()
        bars_items = []
        for _, r in summary_df.iterrows():
            bars_items.append({
                "code": str(r["code"]),
                "hits": int(r["hits"]),
                "running_words": int(r["running_words"]),
                "per10k": round(float(r["per10k"]), 2),
                "color_key": str(r["code"]).split("-")[-1] if "-" in str(r["code"]) else "DEFAULT",
            })

        return {
            "table": df_to_table_payload(summary_df, title=f"'{term}' Arama Özeti"),
            "bars": bars_items,
            "total_hits": int(summary_df["hits"].sum()),
        }

    def get_views_comparison(self, term: str) -> dict[str, Any]:
        engine = search.CorpusSearchEngine()
        turkish_texts = list(self.repo.loader.load_all_turkish())
        rows = []
        for fw, mode in [(False, "drop"), (True, "drop"), (True, "mask")]:
            q = search.SearchQuery([term], "lem", filter_function_words=fw, mode=mode)
            s = engine.search(q, turkish_texts).summary()
            total_hits = int(s["hits"].sum())
            running = int(s["running_words"].sum())
            per10k = 1e4 * total_hits / max(running, 1)
            rows.append({
                "filter_function_words": "İçerik (True)" if fw else "Ham (False)",
                "mode": mode,
                "total_hits": total_hits,
                "running_words": running,
                "per10k": round(per10k, 2),
            })
        return df_to_table_payload(pd.DataFrame(rows), title="Görünüm Karşılaştırması (Ham vs İçerik, Drop vs Mask)")

    def get_nltk_concordance_and_similar(self, code: str, word: str, width: int = 70, lines: int = 6) -> dict[str, Any]:
        from corpus_toolkit import TokenView
        text = self.repo.loader.load_text(code)
        try:
            v = TokenView(text, "tok", False)
            conc_lines = list(nltk_adapter.nltk_concordance(v, word, width=width, lines=lines))
            similar_words = list(nltk_adapter.nltk_similar(v, word, 6))
            return {
                "text_code": code,
                "word": word,
                "concordance": conc_lines,
                "similar": similar_words,
            }
        finally:
            text.evict()
