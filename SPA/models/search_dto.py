"""Search and Concordance Data Transfer Objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SearchQueryDTO:
    """Strongly-typed DTO for concordance search queries."""

    query: str
    match_mode: str = "exact"  # 'exact' | 'glob' | 'regex'
    case_sensitive: bool = False
    window_left: int = 5
    window_right: int = 5
    pos_filter: str | None = None
    collocate: str | None = None
    collocate_span: tuple[int, int] | None = None
    sentence_clamped: bool = False
    max_hits: int = 500

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SearchQueryDTO:
        span_raw = data.get("collocate_span")
        span = None
        if (
            isinstance(span_raw, (list, tuple))
            and len(span_raw) == 2
        ):
            span = (int(span_raw[0]), int(span_raw[1]))
        return cls(
            query=str(data.get("query", "")),
            match_mode=str(data.get("match_mode", "exact")),
            case_sensitive=bool(data.get("case_sensitive", False)),
            window_left=int(data.get("window_left", 5)),
            window_right=int(data.get("window_right", 5)),
            pos_filter=data.get("pos_filter"),
            collocate=data.get("collocate"),
            collocate_span=span,
            sentence_clamped=bool(data.get("sentence_clamped", False)),
            max_hits=int(data.get("max_hits", 500)),
        )


@dataclass(frozen=True)
class KwicSpanDTO:
    """DTO for a single KWIC hit with Left, Node, Right, and coordinates."""

    hit_id: int
    text_code: str
    left_context: str
    node: str
    right_context: str
    chapter_no: int
    paragraph_no: int
    sentence_no: int
    token_index: int
    pos_tag: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "hit_id": self.hit_id,
            "text_code": self.text_code,
            "left": self.left_context,
            "node": self.node,
            "right": self.right_context,
            "coords": f"{self.text_code}:{self.chapter_no}:{self.paragraph_no}:{self.sentence_no}",
            "token_index": self.token_index,
            "pos": self.pos_tag or "",
        }


@dataclass(frozen=True)
class BatchSearchQueryDTO:
    """DTO for batch KWIC queries across multiple terms."""

    terms: list[str]
    match_mode: str = "exact"
    case_sensitive: bool = False
    scope: str = "all"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BatchSearchQueryDTO:
        return cls(
            terms=[
                str(t).strip()
                for t in data.get("terms", [])
                if str(t).strip()
            ],
            match_mode=str(data.get("match_mode", "exact")),
            case_sensitive=bool(data.get("case_sensitive", False)),
            scope=str(data.get("scope", "all")),
        )
