"""Service providing search frequency summary, view comparisons, and NLTK checks."""

from __future__ import annotations

from typing import Any

import pandas as pd

from corpus_toolkit import nltk_adapter, search
from SPA.models.view_params_dto import CorpusScopeDTO, TokenViewParamsDTO
from SPA.repositories.corpus_repository import CorpusRepository
from SPA.services.payload_cache import global_payload_cache
from SPA.services.payload_utils import df_to_table_payload


class SearchSummaryService:
    def __init__(self, corpus_repo: CorpusRepository | None = None) -> None:
        self._repo = corpus_repo or CorpusRepository()
        self.repo = self._repo

    def get_search_summary_and_bars(
        self,
        term: str,
        field: str = "lem",
        match: str = "exact",
        scope: CorpusScopeDTO | None = None,
        view_params: TokenViewParamsDTO | None = None,
    ) -> dict[str, Any]:
        sc = scope or CorpusScopeDTO(scope="all")
        vp = view_params or TokenViewParamsDTO(field=field)
        eff_field = vp.field if view_params else field
        cache_key = global_payload_cache.build_key(
            "conc:summary", scope=sc, view=vp, term=term, eff_field=eff_field, match=match
        )
        if cached := global_payload_cache.get(cache_key):
            return cached

        engine = search.CorpusSearchEngine()
        texts = self.repo.get_texts_by_scope(sc) or list(self.repo.loader.load_all())
        terms = [t.strip() for t in term.split(",") if t.strip()] or [term]
        q = search.SearchQuery(
            terms,
            field=eff_field,  # type: ignore[arg-type]
            match=match,  # type: ignore[arg-type]
            filter_function_words=vp.filter_function_words,
            mode=vp.mode,  # type: ignore[arg-type]
            punct=vp.punct,  # type: ignore[arg-type]
        )
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

        payload = {
            "table": df_to_table_payload(summary_df, title=f"'{term}' Arama Özeti"),
            "bars": bars_items,
            "total_hits": int(summary_df["hits"].sum()) if not summary_df.empty else 0,
        }
        global_payload_cache.put(cache_key, payload)
        return payload

    def get_views_comparison(
        self,
        term: str,
        match: str = "exact",
        scope: CorpusScopeDTO | None = None,
        view_params: TokenViewParamsDTO | None = None,
    ) -> dict[str, Any]:
        sc = scope or CorpusScopeDTO(scope="all_tr")
        vp = view_params or TokenViewParamsDTO(field="lem")
        cache_key = global_payload_cache.build_key(
            "conc:views", scope=sc, view=vp, term=term, match=match
        )
        if cached := global_payload_cache.get(cache_key):
            return cached

        engine = search.CorpusSearchEngine()
        texts = self.repo.get_texts_by_scope(sc) or list(self.repo.loader.load_all_turkish())
        terms = [t.strip() for t in term.split(",") if t.strip()] or [term]
        rows = []
        combos = [
            (vp.field, False, "drop", vp.punct, f"{vp.field} · Ham (False) · drop · {vp.punct}"),
            (vp.field, True, "drop", vp.punct, f"{vp.field} · İçerik (True) · drop · {vp.punct}"),
            (vp.field, True, "mask", vp.punct, f"{vp.field} · İçerik (True) · mask · {vp.punct}"),
            ("tok", vp.filter_function_words, vp.mode, "keep", f"tok · fw={vp.filter_function_words} · {vp.mode} · keep"),
            ("tok", vp.filter_function_words, vp.mode, "strip", f"tok · fw={vp.filter_function_words} · {vp.mode} · strip"),
            ("tok", vp.filter_function_words, vp.mode, "split", f"tok · fw={vp.filter_function_words} · {vp.mode} · split"),
        ]
        for fld, fw, mode, p_reg, label in combos:
            q = search.SearchQuery(
                terms, fld, match=match, filter_function_words=fw, mode=mode, punct=p_reg  # type: ignore[arg-type]
            )
            s = engine.search(q, texts).summary()
            total_hits = int(s["hits"].sum()) if not s.empty else 0
            running = int(s["running_words"].sum()) if not s.empty else 0
            per10k = 1e4 * total_hits / max(running, 1)
            rows.append({
                "view_config": label,
                "field": fld,
                "filter_function_words": "İçerik (True)" if fw else "Ham (False)",
                "mode": mode,
                "punct": p_reg,
                "total_hits": total_hits,
                "running_words": running,
                "per10k": round(per10k, 2),
            })
        payload = df_to_table_payload(pd.DataFrame(rows), title="Görünüm Karşılaştırması (Ham vs İçerik, Drop vs Mask, Noktalama)")
        global_payload_cache.put(cache_key, payload)
        return payload

    def get_nltk_concordance_and_similar(
        self,
        code: str,
        word: str,
        width: int = 70,
        lines: int = 6,
        view_params: TokenViewParamsDTO | None = None,
    ) -> dict[str, Any]:
        from corpus_toolkit import TokenView
        vp = view_params or TokenViewParamsDTO(field="tok", filter_function_words=False)
        text = self.repo.get_text_by_code(code) or self.repo.loader.load_text(code)
        try:
            v = TokenView(text, vp.field, vp.filter_function_words, vp.mode, punct=vp.punct)  # type: ignore[arg-type]
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

