"""Service for syntactic dependency trees and CoNLL table representation."""

from __future__ import annotations

from typing import Any

from corpus_toolkit.depviz import DependencyVisualizer, displacy_payload
from SPA.repositories.corpus_repository import CorpusRepository


class DepvizService:
    """Manages Tab 5 Universal Dependencies studio and displaCy tree rendering."""

    def __init__(self, corpus_repo: CorpusRepository) -> None:
        self._repo = corpus_repo
        self._viz = DependencyVisualizer(corpus_repo.loader)

    def get_sentence_conll_table(
        self,
        text_code: str,
        chapter_no: int,
        paragraph_no: int,
        sentence_no: int,
    ) -> list[dict[str, Any]]:
        """Return token-by-token dependency tuples for a single sentence."""
        text = self._repo.loader.load_text(text_code)
        sid = self._viz.sid_of(text, (chapter_no, paragraph_no, sentence_no))
        df = self._viz.table(text, sid)
        return df.to_dict(orient="records")

    def get_sentence_tree_svg(
        self,
        text_code: str,
        chapter_no: int,
        paragraph_no: int,
        sentence_no: int,
        dim_function_words: bool = True,
        compact: bool = False,
    ) -> str:
        """Render spaCy-style dependency SVG string for a single sentence."""
        text = self._repo.loader.load_text(text_code)
        sid = self._viz.sid_of(text, (chapter_no, paragraph_no, sentence_no))
        return self._viz.svg(
            text,
            sid,
            dim_function_words=dim_function_words,
            compact=compact,
        )

    def get_sentence_tree_payload(
        self,
        text_code: str,
        chapter_no: int,
        paragraph_no: int,
        sentence_no: int,
    ) -> dict[str, Any]:
        """Return raw displaCy words and arcs payload for client-side rendering."""
        text = self._repo.loader.load_text(text_code)
        sid = self._viz.sid_of(text, (chapter_no, paragraph_no, sentence_no))
        slice_df = self._viz._slice(text, sid).reset_index(drop=True)
        words = slice_df["tok"].astype(str).tolist()
        pos = slice_df["pos"].astype(str).tolist()
        heads = slice_df["head"].astype(int).tolist()
        rels = slice_df["rel"].astype(str).tolist()
        return displacy_payload(
            words, pos, heads, rels, text.record.language, normalize_labels=True
        )

    def get_aligned_tree_pair(
        self,
        pair_code: str,
        alignment_idx: int,
        normalize_labels: bool = True,
        dim_function_words: bool = True,
    ) -> dict[str, Any]:
        """Retrieve aligned dependency payloads for English source and Turkish target."""
        pairs = self._repo.loader.load_translation_pairs().items
        pair = None
        for spec, eng, tur in pairs:
            if pair_code in (
                spec.pair_id,
                f"{spec.eng.code}_{spec.tur.code}",
                spec.tur.code,
                spec.eng.code,
            ):
                pair = (spec, eng, tur)
                break
        if not pair:
            return {"error": f"Pair not found: {pair_code}"}

        spec, eng_text, tur_text = pair
        idx = self._repo.loader.alignment_index(spec)
        eng_coords, tur_coords = idx.coords(alignment_idx)

        eng_svg = ""
        if eng_coords:
            eng_sid = self._viz.sid_of(eng_text, tuple(eng_coords[0]))
            eng_svg = self._viz.svg(
                eng_text,
                eng_sid,
                dim_function_words=dim_function_words,
                normalize_labels=normalize_labels,
            )

        tur_svg = ""
        if tur_coords:
            tur_sid = self._viz.sid_of(tur_text, tuple(tur_coords[0]))
            tur_svg = self._viz.svg(
                tur_text,
                tur_sid,
                dim_function_words=dim_function_words,
                normalize_labels=normalize_labels,
            )

        combined_html = (
            f'<div class="aligned-trees-card" style="display:flex;flex-direction:column;gap:14px;">'
            f'<div class="aligned-tree-row"><div style="font-size:12px;font-weight:700;color:#2563eb;margin-bottom:4px;">'
            f'EN: {eng_text.record.title} ({len(eng_coords)} sent)</div>'
            f'<div style="overflow-x:auto;">{eng_svg or "<em>No English sentence</em>"}</div></div>'
            f'<div class="aligned-tree-row"><div style="font-size:12px;font-weight:700;color:#0d9488;margin-bottom:4px;">'
            f'TR: {tur_text.record.title} ({len(tur_coords)} sent)</div>'
            f'<div style="overflow-x:auto;">{tur_svg or "<em>No Turkish sentence</em>"}</div></div>'
            f"</div>"
        )

        return {
            "pair_code": pair_code,
            "ai": alignment_idx,
            "eng_title": eng_text.record.title,
            "tur_title": tur_text.record.title,
            "eng_svg": eng_svg,
            "tur_svg": tur_svg,
            "html": combined_html,
        }
