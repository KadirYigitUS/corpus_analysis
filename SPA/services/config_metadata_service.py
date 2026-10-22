"""Service for configuration validation and statistical formula registry."""

from __future__ import annotations

from typing import Any

from SPA.models.config_dto import AuthorMetadataDTO, BookMetadataDTO, PathConfigDTO
from SPA.repositories.config_repository import ConfigRepository
from SPA.services.help_catalog_data import get_help_catalog


class ConfigMetadataService:
    """Provides path validation, metadata management, and formula definitions."""

    def __init__(self, config_repo: ConfigRepository) -> None:
        self._repo = config_repo

    def get_paths(self) -> PathConfigDTO:
        return self._repo.get_paths()

    def update_paths(self, new_paths: PathConfigDTO) -> dict[str, Any]:
        """Validate paths and persist if valid."""
        results: dict[str, bool] = {}
        for field_name, path_val in new_paths.__dict__.items():
            results[field_name] = self._repo.validate_path_exists(path_val)
        self._repo.save_paths(new_paths)
        return {"saved": True, "validation": results}

    def get_books(self, author_code: str | None = None) -> list[dict[str, Any]]:
        meta = self._repo.get_corpus_metadata()
        books = meta.get("books", [])
        if author_code:
            books = [b for b in books if b.get("author") == author_code or b.get("translator") == author_code]
        return books

    def update_book(self, book_dto: BookMetadataDTO) -> None:
        self._repo.update_book_metadata(book_dto)

    def get_authors(self) -> list[dict[str, Any]]:
        meta = self._repo.get_corpus_metadata()
        return meta.get("authors", [])

    def update_author(self, author_dto: AuthorMetadataDTO) -> None:
        self._repo.update_author_metadata(author_dto)

    def upload_image(self, category: str, filename: str, content: bytes) -> str:
        if category not in ("book", "author"):
            raise ValueError(f"Invalid category: {category}")
        return self._repo.save_uploaded_image(category, filename, content)

    def get_formulas_catalog(self) -> dict[str, Any]:
        """Return the complete mathematical formula and pane catalog across all 11 tabs."""
        return get_help_catalog()

    def get_formula_registry(self) -> dict[str, Any]:
        """Return the mathematical formula registry for help_docs_drawer.js."""
        return self.get_formulas_catalog()
