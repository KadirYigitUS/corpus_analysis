"""Service for sublinear TF-IDF keyness and keyword extraction."""

from __future__ import annotations

from typing import Any

from corpus_toolkit.tfidf import TfidfAnalyzer
from SPA.models.stats_dto import TfidfParamsDTO
from SPA.models.view_params_dto import CorpusScopeDTO, TokenViewParamsDTO
from SPA.repositories.corpus_repository import CorpusRepository


class TfidfService:
    """Manages Tab 10 sublinear TF-IDF calculations and keyword profiles."""

    def __init__(self, corpus_repo: CorpusRepository) -> None:
        self._repo = corpus_repo
        self._analyzer = TfidfAnalyzer()

    def get_top_keywords_per_text(
        self,
        tfidf_params: TfidfParamsDTO,
        view_params: TokenViewParamsDTO,
        scope_dto: CorpusScopeDTO,
    ) -> dict[str, Any]:
        """Compute top-K TF-IDF keywords for each text in the given scope."""
        texts = self._repo.get_texts_by_scope(scope_dto)
        if not texts:
            return {"error": "No texts found for given scope"}

        exclude_pos = set(tfidf_params.exclude_pos) if tfidf_params.exclude_pos else None

        result = self._analyzer.fit(
            texts=texts,
            field=view_params.field,  # type: ignore[arg-type]
            n_chunks=tfidf_params.n_chunks or 1,
            filter_function_words=view_params.filter_function_words,
            mode=view_params.mode,  # type: ignore[arg-type]
            punct=view_params.punct,  # type: ignore[arg-type]
            exclude_pos=exclude_pos,
        )

        texts_keywords: dict[str, list[dict[str, Any]]] = {}
        for doc_id, _doc_label in zip(result.doc_ids, result.doc_labels):
            top_df = result.top_terms(doc_id, n=tfidf_params.top_k)
            terms_list = []
            for _, r in top_df.iterrows():
                terms_list.append({
                    "term": str(r["term"]),
                    "tfidf": round(float(r["tfidf"]), 4),
                })
            texts_keywords[doc_id] = terms_list

        return {
            "vocabulary_size": len(result.vocabulary),
            "doc_ids": result.doc_ids,
            "top_k": tfidf_params.top_k,
            "exclude_pos": list(exclude_pos or []),
            "texts_keywords": texts_keywords,
        }

    def get_dense_matrix(
        self,
        tfidf_params: TfidfParamsDTO,
        view_params: TokenViewParamsDTO,
        scope_dto: CorpusScopeDTO,
        n_per_doc: int = 8,
    ) -> dict[str, Any]:
        """Produce dense doc x term matrix for comparative heatmap display."""
        texts = self._repo.get_texts_by_scope(scope_dto)
        exclude_pos = set(tfidf_params.exclude_pos) if tfidf_params.exclude_pos else None

        result = self._analyzer.fit(
            texts=texts,
            field=view_params.field,  # type: ignore[arg-type]
            filter_function_words=view_params.filter_function_words,
            mode=view_params.mode,  # type: ignore[arg-type]
            punct=view_params.punct,  # type: ignore[arg-type]
            exclude_pos=exclude_pos,
        )

        dense_df = result.dense_top(n_per_doc=n_per_doc)
        return {
            "documents": list(dense_df.index),
            "terms": list(dense_df.columns),
            "matrix": dense_df.values.round(4).tolist(),
        }
