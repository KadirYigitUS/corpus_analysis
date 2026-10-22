"""View parameters and scope DTOs for the 32-combination matrix."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


def _to_bool(val: Any, default: bool = False) -> bool:
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() in ("true", "1", "yes", "on")
    if val is None:
        return default
    return bool(val)


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
        if not isinstance(data, Mapping):
            return cls()
        fw_raw = data.get("filter_function_words", data.get("content_only", False))
        return cls(
            field=str(data.get("field") or "tok"),
            filter_function_words=_to_bool(fw_raw, default=False),
            mode=str(data.get("mode") or "drop"),
            punct=str(data.get("punct") or "drop"),
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
            return cls(scope=data or "all")
        if not isinstance(data, Mapping):
            return cls(scope="all")
        scope_val = data.get("scope") or data.get("category") or "all"
        if isinstance(scope_val, Mapping):
            return cls.from_dict(scope_val)
        af = data.get("author_filter") or None
        tc = data.get("text_code") or data.get("code") or None
        pc = data.get("pair_code") or None
        return cls(
            scope=str(scope_val),
            author_filter=str(af) if af else None,
            text_code=str(tc) if tc else None,
            pair_code=str(pc) if pc else None,
        )

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}

    def cache_key(self) -> tuple[str, str | None, str | None, str | None]:
        return (self.scope, self.author_filter, self.pair_code, self.text_code)


def parse_scope_and_view(
    args: Mapping[str, Any] | None = None,
    body: Mapping[str, Any] | None = None,
) -> tuple[CorpusScopeDTO, TokenViewParamsDTO]:
    """Uniformly parse CorpusScopeDTO and TokenViewParamsDTO from query args and/or JSON body."""
    merged: dict[str, Any] = {}
    if args:
        merged.update(dict(args))
    if body and isinstance(body, Mapping):
        merged.update(dict(body))

    scope_src = merged.get("scope")
    if isinstance(scope_src, Mapping):
        scope_dict = {**merged, **dict(scope_src)}
        scope_dict["scope"] = scope_src.get("scope") or scope_src.get("category") or "all"
    else:
        scope_dict = merged
    scope_dto = CorpusScopeDTO.from_dict(scope_dict)

    vp_src = merged.get("view_params")
    if isinstance(vp_src, Mapping):
        vp_dict = {**merged, **dict(vp_src)}
    else:
        vp_dict = merged
    view_dto = TokenViewParamsDTO.from_dict(vp_dict)
    return scope_dto, view_dto



