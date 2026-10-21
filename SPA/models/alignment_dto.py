"""Alignment and Length Delta Data Transfer Objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AlignmentFilterDTO:
    """Filter parameters for translation alignment tables."""

    pair_code: str
    chapter_no: int | None = None
    row_type: str | None = None  # 'one_to_one', 'one_to_many', etc.
    ner_category: str | None = None
    min_delta: int | None = None
    search_query: str = ""
    sort_by: str = "ai"  # 'ai' | 'sent_diff' | 'len_diff' | 'delta_w' | 'delta_c' | 'ratio_w'
    ascending: bool = True
    page: int = 1
    page_size: int = 25

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AlignmentFilterDTO:
        return cls(
            pair_code=str(data.get("pair_code", "")),
            chapter_no=(
                int(data["chapter_no"])
                if data.get("chapter_no") not in (None, "", "all")
                else None
            ),
            row_type=data.get("row_type") or None,
            ner_category=data.get("ner_category") or None,
            min_delta=(
                int(data["min_delta"])
                if data.get("min_delta") not in (None, "")
                else None
            ),
            search_query=str(data.get("search_query", "") or "").strip(),
            sort_by=str(data.get("sort_by", "ai")),
            ascending=bool(data.get("ascending", True)),
            page=max(1, int(data.get("page", 1))),
            page_size=min(200, max(10, int(data.get("page_size", 25)))),
        )


@dataclass(frozen=True)
class AlignmentRowDTO:
    """DTO for a single aligned sentence row."""

    alignment_idx: int
    chapter_no: int
    eng_text: str
    tur_text: str
    sent_eng: int = 1
    sent_tur: int = 1
    sent_diff: int = 0
    len_diff: int = 0
    eng_tokens: list[str] = field(default_factory=list)
    tur_tokens: list[str] = field(default_factory=list)
    delta_words: int = 0
    delta_chars: int = 0
    ratio_words: float = 1.0
    alignment_type: str = "1:1"
    ner_tags_eng: list[str] = field(default_factory=list)
    ner_tags_tur: list[str] = field(default_factory=list)
    ann_eng: list[list[dict[str, Any]]] = field(default_factory=list)
    ann_tur: list[list[dict[str, Any]]] = field(default_factory=list)
    eng_sents: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ai": self.alignment_idx,
            "ch": self.chapter_no,
            "eng": self.eng_text,
            "tur": self.tur_text,
            "sent_eng": self.sent_eng,
            "sent_tur": self.sent_tur,
            "sent_diff": self.sent_diff,
            "len_diff": self.len_diff,
            "eng_tok_count": len(self.eng_tokens),
            "tur_tok_count": len(self.tur_tokens),
            "delta_w": self.delta_words,
            "delta_c": self.delta_chars,
            "ratio_w": round(self.ratio_words, 3),
            "type": self.alignment_type,
            "ner_en": self.ner_tags_eng,
            "ner_tr": self.ner_tags_tur,
            "ann_eng": self.ann_eng,
            "ann_tur": self.ann_tur,
            "eng_sents": self.eng_sents,
        }

