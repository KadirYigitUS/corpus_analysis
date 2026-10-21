"""Test 32-combination TokenView matrix parity between SPA and corpus_toolkit."""

import itertools

import pytest

from corpus_toolkit.tokenview import TokenView
from SPA.models.view_params_dto import TokenViewParamsDTO
from SPA.repositories.corpus_repository import CorpusRepository


@pytest.fixture(scope="module")
def repo():
    return CorpusRepository()


def test_32_combination_tokenview_parity(repo):
    """Test all 2x2x2x4 = 32 combinations of TokenView parameters."""
    fields = ("tok", "lem")
    filters = (False, True)
    modes = ("drop", "mask")
    puncts = ("drop", "keep", "strip", "split")

    # Load one text for testing
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
