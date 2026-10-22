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
        texts = self._repo.get_texts_by_scope(scope) if scope else list(loader.load_all())
        allowed_codes = {t.record.code for t in texts}
        sizes = loader.load_all().summary()
        merged = sizes.merge(inv[["code", "focal_code", "year"]], on="code")
        merged = merged[merged["code"].isin(allowed_codes)]

        items = []
        for _, row in merged.iterrows():
            code_str = str(row["code"])
            focal = str(row["focal_code"])
            if view and (view.filter_function_words or view.punct != "drop"):
                t_obj = self._repo.get_text_by_code(code_str)
                tok_n = len(self._repo.get_token_view(t_obj, view).analysed()) if t_obj else int(row["tokens"])
            else:
                tok_n = int(row["tokens"])
            items.append({
                "code": code_str,
                "title": str(row["title"]),
                "tokens": tok_n,
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
        if scope:
            allowed = {t.record.code for t in self._repo.get_texts_by_scope(scope)}
            df = df[df["code"].isin(allowed)].reset_index(drop=True)
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
        if scope:
            allowed = {t.record.code for t in self._repo.get_texts_by_scope(scope)}
            df = df[df["code"].isin(allowed)].reset_index(drop=True)
        if view and (view.filter_function_words or view.punct != "drop") and not df.empty:
            df = df.copy()
            df["tokens"] = [
                len(self._repo.get_token_view(t, view).analysed())
                if (t := self._repo.get_text_by_code(str(c))) is not None
                else int(orig)
                for c, orig in zip(df["code"], df["tokens"])
            ]
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

        vp = view or TokenViewParamsDTO(field="lem", filter_function_words=True, mode="drop", punct="drop")
        texts = self._repo.get_texts_by_scope(scope) if scope else list(self._repo.loader.load_all())
        rows = []
        for t in texts:
            try:
                from corpus_toolkit import TokenView
                tv = TokenView(
                    t,
                    field=vp.field if view else "lem",  # type: ignore[arg-type]
                    filter_function_words=vp.filter_function_words if view else True,
                    mode=vp.mode,  # type: ignore[arg-type]
                    punct=vp.punct,  # type: ignore[arg-type]
                )
                n = len(tv.analysed())
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
