"""Service providing 13x17 UPOS heatmap matrix data."""

from typing import Any

from corpus_toolkit import pos
from SPA.models.view_params_dto import CorpusScopeDTO, TokenViewParamsDTO
from SPA.repositories.corpus_repository import CorpusRepository
from SPA.services.payload_cache import global_payload_cache


class PosMatrixService:
    def __init__(self, corpus_repo: CorpusRepository | None = None) -> None:
        self._repo = corpus_repo or CorpusRepository()
        self.repo = self._repo

    def get_upos_heatmap_matrix(
        self,
        content_only: bool = False,
        scope: CorpusScopeDTO | None = None,
        view: TokenViewParamsDTO | None = None,
    ) -> dict[str, Any]:
        eff_content = content_only or bool(view and view.filter_function_words)
        cache_key = global_payload_cache.build_key(
            "pos:heatmap", scope=scope, view=view, content_only=eff_content
        )
        cached = global_payload_cache.get(cache_key)
        if cached:
            return cached

        texts = self._repo.get_texts_by_scope(scope) if scope else list(self._repo.loader.load_all())
        P = pos.PosComparativeAnalyzer()
        profile_df = P.profile_table(texts, content_only=eff_content)

        rows = [f"{c} · {t[:24]}" for c, t in zip(profile_df["code"], profile_df["title"])] if not profile_df.empty else []
        cols = list(pos.UPOS_ORDER)
        matrix_vals = []

        for _, r in profile_df.iterrows():
            row_vals = []
            for upos_tag in cols:
                val = r[upos_tag] if upos_tag in r else 0.0
                row_vals.append(round(float(val), 1) if val is not None else 0.0)
            matrix_vals.append(row_vals)

        payload = {
            "title": "Part-of-Speech Profile per Text (UPOS %)",
            "rows": rows,
            "cols": cols,
            "values": matrix_vals,
            "fmt": ".0f",
            "scale": "seq",
            "content_only": eff_content,
        }
        global_payload_cache.put(cache_key, payload)
        return payload

