"""Dependency-tree visualiser (Chapter 5) in spaCy's *displaCy* style, for English and Turkish.

**What is a dependency tree?**  Each word (the *dependent*) is attached to exactly one *head*
with a labelled relation (Tesnière 1959; Nivre et al. 2016).  The sentence root has head ``0``.
Arcs are drawn above the sentence; the arrow points from head to dependent.

**How other tools show it.**  VNLP's Turkish ``DependencyParser`` returns plain tuples
``(index, word, head_index, label)`` and documents no built-in tree renderer; we therefore (1) offer the same
tuples as a table (:meth:`DependencyVisualizer.table`) *and* (2) render spaCy-style SVG by feeding
``displacy.render(..., manual=True)`` — no spaCy model is required.

**Design choices.**  Function words are *dimmed*, never deleted, so the tree stays connected;
English ClearNLP/spaCy labels can be mapped to UD names (label-only: attachment structure still
differs, e.g. English prepositions head their objects); long sentences scroll horizontally;
1:N / N:1 aligned groups are drawn as stacked trees.
"""

import re
from typing import Any

import pandas as pd

from .errors import CorpusSelectionError
from .filters import FUNCTION
from .lazy import LazyCorpusText
from .style import CSS, badge, esc

#: English (ClearNLP/spaCy) → Universal Dependencies label names (label-only mapping).
EN_TO_UD = {
    "ROOT": "root", "dobj": "obj", "nsubjpass": "nsubj:pass", "csubjpass": "csubj:pass",
    "auxpass": "aux:pass", "relcl": "acl:relcl", "npadvmod": "obl:npmod", "agent": "obl:agent",
    "dative": "iobj", "poss": "nmod:poss", "quantmod": "advmod", "neg": "advmod",
    "meta": "discourse", "intj": "discourse", "predet": "det:predet", "prt": "compound:prt",
    "acomp": "xcomp", "oprd": "xcomp",
}

_TOKEN_TAG = re.compile(r'<text class="displacy-token"')


def _dim_tokens(svg: str, dim_indices: set[int]) -> str:
    """Add ``opacity`` to the n-th ``displacy-token`` text nodes (function words)."""
    counter = {"i": -1}

    def repl(match: "re.Match[str]") -> str:
        counter["i"] += 1
        return match.group(0) + (' style="opacity:0.4"' if counter["i"] in dim_indices else "")

    return _TOKEN_TAG.sub(repl, svg)


def displacy_payload(words: list[str], pos: list[str], heads: list[int], rels: list[str],
                     language: str, normalize_labels: bool = True) -> dict[str, Any]:
    """Build the manual displaCy dict (words + arcs).  ``heads`` are 1-based, 0 = root."""
    arcs = []
    n = len(words)
    for i, (h, rel) in enumerate(zip(heads, rels)):
        if h == 0 or h > n or h - 1 == i:  # root, out-of-range or self-attached: no arc
            continue
        label = EN_TO_UD.get(rel, rel) if (normalize_labels and language == "en") else rel
        dep_i, head_i = i, h - 1
        arcs.append({"start": min(dep_i, head_i), "end": max(dep_i, head_i), "label": label,
                     "dir": "left" if dep_i < head_i else "right"})
    return {"words": [{"text": w, "tag": p} for w, p in zip(words, pos)], "arcs": arcs}


def render_svg(payload: dict[str, Any], dim: set[int] | None = None, compact: bool = False,
               distance: int = 105) -> str:
    """Render one tree to SVG with spaCy's displaCy (``manual=True``)."""
    from spacy import displacy

    svg = displacy.render(payload, style="dep", manual=True, jupyter=False,
                          options={"compact": compact, "distance": distance, "bg": "#ffffff",
                                   "color": "#1e293b", "font": "Helvetica, Arial, sans-serif",
                                   "word_spacing": 38, "arrow_spacing": 10})
    return _dim_tokens(svg, dim or set())


