"""Shared pytest fixtures and deterministic assertion helpers for Corpus Analysis SPA."""

from __future__ import annotations

import math
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient

from SPA.app import create_app
from SPA.repositories.corpus_repository import CorpusRepository


@pytest.fixture(scope="session")
def app() -> Flask:
    """Create a session-scoped SPA Flask application instance."""
    application = create_app()
    application.config["TESTING"] = True
    return application


@pytest.fixture(scope="session")
def client(app: Flask) -> FlaskClient:
    """Return a session-scoped Flask test client."""
    with app.test_client() as test_client:
        yield test_client


@pytest.fixture(scope="session")
def corpus_repo(app: Flask) -> CorpusRepository:
    """Return the singleton CorpusRepository registered on app.extensions."""
    return app.extensions["corpus_repo"]


def assert_table_payload(
    payload: dict[str, Any],
    *,
    min_rows: int = 1,
    required_cols: tuple[str, ...] = (),
) -> None:
    """Assert that a TablePayload dict contains valid columns and rows."""
    assert isinstance(payload, dict), f"Expected dict payload, got {type(payload)}"
    cols = payload.get("columns", [])
    rows = payload.get("rows", [])
    assert isinstance(cols, list) and len(cols) > 0, "TablePayload missing columns"
    assert isinstance(rows, list) and len(rows) >= min_rows, (
        f"Expected >={min_rows} rows, got {len(rows)}"
    )
    col_keys = {c.get("key") for c in cols if isinstance(c, dict)}
    for req in required_cols:
        assert req in col_keys, f"Missing required column '{req}' in {col_keys}"


def assert_finite_number(value: Any, label: str = "metric") -> float:
    """Assert that value is a finite int or float and return it as float."""
    assert isinstance(value, (int, float)) and not isinstance(value, bool), (
        f"{label} is not numeric: {value!r}"
    )
    fval = float(value)
    assert math.isfinite(fval), f"{label} is not finite: {fval}"
    return fval
