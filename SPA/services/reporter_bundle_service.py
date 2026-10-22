"""Service for generating research reports, ZIP bundles, and explorer console snippets."""

from __future__ import annotations

from typing import Any

import pandas as pd

from corpus_toolkit.kwic import Concordancer
from corpus_toolkit.search import CorpusSearchEngine, SearchQuery
from SPA.models.stats_dto import ExportBundleDTO
from SPA.models.view_params_dto import CorpusScopeDTO, TokenViewParamsDTO
from SPA.repositories.corpus_repository import CorpusRepository
from SPA.repositories.export_repository import ExportRepository


class ReporterBundleService:
    """Manages research report packaging, research bundles, and scriptable console snippets."""

    def __init__(
        self,
        corpus_repo: CorpusRepository,
        export_repo: ExportRepository,
    ) -> None:
        self._repo = corpus_repo
        self._corpus_repo = corpus_repo
        self._export_repo = export_repo

    def execute_quick_search(
        self,
        term: str,
        view_params: TokenViewParamsDTO,
        scope_dto: CorpusScopeDTO | None = None,
        max_concordance: int = 5,
    ) -> dict[str, Any]:
        """Execute quick_search / scoped concordance and return structured summary and samples."""
        sc = scope_dto or CorpusScopeDTO(scope="all")
        texts = self._corpus_repo.get_texts_by_scope(sc)
        if not texts:
            texts = list(self._corpus_repo.loader.load_all())

        terms = [t.strip() for t in term.split(",") if t.strip()] or [term]
        q = SearchQuery(
            terms,
            field=view_params.field,  # type: ignore[arg-type]
            match="exact",
            filter_function_words=view_params.filter_function_words,
            mode=view_params.mode,  # type: ignore[arg-type]
            punct=view_params.punct,  # type: ignore[arg-type]
        )
        search_res = CorpusSearchEngine().search(q, texts)
        conc = Concordancer().run(search_res, texts, span="collocation")

        samples = []
        for line in getattr(conc, "lines", [])[:max_concordance]:
            samples.append({
                "text": line.code,
                "coords": getattr(line, "coordinate", f"tok {line.ti}"),
                "line": f"{line.left_text()} [{line.node[0]}] {line.right_text()}",
            })

        presence = sorted({line.code for line in getattr(conc, "lines", [])})
        cat_map = {
            "all": "All texts",
            "all_en": "All English texts",
            "trans_en": "All English texts",
            "all_tr": "All Turkish texts",
            "indig_tr": "Indigenous Turkish novels",
            "author_related": "Author-translator related texts",
            "author_turkish": "Author-translator Turkish texts",
        }
        cat_label = cat_map.get(sc.scope, "All texts")
        author_arg = f", author='{sc.author_filter}'" if sc.author_filter else ""

        return {
            "term": term,
            "scope": sc.to_dict(),
            "view_params": view_params.to_dict(),
            "total_hits": len(search_res.hits),
            "presence": presence,
            "samples": samples,
            "python_snippet": (
                f"from corpus_toolkit.loader import CorpusLoader\n"
                f"from corpus_toolkit.explorer import quick_search\n\n"
                f"loader = CorpusLoader()\n"
                f"res = quick_search(\n"
                f"    loader, '{term}', category='{cat_label}'{author_arg},\n"
                f"    field='{view_params.field}', filter_function_words={view_params.filter_function_words},\n"
                f"    mode='{view_params.mode}', punct='{view_params.punct}'\n"
                f")\n"
                f"print(res)\n"
            ),
        }


    def generate_research_bundle(
        self,
        bundle_dto: ExportBundleDTO,
        summary_stats: dict[str, Any],
        active_tables: dict[str, list[dict[str, Any]]],
    ) -> bytes:
        """Produce an in-memory ZIP package containing formatted markdown reports and tabular files."""
        # 1. Generate Markdown Report
        md_lines = [
            f"# Corpus Analysis Research Report: {bundle_dto.bundle_name}",
            "",
            "## 1. Corpus Summary Statistics",
            f"- Total Texts: {summary_stats.get('total_texts', 0)}",
            f"- Total Tokens: {summary_stats.get('total_tokens', 0)}",
            f"- Total Sentences: {summary_stats.get('total_sentences', 0)}",
            f"- Resident Memory: {summary_stats.get('rss_mb', 0)} MB",
            "",
            "## 2. Included Analysis Tables",
        ]
        for tbl_name, rows in active_tables.items():
            md_lines.append(f"- **{tbl_name}**: {len(rows)} records")

        md_content = "\n".join(md_lines)
        text_files = {"README.md": md_content}

        # 2. Convert raw tables to pandas DataFrames
        dataframes: dict[str, pd.DataFrame] = {}
        for name, rows in active_tables.items():
            if rows:
                dataframes[name] = pd.DataFrame(rows)

        # 3. Create ZIP bundle via repository
        return self._export_repo.create_zip_bundle(
            bundle_dto=bundle_dto,
            text_files=text_files,
            dataframes=dataframes,
        )
