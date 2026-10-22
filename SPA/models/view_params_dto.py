"""View parameters and scope DTOs for the 32-combination matrix."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TokenViewParamsDTO:
    """Strongly-typed DTO for TokenView 32-combination matrix."""

    field: str = "tok"  # 'tok' | 'lem'
    filter_function_words: bool = False  # False: all, True: content only
    mode: str = "drop"  # 'drop' | 'mask'
    punct: str = "drop"  # 'drop' | 'keep' | 'strip' | 'split'

    def __post_init__(self) -> None:
        if self.field not in ("tok", "lem"):
            raise ValueError(f"Invalid field: {self.field}")
        if self.mode not in ("drop", "mask"):
            raise ValueError(f"Invalid mode: {self.mode}")
        if self.punct not in ("drop", "keep", "strip", "split"):
            raise ValueError(f"Invalid punct: {self.punct}")

    @classmethod
    def from_dict(cls, data: Any) -> TokenViewParamsDTO:
        if not isinstance(data, dict):
            return cls()
        return cls(
            field=str(data.get("field", "tok")),
            filter_function_words=bool(
                data.get("filter_function_words", False)
            ),
            mode=str(data.get("mode", "drop")),
            punct=str(data.get("punct", "drop")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "field": self.field,
            "filter_function_words": self.filter_function_words,
            "mode": self.mode,
            "punct": self.punct,
        }

    def cache_key(self) -> tuple[str, bool, str, str]:
        return (self.field, self.filter_function_words, self.mode, self.punct)


@dataclass(frozen=True)
class CorpusScopeDTO:
    """Strongly-typed DTO for the 8 corpus scopes."""

    scope: str = "all"
    author_filter: str | None = None
    text_code: str | None = None
    pair_code: str | None = None

    ALLOWED_SCOPES = (
        "all",
        "all_en",
        "all_tr",
        "trans_en",
        "trans_tr",
        "indig_tr",
        "author_related",
        "author_turkish",
        "pairs",
        "single",
    )

    def __post_init__(self) -> None:
        if self.scope not in self.ALLOWED_SCOPES:
            raise ValueError(f"Invalid scope: {self.scope}")

    @property
    def category(self) -> str:
        return self.scope

    @classmethod
    def from_dict(cls, data: Any) -> CorpusScopeDTO:
        if isinstance(data, str):
            return cls(scope=data)
        if not isinstance(data, dict):
            return cls(scope="all")
        scope_val = data.get("scope", data.get("category", "all"))
        if isinstance(scope_val, dict):
            return cls.from_dict(scope_val)
        return cls(
            scope=str(scope_val),
            author_filter=data.get("author_filter"),
            text_code=data.get("text_code"),
            pair_code=data.get("pair_code"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}

    def cache_key(self) -> tuple[str, str | None, str | None, str | None]:
        return (self.scope, self.author_filter, self.pair_code, self.text_code)