class DependencyVisualizer:
    """Render sentences of any loaded text; understands hits, coordinates and alignments."""

    def __init__(self, loader: Any) -> None:
        self.loader = loader

    # ---------------------------------------------------------------- lookup
    @staticmethod
    def sid_of(text: LazyCorpusText, coord: tuple[int, int, int]) -> int:
        s = text.sentences
        mask = ((s["ch_no"] == coord[0]) & (s["p_no"] == coord[1]) & (s["s_no"] == coord[2]))
        hit = s.index[mask]
        if len(hit) == 0:
            raise CorpusSelectionError(f"Sentence {coord} not found in {text.record.code}.")
        return int(hit[0])

    @staticmethod
    def _slice(text: LazyCorpusText, sid: int) -> pd.DataFrame:
        s = text.sentences
        start, n = int(s["start"].iat[sid]), int(s["ntok"].iat[sid])
        return text.tokens.iloc[start:start + n]

    def table(self, text: LazyCorpusText, sid: int) -> pd.DataFrame:
        """VNLP-style tuples plus lemma/UPOS and the head word (1-based indices)."""
        t = self._slice(text, sid).reset_index(drop=True)
        words = t["tok"].astype(str).tolist()
        heads = t["head"].astype(int).tolist()
        return pd.DataFrame({
            "idx": range(1, len(t) + 1), "word": words, "lemma": t["lem"].astype(str),
            "upos": t["pos"].astype(str), "head": heads,
            "head_word": [words[h - 1] if h > 0 else "ROOT" for h in heads],
            "deprel": t["rel"].astype(str)})

    # --------------------------------------------------------------- render
    def svg(self, text: LazyCorpusText, sid: int, dim_function_words: bool = True,
            normalize_labels: bool = True, compact: bool = False, drop_punct_arcs: bool = False
            ) -> str:
        t = self._slice(text, sid).reset_index(drop=True)
        words, pos = t["tok"].astype(str).tolist(), t["pos"].astype(str).tolist()
        heads, rels = t["head"].astype(int).tolist(), t["rel"].astype(str).tolist()
        if drop_punct_arcs:
            heads = [0 if r == "punct" else h for h, r in zip(heads, rels)]
        payload = displacy_payload(words, pos, heads, rels, text.record.language,
                                   normalize_labels)
        dim = {i for i, c in enumerate(t["fcl"].tolist()) if c == FUNCTION} \
            if dim_function_words else set()
        return render_svg(payload, dim, compact)

    def html(self, text: LazyCorpusText, sid: int, **kw: Any) -> str:
        s = text.sentences
        coord = f"ch {int(s['ch_no'].iat[sid])} · p {int(s['p_no'].iat[sid])} · " \
                f"s {int(s['s_no'].iat[sid])}"
        head = (f"{badge(text.record.corpus_type)} <b>{esc(text.record.title)}</b> "
                f"<span class='chip'>{coord}</span>")
        return (f"<div class='card'><div class='head'>{head}</div>"
                f"<div style='overflow-x:auto'>{self.svg(text, sid, **kw)}</div></div>")

    def alignment_html(self, code: str, ai: int, **kw: Any) -> str:
        """Stacked trees of an aligned group: every English sentence, then every Turkish one."""
        rec = self.loader.registry.resolve_text(code)
        if not rec.pair_id:
            raise CorpusSelectionError(f"{rec.code} has no aligned counterpart.")
        pair = self.loader.registry.pairs[rec.pair_id]
        idx = self.loader.alignment_index(pair)
        eng_c, tur_c = idx.coords(ai)
        parts: list[str] = [f"<div class='meta'>Aligned group <b>{ai}</b>: "
                            f"{len(eng_c)} English ⇄ {len(tur_c)} Turkish sentence(s)</div>"]
        for text, coords in ((self.loader.load_text(pair.eng.code), eng_c),
                             (self.loader.load_text(pair.tur.code), tur_c)):
            for c in coords:
                parts.append(self.html(text, self.sid_of(text, tuple(c)), **kw))
            text.evict()
        return "<div class='ct'>" + "".join(parts) + "</div>"

    def show(self, code: str, coord: tuple[int, int, int] | None = None, sid: int | None = None,
             **kw: Any) -> None:
        """Display one sentence tree in a notebook (coordinate ``(ch, p, s)`` or ``sid``)."""
        from IPython.display import HTML, display

        text = self.loader.load_text(code)
        use = sid if sid is not None else self.sid_of(text, coord or (1, 1, 1))
        display(HTML(CSS + "<div class='ct'>" + self.html(text, use, **kw) + "</div>"))
        text.evict()
