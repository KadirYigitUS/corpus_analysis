"""Service for NDA parallel corpora view, visual sets, and dictionary drawer."""

from __future__ import annotations

import math
from typing import Any

from corpus_toolkit.parallel_view import PV_CSS, _resolve_pair, parallel_html
from corpus_toolkit.style import CSS
from SPA.repositories.corpus_repository import CorpusRepository
from SPA.repositories.nda_cache_repository import NdaCacheRepository

_SPA_PV_OVERRIDE = """
<style>
.ct.pv { background: #ffffff; color: #0f172a; padding: 10px 12px; border-radius: 8px;
         border: 1px solid #cbd5e1; box-shadow: 0 1px 3px rgba(15,23,42,.08); }
.ct.pv table.pv-grid th { color: #0f172a; }
.ct.pv table.pv-grid td { color: #0f172a; }
</style>
"""


class NdaParallelService:
    """Manages Tab 3 parallel view, SVG link metadata, and dictionary drawer."""

    def __init__(
        self,
        corpus_repo: CorpusRepository,
        nda_repo: NdaCacheRepository,
    ) -> None:
        self._corpus_repo = corpus_repo
        self._nda_repo = nda_repo

    def get_parallel_payload(
        self,
        pair_code: str,
        mode: str = "linked",
        page: int = 1,
        max_rows: int = 15,
        alignment_ids: list[int] | None = None,
        hits: list[str] | None = None,
    ) -> dict[str, Any]:
        """Return paginated notebook-identical parallel view HTML + pagination metadata."""
        try:
            pair_obj = _resolve_pair(self._corpus_repo.loader, pair_code)
            idx = self._corpus_repo.loader.alignment_index(pair_obj)
            all_ais = sorted(int(a) for a in idx.frame.reset_index()["ai"].tolist() if int(a) > 0)
        except Exception as exc:
            return {
                "pair_code": pair_code,
                "mode": mode,
                "page": 1,
                "total_pages": 1,
                "total_groups": 0,
                "ais": [],
                "html": f"<div class='nda-alert'>Parallel view unavailable: {exc}</div>",
            }

        overlay = self._nda_repo.get_overlay_for_pair(pair_code)
        linked_ais = sorted(
            ai for ai, s in overlay.row_summaries.items() if s.linked_pairs and ai > 0
        )

        if alignment_ids:
            pool = [a for a in alignment_ids if a in set(all_ais)]
            if not pool:
                pool = alignment_ids[:max_rows]
        elif mode == "all":
            pool = all_ais
        else:
            # 'linked' mode: show linked groups first, then fill with sequential AIs
            pool = list(linked_ais)
            if len(pool) < max_rows:
                seen = set(pool)
                for a in all_ais:
                    if a not in seen:
                        pool.append(a)
                        seen.add(a)
                    if len(pool) >= max(max_rows, 60):
                        break

        page_size = max(1, min(50, int(max_rows)))
        total_groups = len(pool)
        total_pages = max(1, math.ceil(total_groups / page_size))
        cur_page = min(max(1, int(page)), total_pages)
        start = (cur_page - 1) * page_size
        selected_ais = pool[start : start + page_size]

        try:
            raw_html = parallel_html(
                self._corpus_repo.loader,
                pair_obj,
                ais=selected_ais,
                overlay=True,
                hits=hits,
                show_lemma=True,
            )
            full_html = CSS + PV_CSS + _SPA_PV_OVERRIDE + raw_html
        except Exception as exc:
            full_html = f"<div class='nda-alert'>Parallel view unavailable: {exc}</div>"

        return {
            "pair_code": pair_code,
            "mode": mode,
            "page": cur_page,
            "page_size": page_size,
            "total_pages": total_pages,
            "total_groups": total_groups,
            "linked_groups_total": len(linked_ais),
            "ais": selected_ais,
            "html": full_html,
        }

    def get_parallel_html(
        self,
        pair_code: str,
        alignment_ids: list[int] | None = None,
        max_rows: int = 15,
    ) -> str:
        """Backwards-compatible HTML helper returning CSS + PV_CSS + parallel_html."""
        res = self.get_parallel_payload(
            pair_code=pair_code,
            mode="custom" if alignment_ids else "linked",
            page=1,
            max_rows=max_rows,
            alignment_ids=alignment_ids,
        )
        return str(res["html"])

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
