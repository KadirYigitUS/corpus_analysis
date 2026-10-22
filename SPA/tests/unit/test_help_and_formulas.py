"""Unit tests for the 12-section Help & Formula Catalog, MathML/HTML formatting, and DI cache."""

from __future__ import annotations

from flask import Flask
from flask.testing import FlaskClient

from SPA.models.view_params_dto import CorpusScopeDTO, TokenViewParamsDTO
from SPA.services.payload_cache import global_payload_cache

EXPECTED_HELP_TABS = {
    "Global Matrix",
    "Tab 1",
    "Tab 2",
    "Tab 3",
    "Tab 4",
    "Tab 5",
    "Tab 6",
    "Tab 7",
    "Tab 8",
    "Tab 9",
    "Tab 10",
    "Tab 11",
}


def test_help_formulas_catalog_completeness_and_zero_raw_latex(client: FlaskClient) -> None:
    """Verify /api/v1/help/formulas covers Global Matrix + Tabs 1..11 with semantic HTML math."""
    resp = client.get("/api/v1/help/formulas")
    assert resp.status_code == 200
    catalog = resp.get_json()
    assert isinstance(catalog, dict) and len(catalog) == 12

    seen_tabs = set()
    for section_key, entries in catalog.items():
        assert isinstance(entries, list) and len(entries) >= 1, (
            f"Section '{section_key}' has no entries"
        )
        for entry in entries:
            assert "tab" in entry and "name" in entry
            assert "formula" in entry and "formula_html" in entry
            assert "description" in entry and "nan_guard" in entry and "citation" in entry
            seen_tabs.add(entry["tab"])

            for text_field in (entry["formula"], entry["formula_html"], entry["description"]):
                for raw_latex in (r"\frac", r"\text", r"\sqrt", r"\sum", r"\cdot"):
                    assert raw_latex not in text_field, (
                        f"Raw LaTeX '{raw_latex}' found in {entry['tab']}: {text_field}"
                    )

    assert seen_tabs == EXPECTED_HELP_TABS

    raw_body = resp.get_data(as_text=True)
    assert "math-frac" in raw_body
    assert "math-num" in raw_body
    assert "math-den" in raw_body
    assert "math-sqrt" in raw_body


def test_singleton_di_and_payload_cache_eviction(app: Flask, client: FlaskClient) -> None:
    """Verify all corpus services share a single CorpusRepository/Loader and evict-all clears cache."""
    repo = app.extensions["corpus_repo"]
    services = app.extensions["services"]
    assert len(services) == 22

    loader_id = id(repo._loader)
    for name, svc in services.items():
        assert hasattr(svc, "_repo"), f"Service '{name}' missing _repo"
        assert id(svc._repo) == id(repo), f"Service '{name}' has distinct CorpusRepository"
        assert id(svc._repo._loader) == loader_id, f"Service '{name}' has distinct CorpusLoader"

    k_drop = global_payload_cache.build_key(
        "test:ns",
        scope=CorpusScopeDTO(scope="all_tr", author_filter="SM"),
        view=TokenViewParamsDTO(field="lem", filter_function_words=True, mode="drop", punct="drop"),
        term="robot",
    )
    k_mask = global_payload_cache.build_key(
        "test:ns",
        scope=CorpusScopeDTO(scope="all_tr", author_filter="SM"),
        view=TokenViewParamsDTO(field="lem", filter_function_words=True, mode="mask", punct="drop"),
        term="robot",
    )
    assert k_drop != k_mask

    global_payload_cache.put(k_drop, {"cached": True})
    assert global_payload_cache.get(k_drop) == {"cached": True}

    ev_resp = client.post("/api/v1/corpus/evict-all")
    assert ev_resp.status_code == 200
    assert global_payload_cache.get(k_drop) is None
