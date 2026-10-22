"""Service computing corpus size distribution, verification, and schema previews."""

from typing import Any

import pandas as pd

from corpus_toolkit import viz
from SPA.models.view_params_dto import CorpusScopeDTO, TokenViewParamsDTO
from SPA.repositories.corpus_repository import CorpusRepository
from SPA.services.payload_cache import global_payload_cache
from SPA.services.payload_utils import df_to_table_payload


class InventoryTablesService:
    def __init__(self, corpus_repo: CorpusRepository | None = None) -> None:
        self._repo = corpus_repo or CorpusRepository()
        self.repo = self._repo

    def get_sizes_chart_data(
        self,
        scope: CorpusScopeDTO | None = None,
        view: TokenViewParamsDTO | None = None,
    ) -> dict[str, Any]:
        cache_key = global_payload_cache.build_key("inv:sizes_chart", scope=scope, view=view)
        cached = global_payload_cache.get(cache_key)
        if cached:
            return cached

        loader = self._repo.loader
        inv = loader.registry.inventory()
        sizes = loader.load_all().summary()
        merged = sizes.merge(inv[["code", "focal_code", "year"]], on="code")

        items = []
        for _, row in merged.iterrows():
            focal = str(row["focal_code"])
            items.append({
                "code": str(row["code"]),
                "title": str(row["title"]),
                "tokens": int(row["tokens"]),
                "sentences": int(row["sentences"]),
                "focal_code": focal,
                "year": int(row["year"]) if pd.notna(row["year"]) else 0,
                "color_key": focal,
                "color": viz.color_for(focal),
            })

        payload = {"items": items, "title": "Metin Boyutları Dağılımı"}
        global_payload_cache.put(cache_key, payload)
        return payload

    def get_verify_files_table(
        self,
        scope: CorpusScopeDTO | None = None,
        view: TokenViewParamsDTO | None = None,
    ) -> dict[str, Any]:
        cache_key = global_payload_cache.build_key("inv:verify_files", scope=scope, view=view)
        cached = global_payload_cache.get(cache_key)
        if cached:
            return cached

        df = self._repo.loader.registry.verify_files()
        payload = df_to_table_payload(df, title="Disk Pickle Doğrulama Tablosu")
        global_payload_cache.put(cache_key, payload)
        return payload

    def get_size_summary_table(
        self,
        scope: CorpusScopeDTO | None = None,
        view: TokenViewParamsDTO | None = None,
    ) -> dict[str, Any]:
        cache_key = global_payload_cache.build_key("inv:size_summary", scope=scope, view=view)
        cached = global_payload_cache.get(cache_key)
        if cached:
            return cached

        df = self._repo.loader.load_all().summary().sort_values(["author_translator", "type"])
        payload = df_to_table_payload(df, title="Derlem Boyut Özeti")
        global_payload_cache.put(cache_key, payload)
        return payload

    def get_memory_report_table(self) -> dict[str, Any]:
        df = self._repo.loader.memory_report()
        return df_to_table_payload(df, title="Bellek Kullanım Raporu")

    def get_content_lemmas_summary(
        self,
        scope: CorpusScopeDTO | None = None,
        view: TokenViewParamsDTO | None = None,
    ) -> dict[str, Any]:
        cache_key = global_payload_cache.build_key("inv:content_lemmas", scope=scope, view=view)
        cached = global_payload_cache.get(cache_key)
        if cached:
            return cached

        rows = []
        for t in self._repo.loader.load_all().iter_evicting():
            try:
                from corpus_toolkit import TokenView
                n = len(TokenView(t, "lem", filter_function_words=True))
                rows.append({
                    "author_translator": t.record.focal_name,
                    "title": t.record.title,
                    "code": t.record.code,
                    "content_lemmas": n,
                })
            finally:
                t.evict()

        df = pd.DataFrame(rows)
        payload = df_to_table_payload(df, title="Metin Başına İçerik Kök Sayıları")
        global_payload_cache.put(cache_key, payload)
        return payload

    def get_head_preview(self, code: str, n: int = 8) -> dict[str, Any]:
        text = self._repo.loader.load_text(code)
        try:
            tokens_head = text.tokens.head(n)
            sents_head = text.sentences.head(n)
            return {
                "tokens": df_to_table_payload(tokens_head, title=f"{code} Tokens Preview (Head {n})"),
                "sentences": df_to_table_payload(sents_head, title=f"{code} Sentences Preview (Head {n})"),
            }
        finally:
            text.evict()
