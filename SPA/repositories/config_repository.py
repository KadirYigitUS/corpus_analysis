"""Config repository for reading, writing, and validating YAML and image assets."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

import yaml

from SPA.models.config_dto import AuthorMetadataDTO, BookMetadataDTO, PathConfigDTO


class ConfigRepository:
    """Handles persistence and retrieval for config YAMLs and uploaded assets."""

    def __init__(self, config_dir: str | None = None) -> None:
        if config_dir is None:
            base_dir = Path(__file__).resolve().parent.parent
            self._config_dir = base_dir / "config"
        else:
            self._config_dir = Path(config_dir)
        self._paths_file = self._config_dir / "spa_paths.yaml"
        self._metadata_file = self._config_dir / "corpus_metadata.yaml"

    def get_paths(self) -> PathConfigDTO:
        """Read and parse spa_paths.yaml into PathConfigDTO."""
        if not self._paths_file.exists():
            return PathConfigDTO.from_dict({})
        with open(self._paths_file, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return PathConfigDTO.from_dict(data)

    def save_paths(self, config_dto: PathConfigDTO) -> None:
        """Atomically persist PathConfigDTO to spa_paths.yaml."""
        data = config_dto.to_dict()
        self._atomic_write_yaml(self._paths_file, data)

    def get_corpus_metadata(self) -> dict[str, Any]:
        """Read raw corpus_metadata.yaml dictionary."""
        if not self._metadata_file.exists():
            return {"books": [], "authors": []}
        with open(self._metadata_file, encoding="utf-8") as f:
            return yaml.safe_load(f) or {"books": [], "authors": []}

    def save_corpus_metadata(self, metadata: dict[str, Any]) -> None:
        """Atomically persist metadata dictionary to corpus_metadata.yaml."""
        self._atomic_write_yaml(self._metadata_file, metadata)

    def update_book_metadata(self, book_dto: BookMetadataDTO) -> None:
        """Update or insert a book record in corpus_metadata.yaml."""
        meta = self.get_corpus_metadata()
        books = meta.get("books", [])
        updated = False
        for i, b in enumerate(books):
            if b.get("code") == book_dto.code:
                books[i] = book_dto.to_dict()
                updated = True
                break
        if not updated:
            books.append(book_dto.to_dict())
        meta["books"] = books
        self.save_corpus_metadata(meta)

    def update_author_metadata(self, author_dto: AuthorMetadataDTO) -> None:
        """Update or insert an author record in corpus_metadata.yaml."""
        meta = self.get_corpus_metadata()
        authors = meta.get("authors", [])
        updated = False
        for i, a in enumerate(authors):
            if a.get("code") == author_dto.code:
                authors[i] = author_dto.to_dict()
                updated = True
                break
        if not updated:
            authors.append(author_dto.to_dict())
        meta["authors"] = authors
        self.save_corpus_metadata(meta)

    def save_uploaded_image(
        self,
        category: str,
        filename: str,
        content_bytes: bytes,
    ) -> str:
        """Save uploaded image to the appropriate image folder and return relative path."""
        paths = self.get_paths()
        target_dir = Path(
            paths.book_images_dir
            if category == "book"
            else paths.author_images_dir
        )
        if not target_dir.is_absolute():
            target_dir = (self._config_dir / target_dir).resolve()
        target_dir.mkdir(parents=True, exist_ok=True)

        target_file = target_dir / filename
        with open(target_file, "wb") as f:
            f.write(content_bytes)

        return f"/static/img/{'books' if category == 'book' else 'authors'}/{filename}"

    def validate_path_exists(self, path_str: str) -> bool:
        """Check if a path string exists on disk."""
        if not path_str:
            return False
        return Path(path_str).exists()

    def _atomic_write_yaml(
        self, target_path: Path, data: dict[str, Any]
    ) -> None:
        """Atomic write pattern: write to tmp file in same dir, then rename."""
        target_path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_file = tempfile.mkstemp(
            dir=str(target_path.parent), prefix="tmp_cfg_"
        )
        try:
            with open(fd, "w", encoding="utf-8") as f:
                yaml.dump(
                    data,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )
            os.replace(temp_file, target_path)
        except Exception:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            raise
