"""Service for corpus search, KWIC concordancing, and multi-view results."""

from __future__ import annotations

from typing import Any

from corpus_toolkit.kwic import Concordancer
from corpus_toolkit.search import CorpusSearchEngine, SearchQuery
from SPA.models.search_dto import SearchQueryDTO
from SPA.models.view_params_dto import CorpusScopeDTO, TokenViewParamsDTO
from SPA.repositories.corpus_repository import CorpusRepository


class SearchKwicService:
    """Manages Tab 6 search queries, KWIC concordance lines, and multi-key sorting."""

    def __init__(self, corpus_repo: CorpusRepository) -> None:
        self._repo = corpus_repo
        self._engine = CorpusSearchEngine()
        self._concordancer = Concordancer()

    def search_kwic(
        self,
        query_dto: SearchQueryDTO,
        view_params: TokenViewParamsDTO,
        scope_dto: CorpusScopeDTO,
        sort_by: str = "position",
    ) -> dict[str, Any]:
        """Execute search and return KWIC concordance lines with coordinate details."""
        texts = self._repo.get_texts_by_scope(scope_dto)
        terms = [t.strip() for t in query_dto.query.split(",") if t.strip()]
        if not terms:
            return {"total_hits": 0, "lines": []}

        search_query = SearchQuery(
            terms=terms,
            field=view_params.field,  # type: ignore[arg-type]
            match=query_dto.match_mode,  # type: ignore[arg-type]
            case_sensitive=query_dto.case_sensitive,
            pos={query_dto.pos_filter} if query_dto.pos_filter else None,
            collocate=[query_dto.collocate] if query_dto.collocate else None,
            collocate_span=query_dto.collocate_span or (5, 5),
            sentence_clamped=query_dto.sentence_clamped,
            filter_function_words=view_params.filter_function_words,
            mode=view_params.mode,  # type: ignore[arg-type]
            punct=view_params.punct,  # type: ignore[arg-type]
        )

        search_result = self._engine.search(search_query, texts, evict=False)
        if len(search_result) == 0:
            return {"total_hits": 0, "lines": []}

        span = (query_dto.window_left, query_dto.window_right)
        conc_res = self._concordancer.run(search_result, texts, span=span, evict=False)
        if sort_by != "position":
            try:
                conc_res = conc_res.sorted(by=sort_by)  # type: ignore[arg-type]
            except Exception:
                pass
        lines_df = conc_res.to_dataframe().head(query_dto.max_hits)

        formatted_lines: list[dict[str, Any]] = []
        for idx, row in lines_df.iterrows():
            formatted_lines.append(
                {
                    "hit_id": int(idx),
                    "text_code": str(row.get("text_code", "")),
                    "left": str(row.get("left", "")),
                    "node": str(row.get("node", "")),
                    "right": str(row.get("right", "")),
                    "coords": str(row.get("coords", "")),
                    "chapter": int(row.get("ch_no", 1)),
                    "paragraph": int(row.get("p_no", 1)),
                    "sentence": int(row.get("s_no", 1)),
                    "pos": str(row.get("pos", "")),
                }
            )

        return {
            "total_hits": len(search_result),
            "returned_hits": len(formatted_lines),
            "query": query_dto.query,
            "span": span,
            "lines": formatted_lines,
        }

    def compare_punctuation_regimes(
        self,
        query_dto: SearchQueryDTO,
        scope_dto: CorpusScopeDTO,
        view_params: TokenViewParamsDTO | None = None,
    ) -> dict[str, int]:
        """Run search across all 4 punctuation regimes (drop, keep, strip, split) to compare hit counts."""
        vp = view_params or TokenViewParamsDTO()
        texts = self._repo.get_texts_by_scope(scope_dto)
        terms = [t.strip() for t in query_dto.query.split(",") if t.strip()]
        counts: dict[str, int] = {}

        for p_mode in ("drop", "keep", "strip", "split"):
            sq = SearchQuery(
                terms=terms,
                field=vp.field,  # type: ignore[arg-type]
                match=query_dto.match_mode,  # type: ignore[arg-type]
                case_sensitive=query_dto.case_sensitive,
                filter_function_words=vp.filter_function_words,
                mode=vp.mode,  # type: ignore[arg-type]
                punct=p_mode,  # type: ignore[arg-type]
            )
            res = self._engine.search(sq, texts)
            counts[p_mode] = len(res.hits)

        return counts
