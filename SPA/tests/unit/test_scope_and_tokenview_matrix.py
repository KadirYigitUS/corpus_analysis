"""Parametrized unit tests for the 8 Corpus Scopes and 32 TokenView combinations."""

from __future__ import annotations

import itertools

import pytest

from corpus_toolkit.tokenview import TokenView
from SPA.models.stats_dto import CollocationParamsDTO
from SPA.models.view_params_dto import (
    CorpusScopeDTO,
    TokenViewParamsDTO,
    parse_scope_and_view,
)
from SPA.repositories.corpus_repository import CorpusRepository
from SPA.services.collocation_service import CollocationService
from SPA.services.diversity_service import DiversityService
from SPA.tests.conftest import assert_finite_number

SCOPE_EXPECTATIONS = [
    ("all", None, None, 13),
    ("all_tr", None, None, 8),
    ("trans_en", None, None, 5),
    ("trans_tr", None, None, 5),
    ("indig_tr", None, None, 3),
    ("author_related", "SM", None, 3),
    ("author_related", "ZB", None, 7),
    ("author_related", "OK", None, 3),
    ("author_turkish", "SM", None, 2),
    ("author_turkish", "ZB", None, 4),
    ("author_turkish", "OK", None, 2),
    ("single", None, "BR-SM", 1),
    ("all", "SM", None, 3),
    ("all_tr", "OK", None, 2),
]

ALL_32_VIEW_COMBOS = list(
    itertools.product(
        ("tok", "lem"),
        (False, True),
        ("drop", "mask"),
        ("drop", "keep", "strip", "split"),
    )
)


@pytest.mark.parametrize(
    ("scope_name", "author_filter", "text_code", "expected_count"),
    SCOPE_EXPECTATIONS,
)
def test_corpus_scope_resolution_and_api_counts(
    corpus_repo: CorpusRepository,
    client,
    scope_name: str,
    author_filter: str | None,
    text_code: str | None,
    expected_count: int,
) -> None:
    """Verify repository text resolution and /inventory endpoint across all 8 scopes."""
    scope_dto = CorpusScopeDTO(
        scope=scope_name,
        author_filter=author_filter,
        text_code=text_code,
    )
    texts = corpus_repo.get_texts_by_scope(scope_dto)
    assert len(texts) == expected_count

    qs = f"scope={scope_name}"
    if author_filter:
        qs += f"&author_filter={author_filter}"
    if text_code:
        qs += f"&text_code={text_code}"
    resp = client.get(f"/api/v1/corpus/inventory?{qs}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total_texts"] == expected_count
    assert data["total_tokens"] > 0


@pytest.mark.parametrize(
    ("field", "filter_fw", "mode", "punct"),
    ALL_32_VIEW_COMBOS,
)
def test_32_tokenview_combinations_invariants(
    corpus_repo: CorpusRepository,
    field: str,
    filter_fw: bool,
    mode: str,
    punct: str,
) -> None:
    """Verify forms vs analysed() invariants across all 32 TokenView states on A-ZB."""
    text = corpus_repo.loader.load_text("A-ZB")
    dto = TokenViewParamsDTO(
        field=field,
        filter_function_words=filter_fw,
        mode=mode,
        punct=punct,
    )
    spa_view = corpus_repo.get_token_view(text, dto)
    tk_view = TokenView(
        text=text,
        field=field,
        filter_function_words=filter_fw,
        mode=mode,
        punct=punct,
    )
    assert len(spa_view.forms) == len(tk_view.forms)
    assert len(spa_view.analysed()) == len(tk_view.analysed())

    unmasked = corpus_repo.get_text_tokens_matrix([text], dto, include_masked=False)["A-ZB"]
    masked = corpus_repo.get_text_tokens_matrix([text], dto, include_masked=True)["A-ZB"]
    assert all(tok is not None for tok in unmasked)
    assert len(unmasked) == len(tk_view.analysed())

    if filter_fw:
        unfiltered = TokenView(
            text=text, field=field, filter_function_words=False, mode="drop", punct=punct
        )
        if mode == "mask":
            assert len(spa_view.forms) == len(unfiltered.forms)
            assert any(tok is None for tok in masked)
        else:
            assert len(spa_view.forms) < len(unfiltered.forms)
            assert all(tok is not None for tok in masked)


def test_drop_vs_mask_punct_and_field_ordering(corpus_repo: CorpusRepository) -> None:
    """Verify drop vs mask distinction and punct/field inequalities on BR-SM."""
    text = corpus_repo.loader.load_text("BR-SM")
    v_drop_p = TokenView(text, field="tok", filter_function_words=False, mode="drop", punct="drop")
    v_keep_p = TokenView(text, field="tok", filter_function_words=False, mode="drop", punct="keep")
    v_split_p = TokenView(text, field="tok", filter_function_words=False, mode="drop", punct="split")
    assert len(v_keep_p.forms) >= len(v_split_p.forms) >= len(v_drop_p.forms)

    v_tok = TokenView(text, field="tok", filter_function_words=False, mode="drop", punct="drop")
    v_lem = TokenView(text, field="lem", filter_function_words=False, mode="drop", punct="drop")
    assert len(set(v_lem.analysed())) <= len(set(v_tok.analysed()))

    div_svc = DiversityService(corpus_repo)
    col_svc = CollocationService(corpus_repo)
    sc = CorpusScopeDTO(scope="single", text_code="BR-SM")
    vp_drop = TokenViewParamsDTO(field="lem", filter_function_words=True, mode="drop", punct="drop")
    vp_mask = TokenViewParamsDTO(field="lem", filter_function_words=True, mode="mask", punct="drop")

    r_drop = div_svc.get_diversity_table(vp_drop, sc)[0]
    r_mask = div_svc.get_diversity_table(vp_mask, sc)[0]
    assert r_drop["N"] == r_mask["N"] and r_drop["V"] == r_mask["V"]
    assert assert_finite_number(r_drop["MATTR_100"]) != assert_finite_number(r_mask["MATTR_100"])
    assert assert_finite_number(r_drop["MATTR_500"]) != assert_finite_number(r_mask["MATTR_500"])

    traj_drop = div_svc.get_mattr_trajectory("BR-SM", vp_drop, window=200)
    traj_mask = div_svc.get_mattr_trajectory("BR-SM", vp_mask, window=200)
    assert traj_drop["mean_ttr"] != traj_mask["mean_ttr"]

    c_dto = CollocationParamsDTO(node_query="robot", text_code="BR-SM", min_freq=2, stat_metric="G2")
    c_drop = col_svc.get_collocations(c_dto, vp_drop)
    c_mask = col_svc.get_collocations(c_dto, vp_mask)
    assert c_drop["R1"] != c_mask["R1"]

    sc_parsed, vp_parsed = parse_scope_and_view(
        args={"scope": "author_related", "author_filter": "ZB"},
        body={"view_params": {"field": "lem", "filter_function_words": True, "mode": "mask", "punct": "strip"}},
    )
    assert sc_parsed.scope == "author_related" and sc_parsed.author_filter == "ZB"
    assert vp_parsed.mode == "mask" and vp_parsed.punct == "strip"
