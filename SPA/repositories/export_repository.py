"""Export repository for generating tables, figures, and research ZIP bundles."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pandas as pd

from SPA.models.config_dto import PathConfigDTO
from SPA.models.stats_dto import ExportBundleDTO


class ExportRepository:
    """Handles file saving for research reports, figures, tables, and ZIP bundles."""

    def __init__(self, path_config: PathConfigDTO) -> None:
        self._paths = path_config
        self._reports_dir = Path(path_config.reports_dir)
        self._tables_dir = Path(path_config.tables_dir)
        self._figures_dir = Path(path_config.figures_dir)
        for d in (self._reports_dir, self._tables_dir, self._figures_dir):
            if not d.is_absolute():
                d = (Path(path_config.thesis_root) / d).resolve()
            d.mkdir(parents=True, exist_ok=True)

    def save_markdown_report(self, filename: str, content: str) -> Path:
        """Write markdown report content to disk."""
        target = self._reports_dir / filename
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        return target

    def save_dataframe_tsv(self, filename: str, df: pd.DataFrame) -> Path:
        """Export pandas DataFrame to TSV file."""
        target = self._tables_dir / filename
        df.to_csv(target, sep="\t", index=False)
        return target

    def save_multi_sheet_excel(
        self, filename: str, sheets: dict[str, pd.DataFrame]
    ) -> Path:
        """Export multiple DataFrames into a formatted multi-sheet Excel file."""
        target = self._tables_dir / filename
        with pd.ExcelWriter(target, engine="openpyxl") as writer:
            for sheet_name, df in sheets.items():
                safe_name = sheet_name[:31].replace(":", "_").replace("/", "_")
                df.to_excel(writer, sheet_name=safe_name, index=False)
        return target

    def create_zip_bundle(
        self,
        bundle_dto: ExportBundleDTO,
        text_files: dict[str, str],
        dataframes: dict[str, pd.DataFrame],
    ) -> bytes:
        """Create an in-memory ZIP bundle of selected reports, TSVs, and Excel workbooks."""
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(
            zip_buffer, "w", zipfile.ZIP_DEFLATED
        ) as zip_file:
            # 1. Text / Markdown files
            if "md" in bundle_dto.export_formats:
                for fname, text in text_files.items():
                    zip_file.writestr(f"reports/{fname}", text)

            # 2. TSV files
            if "tsv" in bundle_dto.export_formats:
                for fname, df in dataframes.items():
                    tsv_data = df.to_csv(sep="\t", index=False)
                    zip_file.writestr(f"tables/{fname}.tsv", tsv_data)

            # 3. Combined Excel workbook
            if "xlsx" in bundle_dto.export_formats and dataframes:
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(
                    excel_buffer, engine="openpyxl"
                ) as writer:
                    for name, df in dataframes.items():
                        safe = name[:31].replace(":", "_").replace("/", "_")
                        df.to_excel(writer, sheet_name=safe, index=False)
                zip_file.writestr(
                    f"tables/{bundle_dto.bundle_name}.xlsx",
                    excel_buffer.getvalue(),
                )

        zip_buffer.seek(0)
        return zip_buffer.getvalue()
