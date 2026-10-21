"""Service for translation alignment, sentence ratios, and length delta analysis."""

from __future__ import annotations

from typing import Any

from corpus_toolkit.alignment import AlignmentStructureAnalyzer
from corpus_toolkit.lazy import LazyCorpusText
from corpus_toolkit.registry import PairSpec
from SPA.models.alignment_dto import AlignmentFilterDTO, AlignmentRowDTO
from SPA.repositories.corpus_repository import CorpusRepository


class AlignmentDeltaService:
    """Manages Tab 2 alignment rows, length deltas, and NER filtering."""

    def __init__(self, corpus_repo: CorpusRepository) -> None:
        self._repo = corpus_repo

    def get_alignment_kpis(self, pair_code: str) -> dict[str, Any]:
        """Calculate KPI statistics for a translation pair."""
        found = self._find_pair(pair_code)
        if not found:
            return {"error": f"Pair not found: {pair_code}"}
        spec, _, _ = found
        analyzer = AlignmentStructureAnalyzer(self._repo.loader.cache)
        card = analyzer.cardinality_table(spec)
        n_eng_sum = float(card["n_eng"].sum())
        n_tur_sum = float(card["n_tur"].sum())
        eng_w_sum = float(card["eng_words"].sum())
        tur_w_sum = float(card["tur_words"].sum())
        tot = len(card)
        return {
            "pair_code": pair_code,
            "total_alignments": tot,
            "sentence_ratio": round(n_tur_sum / n_eng_sum, 3) if n_eng_sum else 1.0,
            "one_to_one_pct": round(100.0 * float((card["type"] == "1:1").sum()) / float(tot), 2) if tot else 0.0,
            "expansion_ratio": round(tur_w_sum / eng_w_sum, 3) if eng_w_sum else 1.0,
            "type_counts": {str(k): int(v) for k, v in card["type"].value_counts().items()},
        }

    def get_chapter_navigation(self, pair_code: str) -> list[dict[str, Any]]:
        """Return chapter list with alignment row counts for sidebar badges."""
        found = self._find_pair(pair_code)
        if not found:
            return []
        spec, _, _ = found
        idx = self._repo.loader.alignment_index(spec)
        ch_counts: dict[int, int] = {}
        for coords in idx.map_eng.values():
            ch = coords[0][0] if coords else 1
            ch_counts[ch] = ch_counts.get(ch, 0) + 1
        return [
            {"chapter": ch, "alignment_count": cnt}
            for ch, cnt in sorted(ch_counts.items())
        ]

    def get_filtered_rows(
        self, filter_dto: AlignmentFilterDTO
    ) -> dict[str, Any]:
        """Fetch paginated, filtered, and sorted alignment rows."""
        found = self._find_pair(filter_dto.pair_code)
        if not found:
            return {"total": 0, "rows": []}
        spec, _, _ = found
        analyzer = AlignmentStructureAnalyzer(self._repo.loader.cache)
        card = analyzer.cardinality_table(spec)
        idx = self._repo.loader.alignment_index(spec)

        raw_rows: list[dict[str, Any]] = []
        for row in card.itertuples(index=False):
            ai = int(row.ai)
            coords_en, coords_tr = idx.coords(ai)
            ch = coords_en[0][0] if coords_en else (coords_tr[0][0] if coords_tr else 1)
            if filter_dto.chapter_no is not None and ch != filter_dto.chapter_no:
                continue
            if filter_dto.row_type and row.type != filter_dto.row_type:
                continue
            delta_w = int(row.tur_words - row.eng_words)
            delta_c = int(row.tur_chars - row.eng_chars)
            if filter_dto.min_delta is not None and abs(delta_w) < filter_dto.min_delta:
                continue
            eng_txt, tur_txt = idx.texts(ai)
            ratio_w = float(row.tur_words / row.eng_words) if row.eng_words else 1.0
            raw_rows.append({
                "alignment_idx": ai,
                "chapter_no": ch,
                "eng_text": eng_txt,
                "tur_text": tur_txt,
                "eng_tokens": eng_txt.split(),
                "tur_tokens": tur_txt.split(),
                "delta_words": delta_w,
                "delta_chars": delta_c,
                "ratio_words": ratio_w,
                "alignment_type": row.type,
            })

        # Apply sorting
        reverse = not filter_dto.ascending
        if filter_dto.sort_by == "delta_w":
            raw_rows.sort(key=lambda r: abs(r["delta_words"]), reverse=reverse)
        elif filter_dto.sort_by == "delta_c":
            raw_rows.sort(key=lambda r: abs(r["delta_chars"]), reverse=reverse)
        elif filter_dto.sort_by == "ratio_w":
            raw_rows.sort(key=lambda r: r["ratio_words"], reverse=reverse)
        else:
            raw_rows.sort(key=lambda r: r["alignment_idx"], reverse=reverse)

        total = len(raw_rows)
        start = (filter_dto.page - 1) * filter_dto.page_size
        end = start + filter_dto.page_size
        sliced = raw_rows[start:end]

        dtos = [
            AlignmentRowDTO(
                alignment_idx=r["alignment_idx"],
                chapter_no=r["chapter_no"],
                eng_text=r["eng_text"],
                tur_text=r["tur_text"],
                eng_tokens=r["eng_tokens"],
                tur_tokens=r["tur_tokens"],
                delta_words=r["delta_words"],
                delta_chars=r["delta_chars"],
                ratio_words=r["ratio_words"],
                alignment_type=r["alignment_type"],
            ).to_dict()
            for r in sliced
        ]

        return {
            "total": total,
            "page": filter_dto.page,
            "page_size": filter_dto.page_size,
            "rows": dtos,
        }

    def _find_pair(
        self, pair_code: str | None
    ) -> tuple[PairSpec, LazyCorpusText, LazyCorpusText] | None:
        pairs = self._repo.loader.load_translation_pairs().items
        if not pairs:
            return None
        if not pair_code:
            return pairs[0]
        for spec, eng, tur in pairs:
            if pair_code in (
                spec.pair_id,
                f"{spec.eng.code}_{spec.tur.code}",
                spec.tur.code,
                spec.eng.code,
            ):
                return spec, eng, tur
        return None

