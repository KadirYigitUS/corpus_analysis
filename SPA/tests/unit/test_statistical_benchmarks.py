"""Test statistical calculations and formula benchmarks across SPA services."""

import pytest

from SPA.models.stats_dto import CollocationParamsDTO, TfidfParamsDTO
from SPA.models.view_params_dto import CorpusScopeDTO, TokenViewParamsDTO
from SPA.repositories.corpus_repository import CorpusRepository
from SPA.services.batch_dispersion_service import BatchDispersionService
from SPA.services.collocation_service import CollocationService
from SPA.services.diversity_service import DiversityService
from SPA.services.tfidf_service import TfidfService


@pytest.fixture(scope="module")
def repo():
    return CorpusRepository()


def test_diversity_service_benchmarks(repo):
    """Verify LancsBox-X diversity table computation."""
    div_service = DiversityService(repo)
    v_params = TokenViewParamsDTO(field="lem", filter_function_words=False)
    scope = CorpusScopeDTO(scope="single", text_code="BR-SM")

    table = div_service.get_diversity_table(v_params, scope)
    assert len(table) == 1
    row = table[0]
    assert row["text_code"] == "BR-SM"
    assert row["N"] > 1000
    assert row["V"] > 100
    assert 0.0 < row["TTR"] < 1.0
    assert row["Yule_K"] > 0.0
    assert 0.0 < row["Simpson_D"] < 1.0


def test_collocation_service_benchmarks(repo):
    """Verify Union-Slot collocation calculation."""
    colloc_service = CollocationService(repo)
    v_params = TokenViewParamsDTO(field="lem")
    c_params = CollocationParamsDTO(
        node_query="robot",
        text_code="BR-SM",
        min_freq=2,
        stat_metric="LogDice",
    )

    res = colloc_service.get_collocations(c_params, v_params)
    assert res["node"] == "robot"
    assert res["f_node"] > 0
    assert res["R1"] > 0
    assert len(res["items"]) > 0
    first = res["items"][0]
    assert "LogDice" in first
    assert "MI" in first
    assert "G2" in first


def test_dispersion_service_benchmarks(repo):
    """Verify Juilland's D and narrative dispersion."""
    disp_service = BatchDispersionService(repo)
    v_params = TokenViewParamsDTO(field="lem")
    scope = CorpusScopeDTO(scope="all_tr")

    res = disp_service.analyze_batch(
        terms=["robot", "insan"],
        view_params=v_params,
        scope_dto=scope,
        n_chunks=10,
    )
    assert "summary" in res
    assert len(res["summary"]) == 2
    for s in res["summary"]:
        assert 0.0 <= s["D_across_texts"] <= 1.0


def test_tfidf_service_benchmarks(repo):
    """Verify sublinear TF-IDF keyness extraction."""
    tfidf_service = TfidfService(repo)
    v_params = TokenViewParamsDTO(field="lem")
    scope = CorpusScopeDTO(scope="all_tr")
    t_params = TfidfParamsDTO(top_k=10, exclude_pos=["PROPN"])

    res = tfidf_service.get_top_keywords_per_text(
        tfidf_params=t_params,
        view_params=v_params,
        scope_dto=scope,
    )
    assert "texts_keywords" in res
    assert len(res["texts_keywords"]) > 0
    for _text_id, kws in res["texts_keywords"].items():
        assert len(kws) <= 10
        if kws:
            assert "term" in kws[0]
            assert "tfidf" in kws[0]
