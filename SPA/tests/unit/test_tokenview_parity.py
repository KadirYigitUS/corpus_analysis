"""Test 8-scope and 32-combination TokenView matrix parity across SPA and corpus_toolkit."""

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


@pytest.fixture(scope="module")
def repo():
    return CorpusRepository()


def test_all_8_scopes_and_author_filters(repo):
    """Verify all 8 corpus scopes and secondary author_filter / text_code selection."""
    expected_counts = [
        (CorpusScopeDTO(scope="all"), 13),
        (CorpusScopeDTO(scope="all_en"), 5),
        (CorpusScopeDTO(scope="trans_en"), 5),
        (CorpusScopeDTO(scope="all_tr"), 8),
        (CorpusScopeDTO(scope="trans_tr"), 5),
        (CorpusScopeDTO(scope="indig_tr"), 3),
        (CorpusScopeDTO(scope="author_related", author_filter="SM"), 3),
        (CorpusScopeDTO(scope="author_related", author_filter="ZB"), 7),
        (CorpusScopeDTO(scope="author_related", author_filter="OK"), 3),
        (CorpusScopeDTO(scope="author_turkish", author_filter="SM"), 2),
        (CorpusScopeDTO(scope="author_turkish", author_filter="ZB"), 4),
        (CorpusScopeDTO(scope="author_turkish", author_filter="OK"), 2),
        (CorpusScopeDTO(scope="single", text_code="BR-SM"), 1),
        (CorpusScopeDTO(scope="all", author_filter="SM"), 3),
        (CorpusScopeDTO(scope="all_tr", author_filter="ZB"), 4),
    ]
    for scope_dto, expected in expected_counts:
        texts = repo.get_texts_by_scope(scope_dto)
        assert len(texts) == expected, f"Scope {scope_dto} returned {len(texts)}, expected {expected}"

    # Verify parse_scope_and_view helper
    sc, vp = parse_scope_and_view(
        args={"category": "author_turkish", "author_filter": "OK", "field": "lem"},
        body={"filter_function_words": "true", "mode": "mask", "punct": "split"},
    )
    assert sc.scope == "author_turkish"
    assert sc.author_filter == "OK"
    assert vp.field == "lem"
    assert vp.filter_function_words is True
    assert vp.mode == "mask"
    assert vp.punct == "split"


def test_32_combination_tokenview_parity_and_drop_vs_mask(repo):
    """Test all 2x2x2x4 = 32 combinations of TokenView parameters and drop vs mask distinction."""
    fields = ("tok", "lem")
    filters = (False, True)
    modes = ("drop", "mask")
    puncts = ("drop", "keep", "strip", "split")

    text = repo.loader.load_text("BR-SM")
    combinations = list(itertools.product(fields, filters, modes, puncts))
    assert len(combinations) == 32

    for field, filt, mode, punct in combinations:
        dto = TokenViewParamsDTO(
            field=field,
            filter_function_words=filt,
            mode=mode,
            punct=punct,
        )
        repo_view = repo.get_token_view(text, dto)
        direct_view = TokenView(
            text=text,
            field=field,
            filter_function_words=filt,
            mode=mode,
            punct=punct,
        )
        assert len(repo_view.forms) == len(direct_view.forms)
        assert list(repo_view.forms[:50]) == list(direct_view.forms[:50])

        # Verify get_text_tokens_matrix include_masked=False vs include_masked=True
        mat_unmasked = repo.get_text_tokens_matrix([text], dto, include_masked=False)["BR-SM"]
        mat_masked = repo.get_text_tokens_matrix([text], dto, include_masked=True)["BR-SM"]
        assert all(x is not None for x in mat_unmasked)
        assert len(mat_unmasked) == len(direct_view.analysed())
        if filt and mode == "mask":
            assert any(x is None for x in mat_masked)
            assert len(mat_masked) == len(direct_view.forms)
        else:
            assert all(x is not None for x in mat_masked)

    # Verify mode='drop' vs mode='mask' produces distinct MATTR and Collocation scores
    div_svc = DiversityService(repo)
    col_svc = CollocationService(repo)
    sc_single = CorpusScopeDTO(scope="single", text_code="BR-SM")
    vp_drop = TokenViewParamsDTO(field="lem", filter_function_words=True, mode="drop", punct="drop")
    vp_mask = TokenViewParamsDTO(field="lem", filter_function_words=True, mode="mask", punct="drop")

    row_drop = div_svc.get_diversity_table(vp_drop, sc_single)[0]
    row_mask = div_svc.get_diversity_table(vp_mask, sc_single)[0]
    assert row_drop["N"] == row_mask["N"]
    assert row_drop["V"] == row_mask["V"]
    assert row_drop["MATTR_100"] != row_mask["MATTR_100"]
    assert row_drop["MATTR_500"] != row_mask["MATTR_500"]

    c_params = CollocationParamsDTO(node_query="robot", text_code="BR-SM", min_freq=2, stat_metric="G2")
    col_drop = col_svc.get_collocations(c_params, vp_drop)
    col_mask = col_svc.get_collocations(c_params, vp_mask)
    assert col_drop["R1"] != col_mask["R1"]

