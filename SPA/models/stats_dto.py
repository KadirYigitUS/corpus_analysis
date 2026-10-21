"""Statistical and Export Parameters DTOs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CollocationParamsDTO:
    """Parameters for collocation analysis and GraphColl network."""

    node_query: str
    left_span: int = 5
    right_span: int = 5
    min_freq: int = 3
    stat_metric: str = "LogDice"  # LogDice, MI, MI2, MI3, T, G2
    sentence_clamped: bool = True
    scope: str = "all"
    text_code: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CollocationParamsDTO:
        return cls(
            node_query=str(data.get("node_query", "")),
            left_span=int(data.get("left_span", 5)),
            right_span=int(data.get("right_span", 5)),
            min_freq=max(1, int(data.get("min_freq", 3))),
            stat_metric=str(data.get("stat_metric", "LogDice")),
            sentence_clamped=bool(data.get("sentence_clamped", True)),
            scope=str(data.get("scope", "all")),
            text_code=data.get("text_code"),
        )


@dataclass(frozen=True)
class DiversityParamsDTO:
    """Parameters for lexical diversity calculation."""

    window_size: int = 500  # for MATTR / STTR
    mtld_ttr_threshold: float = 0.72
    hdd_sample_size: int = 42

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DiversityParamsDTO:
        return cls(
            window_size=max(50, int(data.get("window_size", 500))),
            mtld_ttr_threshold=float(data.get("mtld_ttr_threshold", 0.72)),
            hdd_sample_size=max(10, int(data.get("hdd_sample_size", 42))),
        )


@dataclass(frozen=True)
class TfidfParamsDTO:
    """Parameters for sublinear TF-IDF keyword extraction."""

    top_k: int = 15
    exclude_pos: list[str] = field(default_factory=lambda: ["PROPN"])
    sublinear_tf: bool = True
    smooth_idf: bool = True
    n_chunks: int | None = None
    language: str = "tr"  # 'tr' | 'en'

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TfidfParamsDTO:
        return cls(
            top_k=max(5, min(100, int(data.get("top_k", 15)))),
            exclude_pos=list(data.get("exclude_pos", ["PROPN"])),
            sublinear_tf=bool(data.get("sublinear_tf", True)),
            smooth_idf=bool(data.get("smooth_idf", True)),
            n_chunks=(
                int(data["n_chunks"])
                if data.get("n_chunks") is not None
                else None
            ),
            language=str(data.get("language", "tr")),
        )


@dataclass(frozen=True)
class ExportBundleDTO:
    """Parameters for bundling and downloading research outputs."""

    export_formats: list[str] = field(
        default_factory=lambda: ["md", "tsv", "xlsx"]
    )
    include_figures: bool = True
    include_tables: bool = True
    author_filter: str | None = None
    bundle_name: str = "corpus_analysis_export"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExportBundleDTO:
        return cls(
            export_formats=list(
                data.get("export_formats", ["md", "tsv", "xlsx"])
            ),
            include_figures=bool(data.get("include_figures", True)),
            include_tables=bool(data.get("include_tables", True)),
            author_filter=data.get("author_filter"),
            bundle_name=str(
                data.get("bundle_name", "corpus_analysis_export")
            ),
        )
