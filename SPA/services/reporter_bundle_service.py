"""Service for generating research reports, ZIP bundles, and explorer console snippets."""

from __future__ import annotations

from typing import Any

import pandas as pd

from corpus_toolkit.explorer import quick_search
from SPA.models.stats_dto import ExportBundleDTO
from SPA.models.view_params_dto import TokenViewParamsDTO
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
        max_concordance: int = 5,
    ) -> dict[str, Any]:
        """Execute quick_search and return structured summary and concordance samples."""
        res = quick_search(
            loader=self._corpus_repo.loader,
            terms=term,
            field=view_params.field,  # type: ignore[arg-type]
            filter_function_words=view_params.filter_function_words,
            mode=view_params.mode,  # type: ignore[arg-type]
            punct=view_params.punct,  # type: ignore[arg-type]
            max_lines=max_concordance,
        )

        samples = []
        for line in getattr(res, "lines", [])[:max_concordance]:
            samples.append({
                "text": line.code,
                "coords": getattr(line, "coordinate", f"tok {line.ti}"),
                "line": f"{line.left_text()} [{line.node[0]}] {line.right_text()}",
            })

        presence = list({line.code for line in getattr(res, "lines", [])})

        return {
            "term": term,
            "total_hits": int(getattr(res, "total_hits", len(samples))),
            "presence": presence,
            "samples": samples,
            "python_snippet": (
                f"from corpus_toolkit.loader import CorpusLoader\n"
                f"from corpus_toolkit.explorer import quick_search\n\n"
                f"loader = CorpusLoader()\n"
                f"res = quick_search(loader, '{term}', field='{view_params.field}', "
                f"filter_function_words={view_params.filter_function_words}, punct='{view_params.punct}')\n"
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
