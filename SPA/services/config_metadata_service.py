"""Service for configuration validation and statistical formula registry."""

from __future__ import annotations

from typing import Any

from SPA.models.config_dto import AuthorMetadataDTO, BookMetadataDTO, PathConfigDTO
from SPA.repositories.config_repository import ConfigRepository


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

    def get_formula_registry(self) -> dict[str, Any]:
        """Return the mathematical formula registry for help_docs_drawer.js."""
        return {
            "diversity": [
                {
                    "name": "Type-Token Ratio (TTR)",
                    "formula": r"\text{TTR} = \frac{V}{N}",
                    "description": "Ratio of vocabulary types V to total tokens N.",
                    "nan_guard": "N > 0, returns NaN if N=0.",
                    "citation": "Templin (1957)",
                },
                {
                    "name": "Root TTR (RTTR / Guiraud's R)",
                    "formula": r"\text{RTTR} = \frac{V}{\sqrt{N}}",
                    "description": "Mitigates sample-size dependence of raw TTR.",
                    "nan_guard": "N > 0.",
                    "citation": "Guiraud (1954)",
                },
                {
                    "name": "Yule's Characteristic K",
                    "formula": r"K = 10^4 \times \frac{\sum m^2 V_m - N}{N^2}",
                    "description": "Measures repeat rate of vocabulary, independent of text length.",
                    "nan_guard": "N > 0.",
                    "citation": "Yule (1944)",
                },
                {
                    "name": "Moving-Average TTR (MATTR)",
                    "formula": r"\text{MATTR}_W = \frac{1}{N - W + 1} \sum_{i=1}^{N - W + 1} \text{TTR}(w_i \dots w_{i+W-1})",
                    "description": "Calculates smooth sliding-window TTR over fixed window W (default 500).",
                    "nan_guard": "N >= W.",
                    "citation": "Covington & McFall (2010)",
                },
            ],
            "collocation": [
                {
                    "name": "Log-Dice",
                    "formula": r"\text{LogDice} = 14 + \log_2 \frac{2 \times O_{11}}{R_1 + C_1}",
                    "description": "Normalized scale where 14 is theoretical maximum co-occurrence.",
                    "nan_guard": "O11 > 0 and (R1 + C1) > 0.",
                    "citation": "Rychlý (2008)",
                },
                {
                    "name": "Pointwise Mutual Information (MI)",
                    "formula": r"\text{MI} = \log_2 \frac{O_{11}}{E_{11}}",
                    "description": "Ratio of observed co-occurrence to expected by chance.",
                    "nan_guard": "O11 > 0 and E11 > 0.",
                    "citation": "Church & Hanks (1990)",
                },
                {
                    "name": "Signed Log-Likelihood (G2)",
                    "formula": r"G^2 = 2 \sum_{i,j} O_{ij} \ln \frac{O_{ij}}{E_{ij}}",
                    "description": "Dunning's log-likelihood ratio with directional sign.",
                    "nan_guard": "O_ij > 0.",
                    "citation": "Dunning (1993)",
                },
            ],
            "dispersion": [
                {
                    "name": "Juilland's D",
                    "formula": r"D = 1 - \frac{s / \bar{x}}{\sqrt{n - 1}}",
                    "description": "Dispersion across n equal parts (n=10), bounded in [0, 1].",
                    "nan_guard": "x_bar > 0 and n > 1.",
                    "citation": "Juilland & Chang-Rodríguez (1964)",
                }
            ],
        }
