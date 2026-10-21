"""Memory benchmark tests verifying RSS stays strictly below 1500 MB."""

from SPA.models.view_params_dto import CorpusScopeDTO, TokenViewParamsDTO
from SPA.repositories.corpus_repository import CorpusRepository
from SPA.services.inventory_memory_service import InventoryMemoryService


def test_process_rss_memory_bounds():
    """Verify that RSS consumption remains strictly under 1500 MB budget."""
    repo = CorpusRepository()
    inv_service = InventoryMemoryService(repo)

    # 1. Check baseline RSS
    stats = inv_service.get_summary_stats()
    rss_mb = stats["rss_mb"]
    assert (
        rss_mb < 1500.0
    ), f"Baseline RSS {rss_mb} MB exceeds 1500 MB ceiling"

    # 2. Perform loading and TokenView across all texts
    texts = repo.get_texts_by_scope(CorpusScopeDTO(scope="all"))
    params = TokenViewParamsDTO(field="lem", filter_function_words=True)
    matrix = repo.get_text_tokens_matrix(texts, params)

    assert len(matrix) == 13

    # 3. Check post-computation RSS
    post_stats = inv_service.get_summary_stats()
    post_rss_mb = post_stats["rss_mb"]
    assert (
        post_rss_mb < 1500.0
    ), f"Post-computation RSS {post_rss_mb} MB exceeds 1500 MB ceiling"
