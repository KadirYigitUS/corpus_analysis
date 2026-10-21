"""Service for NDA parallel corpora view, visual sets, and dictionary drawer."""

from __future__ import annotations

from typing import Any

from corpus_toolkit.parallel_view import parallel_html
from SPA.repositories.corpus_repository import CorpusRepository
from SPA.repositories.nda_cache_repository import NdaCacheRepository


class NdaParallelService:
    """Manages Tab 3 parallel view, SVG link metadata, and dictionary drawer."""

    def __init__(
        self,
        corpus_repo: CorpusRepository,
        nda_repo: NdaCacheRepository,
    ) -> None:
        self._corpus_repo = corpus_repo
        self._nda_repo = nda_repo

    def get_parallel_html(
        self,
        pair_code: str,
        alignment_ids: list[int] | None = None,
        max_rows: int = 20,
    ) -> str:
        """Render self-contained HTML for parallel sentences with NDA pills and links."""
        if alignment_ids is not None:
            ais = alignment_ids
        else:
            overlay = self._nda_repo.get_overlay_for_pair(pair_code)
            linked_ais = sorted(
                ai for ai, s in overlay.row_summaries.items() if s.linked_pairs and ai > 0
            )
            ais = linked_ais[:8]
            for r in range(1, max_rows * 2):
                if len(ais) >= max_rows:
                    break
                if r not in ais:
                    ais.append(r)
            ais.sort()
        try:
            return parallel_html(self._corpus_repo.loader, pair_code, ais=ais)
        except Exception as exc:
            return f"<div class='nda-alert'>Parallel view unavailable: {exc}</div>"

    def get_tripartite_dictionary(
        self, pair_code: str
    ) -> dict[str, Any]:
        """Fetch dictionary entries grouped into linked, single_eng, and single_tur."""
        raw_dict = self._nda_repo.get_tripartite_dictionary(pair_code)
        return {
            "pair_code": pair_code,
            "has_cache": self._nda_repo.has_cache(pair_code),
            "linked_count": len(raw_dict.get("linked", [])),
            "single_eng_count": len(raw_dict.get("single_eng", [])),
            "single_tur_count": len(raw_dict.get("single_tur", [])),
            "entries": raw_dict,
        }

    def get_row_attribution_summary(
        self, pair_code: str, alignment_idx: int
    ) -> dict[str, Any]:
        """Return the Current Label Attributions footer for a specific alignment row."""
        overlay = self._nda_repo.get_overlay_for_pair(pair_code)
        summary = overlay.row_summaries.get(alignment_idx)
        if not summary:
            return {
                "ai": alignment_idx,
                "linked_pairs": [],
                "single_eng": [],
                "single_tur": [],
                "top_candidates": [],
            }
        return {
            "ai": alignment_idx,
            "linked_pairs": summary.linked_pairs,
            "single_eng": summary.single_eng,
            "single_tur": summary.single_tur,
            "top_candidates": summary.top_candidates,
        }
