"""Service for translation alignment, sentence ratios, and length delta analysis."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

from SPA.models.alignment_dto import AlignmentFilterDTO, AlignmentRowDTO
from SPA.repositories.corpus_repository import CorpusRepository
from SPA.services.alignment_ner_service import AlignmentNerService
from SPA.services.alignment_stats_service import AlignmentStatsService


class AlignmentDeltaService:
    """Manages Tab 2 alignment rows, length deltas, and NER filtering."""

    def __init__(
        self,
        corpus_repo: CorpusRepository,
        stats_service: AlignmentStatsService | None = None,
        ner_service: AlignmentNerService | None = None,
    ) -> None:
        self._repo = corpus_repo
        self._stats = stats_service or AlignmentStatsService(corpus_repo)
        self._ner = ner_service
        self._text_map_cache: dict[str, dict[int, tuple[str, str]]] = {}

    def get_alignment_kpis(
        self, pair_code: str, chapter_no: int | None = None
    ) -> dict[str, Any]:
        """Calculate KPI statistics (including 9 length_view KPIs) for a translation pair."""
        res = self._stats.get_stats_and_series(pair_code, chapter_no=chapter_no)
        if "error" in res:
            return res
        s = res["stats"]
        df = self._stats.get_compact_frame(pair_code)
        type_counts = (
            {str(k): int(v) for k, v in df["type"].value_counts().items()}
            if df is not None
            else {}
        )
        return {
            "pair_code": pair_code,
            "pair_label": res["pair_label"],
            "total_alignments": s["total"],
            "sentence_ratio": s["sentence_ratio"],
            "one_to_one_pct": s["one_to_one_pct"],
            "expansion_ratio": s["expansion_ratio"],
            "count_tur_more": s["count_tur_more"],
            "count_eng_more": s["count_eng_more"],
            "count_one_one": s["count_one_one"],
            "max_sent_diff": s["max_sent_diff"],
            "min_sent_diff": s["min_sent_diff"],
            "avg_len_eng": s["avg_len_eng"],
            "avg_len_tur": s["avg_len_tur"],
            "avg_len_diff": s["avg_len_diff"],
            "type_counts": type_counts,
        }

    def get_chapter_navigation(self, pair_code: str) -> list[dict[str, Any]]:
        """Return chapter list with alignment row counts for sidebar badges."""
        df = self._stats.get_compact_frame(pair_code)
        if df is None or df.empty:
            return []
        counts = df.groupby("ch", sort=True).size()
        return [
            {"chapter": int(ch), "alignment_count": int(cnt)}
            for ch, cnt in counts.items()
        ]

    def get_filtered_rows(
        self, filter_dto: AlignmentFilterDTO
    ) -> dict[str, Any]:
        """Two-stage O(1) slice pagination with NER filter, text search, and token hydration."""
        found = self._stats.find_pair(filter_dto.pair_code)
        df = self._stats.get_compact_frame(filter_dto.pair_code)
        if not found or df is None or df.empty:
            return {"total": 0, "total_pages": 1, "page": 1, "page_size": filter_dto.page_size, "rows": []}
        spec, _, _ = found

        sub = df
        if filter_dto.chapter_no is not None:
            sub = sub[sub["ch"] == int(filter_dto.chapter_no)]
        if filter_dto.row_type:
            sub = sub[sub["type"] == filter_dto.row_type]
        if filter_dto.min_delta is not None:
            sub = sub[sub["delta_w"].abs() >= int(filter_dto.min_delta)]

        if filter_dto.ner_category and self._ner is not None:
            allowed_ais = self._ner.matching_ais(spec.pair_id, filter_dto.ner_category)
            if allowed_ais is not None:
                sub = sub[sub["ai"].isin(allowed_ais)]

        text_map = self._get_text_map(spec)
        if filter_dto.search_query:
            q = filter_dto.search_query.lower()
            matching = [
                ai for ai in sub["ai"].astype(int)
                if q in text_map.get(ai, ("", ""))[0].lower()
                or q in text_map.get(ai, ("", ""))[1].lower()
                or q == str(ai)
            ]
            sub = sub[sub["ai"].isin(matching)]

        sub = self._sort_compact(sub, filter_dto.sort_by, filter_dto.ascending)
        total = int(len(sub))
        total_pages = max(1, math.ceil(total / filter_dto.page_size))
        page = min(max(1, filter_dto.page), total_pages)
        start = (page - 1) * filter_dto.page_size
        sliced = sub.iloc[start : start + filter_dto.page_size]

        dtos: list[dict[str, Any]] = []
        for r in sliced.itertuples(index=False):
            ai = int(r.ai)
            eng_txt, tur_txt = text_map.get(ai, ("", ""))
            ner_en, ner_tr, ann_en, ann_tr = (
                self._ner.get_row_annotations(spec.pair_id, ai)
                if self._ner is not None
                else ([], [], [], [])
            )
            ratio_w = float(r.tur_words / r.eng_words) if r.eng_words else 1.0
            dtos.append(
                AlignmentRowDTO(
                    alignment_idx=ai,
                    chapter_no=int(r.ch),
                    eng_text=eng_txt,
                    tur_text=tur_txt,
                    sent_eng=int(r.sent_eng),
                    sent_tur=int(r.sent_tur),
                    sent_diff=int(r.sent_diff),
                    len_diff=int(r.len_diff),
                    eng_tokens=eng_txt.split(),
                    tur_tokens=tur_txt.split(),
                    delta_words=int(r.delta_w),
                    delta_chars=int(r.delta_c),
                    ratio_words=ratio_w,
                    alignment_type=str(r.type),
                    ner_tags_eng=ner_en,
                    ner_tags_tur=ner_tr,
                    ann_eng=ann_en,
                    ann_tur=ann_tr,
                ).to_dict()
            )

        return {
            "total": total,
            "total_pages": total_pages,
            "page": page,
            "page_size": filter_dto.page_size,
            "rows": dtos,
        }

    def _get_text_map(self, spec: Any) -> dict[int, tuple[str, str]]:
        if spec.pair_id in self._text_map_cache:
            return self._text_map_cache[spec.pair_id]
        idx = self._repo.loader.alignment_index(spec)
        fr = idx.frame.reset_index()
        tmap = {
            int(r.ai): (
                str(r.eng) if isinstance(r.eng, str) else "",
                str(r.tur) if isinstance(r.tur, str) else "",
            )
            for r in fr.itertuples(index=False)
        }
        self._text_map_cache[spec.pair_id] = tmap
        return tmap

    @staticmethod
    def _sort_compact(df: pd.DataFrame, sort_by: str, ascending: bool) -> pd.DataFrame:
        if df.empty:
            return df
        col_map = {
            "ai": "ai",
            "ch": "ch",
            "sent_eng": "sent_eng",
            "sent_tur": "sent_tur",
            "sent_diff": "sent_diff",
            "len_diff": "len_diff",
            "delta_w": "delta_w",
            "delta_c": "delta_c",
            "type": "type",
        }
        col = col_map.get(sort_by, "ai")
        return df.sort_values(by=[col, "ai"], ascending=[ascending, True], kind="mergesort")
