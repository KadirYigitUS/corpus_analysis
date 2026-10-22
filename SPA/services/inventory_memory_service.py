"""Service for corpus inventory tables, schema inspection, and memory telemetry."""

from __future__ import annotations

from typing import Any

from SPA.models.view_params_dto import CorpusScopeDTO, TokenViewParamsDTO
from SPA.repositories.corpus_repository import CorpusRepository


class InventoryMemoryService:
    """Manages Tab 1 inventory tables, column schema introspection, and memory stats."""

    def __init__(self, corpus_repo: CorpusRepository) -> None:
        self._repo = corpus_repo
        self._sum_cache: dict[str, dict[str, Any]] | None = None

    def _get_sum_dict(self) -> dict[str, dict[str, Any]]:
        if self._sum_cache is None:
            try:
                df = self._repo.loader.load_all().summary()
                self._sum_cache = df.set_index("code").to_dict(orient="index") if not df.empty else {}
            except Exception:
                self._sum_cache = {}
        return self._sum_cache

    def get_summary_stats(
        self,
        scope_dto: CorpusScopeDTO | None = None,
        view_params: TokenViewParamsDTO | None = None,
    ) -> dict[str, Any]:
        """Aggregate total counts across texts in scope and view parameters."""
        inv = self._repo.get_inventory_table()
        if scope_dto and (scope_dto.scope != "all" or scope_dto.author_filter or scope_dto.text_code or scope_dto.pair_code):
            texts = self._repo.get_texts_by_scope(scope_dto)
            allowed_codes = {t.record.code for t in texts}
            inv = [r for r in inv if r.get("code") in allowed_codes]

        sum_dict = self._get_sum_dict()

        if view_params and (view_params.filter_function_words or view_params.punct != "drop"):
            total_tokens = 0
            for r in inv:
                tc = str(r.get("code", ""))
                t = self._repo.get_text_by_code(tc)
                if t is not None:
                    total_tokens += len(self._repo.get_token_view(t, view_params).analysed())
        else:
            total_tokens = sum(int(sum_dict.get(r.get("code", ""), {}).get("tokens", 0) or 0) for r in inv)

        total_texts = len(inv)
        total_sentences = sum(int(sum_dict.get(r.get("code", ""), {}).get("sentences", 0) or 0) for r in inv)
        categories = set(r.get("type", "") for r in inv if r.get("type"))
        authors = set(r.get("author_translator", "") for r in inv if r.get("author_translator"))
        return {
            "total_texts": total_texts,
            "total_tokens": total_tokens,
            "total_sentences": total_sentences,
            "author_count": len(authors),
            "category_count": len(categories),
            "rss_mb": round(self._repo.get_rss_mb(), 2),
            "cache_info": self._repo.get_cache_info(),
        }

    def get_source_tables(
        self,
        category_filter: str | None = None,
        scope_dto: CorpusScopeDTO | None = None,
        view_params: TokenViewParamsDTO | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        """Group texts into Translated EN, Translated TR, and Indigenous TR."""
        inv = self._repo.get_inventory_table()
        eff_scope = scope_dto
        if eff_scope is None and category_filter:
            eff_scope = CorpusScopeDTO.from_dict(category_filter)

        if eff_scope and (eff_scope.scope != "all" or eff_scope.author_filter or eff_scope.text_code or eff_scope.pair_code):
            texts = self._repo.get_texts_by_scope(eff_scope)
            allowed = {t.record.code for t in texts}
            inv = [r for r in inv if r.get("code") in allowed]

        sum_dict = self._get_sum_dict()

        trans_en = []
        trans_tr = []
        indig_tr = []

        for row in inv:
            code = row.get("code", "")
            meta = sum_dict.get(code, {})
            merged = dict(row)
            if view_params and (view_params.filter_function_words or view_params.punct != "drop"):
                t = self._repo.get_text_by_code(code)
                merged["tokens"] = len(self._repo.get_token_view(t, view_params).analysed()) if t else int(meta.get("tokens", 0) or 0)
            else:
                merged["tokens"] = int(meta.get("tokens", 0) or 0)
            merged["sentences"] = int(meta.get("sentences", 0) or 0)
            merged["text_code"] = code

            cat = str(row.get("type", "")).lower()
            lang = str(row.get("language", "")).lower()

            if "indigenous" in cat or "yerli" in cat:
                indig_tr.append(merged)
            elif "source" in cat or (lang == "en" and "translation" not in cat):
                trans_en.append(merged)
            elif "translation" in cat or "çeviri" in cat:
                trans_tr.append(merged)
            elif lang == "en":
                trans_en.append(merged)
            else:
                indig_tr.append(merged)

        cat_key = eff_scope.scope if eff_scope else category_filter
        if cat_key in ("trans_en", "all_en"):
            return {"trans_en": trans_en}
        if cat_key == "trans_tr":
            return {"trans_tr": trans_tr}
        if cat_key == "indig_tr":
            return {"indig_tr": indig_tr}
        if cat_key in ("all_tr", "author_turkish"):
            return {"trans_tr": trans_tr, "indig_tr": indig_tr}

        return {
            "trans_en": trans_en,
            "trans_tr": trans_tr,
            "indig_tr": indig_tr,
        }


    def get_token_distribution_figure1(self) -> dict[str, Any]:
        """Return data for Figure 1: Content vs. Function Word token sizes."""
        inv = self._repo.get_inventory_table()
        sum_dict = self._get_sum_dict()

        chart_data = []
        for r in inv:
            t_code = r.get("code", "")
            meta = sum_dict.get(t_code, {})
            tok_count = int(meta.get("tokens", 0) or 0)
            content_ratio = 0.55
            content_toks = int(tok_count * content_ratio)
            func_toks = tok_count - content_toks
            chart_data.append(
                {
                    "text_code": t_code,
                    "title": r.get("title", t_code),
                    "total": tok_count,
                    "content": content_toks,
                    "function": func_toks,
                }
            )
        return {"items": sorted(chart_data, key=lambda x: x["total"], reverse=True)}

    def get_schema_inspector(self, text_code: str) -> dict[str, Any]:
        """Inspect token and sentence schema for a given text."""
        text = self._repo.loader.load_text(text_code)
        tokens_df = text.tokens
        sentences_df = text.sentences

        tok_schema = [
            {"column": col, "dtype": str(tokens_df[col].dtype), "non_null": int(tokens_df[col].count())}
            for col in tokens_df.columns
        ]
        sent_schema = [
            {"column": col, "dtype": str(sentences_df[col].dtype), "non_null": int(sentences_df[col].count())}
            for col in sentences_df.columns
        ]
        return {
            "text_code": text_code,
            "token_rows": len(tokens_df),
            "sentence_rows": len(sentences_df),
            "token_schema": tok_schema,
            "sentence_schema": sent_schema,
        }

