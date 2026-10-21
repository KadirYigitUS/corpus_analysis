"""Service for compact alignment index, 9 length_view KPIs, and sent_diff series."""

from __future__ import annotations

from typing import Any

import pandas as pd

from corpus_toolkit.alignment import AlignmentStructureAnalyzer
from corpus_toolkit.lazy import LazyCorpusText
from corpus_toolkit.registry import PairSpec
from SPA.repositories.corpus_repository import CorpusRepository


class AlignmentStatsService:
    """Computes memory-efficient alignment index, 9 length_view KPIs, and chart series."""

    def __init__(self, corpus_repo: CorpusRepository) -> None:
        self._repo = corpus_repo
        self._compact_cache: dict[str, pd.DataFrame] = {}

    def find_pair(
        self, pair_code: str | None
    ) -> tuple[PairSpec, LazyCorpusText, LazyCorpusText] | None:
        """Resolve a pair_code string to (PairSpec, eng_lazy, tur_lazy)."""
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

    def get_compact_frame(self, pair_code: str) -> pd.DataFrame | None:
        """Return cached compact DataFrame (~400 KB) with chapter and delta columns."""
        found = self.find_pair(pair_code)
        if not found:
            return None
        spec, _, _ = found
        if spec.pair_id in self._compact_cache:
            return self._compact_cache[spec.pair_id]

        analyzer = AlignmentStructureAnalyzer(self._repo.loader.cache)
        card = analyzer.cardinality_table(spec).copy()
        idx = self._repo.loader.alignment_index(spec)

        ch_list: list[int] = []
        for ai in card["ai"].astype(int):
            ce = idx.map_eng.get(ai)
            ct = idx.map_tur.get(ai)
            ch = int(ce[0][0]) if ce else (int(ct[0][0]) if ct else 1)
            ch_list.append(ch)

        card["ch"] = ch_list
        card["sent_eng"] = card["n_eng"].astype(int)
        card["sent_tur"] = card["n_tur"].astype(int)
        card["sent_diff"] = (card["sent_tur"] - card["sent_eng"]).astype(int)
        card["len_eng"] = card["eng_chars"].astype(int)
        card["len_tur"] = card["tur_chars"].astype(int)
        card["len_diff"] = (card["len_tur"] - card["len_eng"]).astype(int)
        card["delta_w"] = (card["tur_words"] - card["eng_words"]).astype(int)
        card["delta_c"] = card["len_diff"]
        self._compact_cache[spec.pair_id] = card
        return card

    def get_stats_and_series(
        self, pair_code: str, chapter_no: int | None = None
    ) -> dict[str, Any]:
        """Compute 9 length_view KPIs + R_sent/expansion + sent_diff series for chart."""
        found = self.find_pair(pair_code)
        df = self.get_compact_frame(pair_code)
        if not found or df is None or df.empty:
            return {"error": f"Pair not found: {pair_code}"}
        spec, _, _ = found

        sub = df[df["ch"] == int(chapter_no)] if chapter_no is not None else df
        if sub.empty:
            sub = df

        tot = len(sub)
        sdiff = sub["sent_diff"]
        n_eng_sum = float(sub["sent_eng"].sum())
        n_tur_sum = float(sub["sent_tur"].sum())
        eng_w_sum = float(sub["eng_words"].sum())
        tur_w_sum = float(sub["tur_words"].sum())

        stats = {
            "total": int(tot),
            "count_tur_more": int((sdiff > 0).sum()),
            "count_eng_more": int((sdiff < 0).sum()),
            "count_one_one": int((sdiff == 0).sum()),
            "strict_one_one": int((sub["type"] == "1:1").sum()),
            "one_to_one_pct": round(100.0 * float((sub["type"] == "1:1").sum()) / float(tot), 2) if tot else 0.0,
            "max_sent_diff": int(sdiff.max()) if tot else 0,
            "min_sent_diff": int(sdiff.min()) if tot else 0,
            "avg_len_eng": round(float(sub["len_eng"].mean()), 1) if tot else 0.0,
            "avg_len_tur": round(float(sub["len_tur"].mean()), 1) if tot else 0.0,
            "avg_len_diff": round(float(sub["len_diff"].mean()), 1) if tot else 0.0,
            "sentence_ratio": round(n_tur_sum / n_eng_sum, 3) if n_eng_sum else 1.0,
            "expansion_ratio": round(tur_w_sum / eng_w_sum, 3) if eng_w_sum else 1.0,
        }

        series = [
            {"ai": int(r.ai), "ch": int(r.ch), "sd": int(r.sent_diff), "ld": int(r.len_diff)}
            for r in sub[["ai", "ch", "sent_diff", "len_diff"]].itertuples(index=False)
        ]

        ch_summary = []
        for ch_val, grp in df.groupby("ch", sort=True):
            gsd = grp["sent_diff"]
            ch_summary.append({
                "ch": int(ch_val),
                "total": int(len(grp)),
                "ai_min": int(grp["ai"].min()),
                "ai_max": int(grp["ai"].max()),
                "tur_more": int((gsd > 0).sum()),
                "eng_more": int((gsd < 0).sum()),
                "one_one": int((gsd == 0).sum()),
                "mean_sd": round(float(gsd.mean()), 3),
            })

        return {
            "pair_code": pair_code,
            "pair_id": spec.pair_id,
            "pair_label": f"{spec.eng.title} ({spec.eng.code}) ⇄ {spec.tur.title} ({spec.tur.code})",
            "scope": f"Chapter {chapter_no}" if chapter_no is not None else "Whole Book (All Chapters)",
            "chapter_no": chapter_no,
            "stats": stats,
            "series": series,
            "chapter_summary": ch_summary,
        }
