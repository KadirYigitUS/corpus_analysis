"""Configuration Data Transfer Objects (DTOs) for Corpus Analysis SPA."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PathConfigDTO:
    """Strongly-typed DTO for system and storage paths."""

    thesis_root: str
    translation_tsv: str
    indigenous_tsv: str
    aligned_root: str
    indigenous_root: str
    nda_cache_dir: str
    passim_output_dir: str
    data_root: str
    reports_dir: str
    tables_dir: str
    figures_dir: str
    cache_dir: str
    book_images_dir: str
    author_images_dir: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PathConfigDTO:
        paths = data.get("paths", {})
        return cls(
            thesis_root=paths.get("thesis_root", ""),
            translation_tsv=paths.get("translation_tsv", ""),
            indigenous_tsv=paths.get("indigenous_tsv", ""),
            aligned_root=paths.get("aligned_root", ""),
            indigenous_root=paths.get("indigenous_root", ""),
            nda_cache_dir=paths.get("nda_cache_dir", ""),
            passim_output_dir=paths.get("passim_output_dir", ""),
            data_root=paths.get("data_root", ""),
            reports_dir=paths.get("reports_dir", ""),
            tables_dir=paths.get("tables_dir", ""),
            figures_dir=paths.get("figures_dir", ""),
            cache_dir=paths.get("cache_dir", ""),
            book_images_dir=paths.get("book_images_dir", ""),
            author_images_dir=paths.get("author_images_dir", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "paths": {
                "thesis_root": self.thesis_root,
                "translation_tsv": self.translation_tsv,
                "indigenous_tsv": self.indigenous_tsv,
                "aligned_root": self.aligned_root,
                "indigenous_root": self.indigenous_root,
                "nda_cache_dir": self.nda_cache_dir,
                "passim_output_dir": self.passim_output_dir,
                "data_root": self.data_root,
                "reports_dir": self.reports_dir,
                "tables_dir": self.tables_dir,
                "figures_dir": self.figures_dir,
                "cache_dir": self.cache_dir,
                "book_images_dir": self.book_images_dir,
                "author_images_dir": self.author_images_dir,
            }
        }


@dataclass(frozen=True)
class BookMetadataDTO:
    """DTO representing verified bibliographic metadata and image path for a book."""

    code: str
    title: str
    author: str
    year: int
    language: str
    category: str
    source_title: str | None = None
    translator: str | None = None
    publisher: str | None = None
    pair_code: str | None = None
    cover_image: str | None = None
    description: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BookMetadataDTO:
        return cls(
            code=data["code"],
            title=data.get("title", ""),
            author=data.get("author", ""),
            year=int(data.get("year", 0)),
            language=data.get("language", "tr"),
            category=data.get("category", "indigenous"),
            source_title=data.get("source_title"),
            translator=data.get("translator"),
            publisher=data.get("publisher"),
            pair_code=data.get("pair_code"),
            cover_image=data.get("cover_image"),
            description=data.get("description"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass(frozen=True)
class AuthorMetadataDTO:
    """DTO representing author/translator profile and portrait image."""

    code: str
    name: str
    role: str
    era: str
    portrait_image: str | None = None
    translated_books: list[str] = field(default_factory=list)
    authored_books: list[str] = field(default_factory=list)
    biography: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuthorMetadataDTO:
        return cls(
            code=data["code"],
            name=data.get("name", ""),
            role=data.get("role", "Author-Translator"),
            era=data.get("era", "First Generation (1974-2000)"),
            portrait_image=data.get("portrait_image"),
            translated_books=list(data.get("translated_books", [])),
            authored_books=list(data.get("authored_books", [])),
            biography=data.get("biography"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}
