"""Concordancer (Chapter 7): Key Word In Context (KWIC) lines with configurable spans.

**KWIC.**  A *concordance* lists every occurrence of a **node** word together with the words
immediately to its left and right, aligned on the node so recurring patterns become visible at a
glance (Luhn 1960; Sinclair 1991 *Corpus, Concordance, Collocation*).  The *span* is how many
words are shown on each side; it also defines the window later used for collocation statistics.

Span options (all through :func:`resolve_span`):

=================  =======  ===============================================================
spec               (L, R)   use
=================  =======  ===============================================================
``"phrase"``       (3, 3)   idioms, fixed phrases, determiner/adjective patterns
``"collocation"``  (5, 5)   the classic collocation window (Sinclair 1991)
``"extended"``     (10, 10) semantic prosody, topical context
``"discourse"``    (20, 20) discourse-level framing
``"sentence"``     whole    full sentence of the node
``7`` / ``(5, 2)`` / ``"L5R2"``  custom symmetric or asymmetric spans (0 ≤ L, R ≤ 20)
=================  =======  ===============================================================
"""

import re
from dataclasses import dataclass, field
from typing import Literal

import numpy as np
import pandas as pd

from .lazy import LazyCorpusText
from .search import SearchResult
from .tokenview import TokenView

SPAN_PRESETS: dict[str, tuple[int, int]] = {
    "phrase": (3, 3), "collocation": (5, 5), "extended": (10, 10), "discourse": (20, 20)}
SENTENCE_SPAN = (10 ** 6, 10 ** 6)
MAX_SPAN = 20
SortKey = Literal["position", "node", "L1", "L2", "L3", "R1", "R2", "R3", "text"]


def resolve_span(span: "int | tuple[int, int] | str") -> tuple[int, int]:
    """Turn a user-friendly span spec into ``(left, right)``; see module docstring."""
    if isinstance(span, str):
        s = span.strip().lower()
        if s == "sentence":
            return SENTENCE_SPAN
        if s in SPAN_PRESETS:
            return SPAN_PRESETS[s]
        m = re.fullmatch(r"l(\d+)r(\d+)", s)
        if m:
            span = (int(m.group(1)), int(m.group(2)))
        else:
            raise ValueError(f"Unknown span '{span}'. Use a preset {sorted(SPAN_PRESETS)}, "
                             "'sentence', an int, (L, R) or 'L5R2'.")
    if isinstance(span, int):
        span = (span, span)
    left, right = int(span[0]), int(span[1])
    if not (0 <= left <= MAX_SPAN and 0 <= right <= MAX_SPAN) or left + right == 0:
        raise ValueError(f"Span sides must be 0–{MAX_SPAN} and not both 0 (got {span}).")
    return left, right


Cell = tuple[str, int]  # (surface form, filter class)


@dataclass
class KwicLine:
    """One concordance line with everything needed by every renderer."""

    code: str
    title: str
    language: str
    corpus_type: str
    focal_name: str
    ch_no: int
    p_no: int
    s_no: int
    ti: int  # 1-based token position of the node inside its sentence
    left: list[Cell]
    node: Cell
    right: list[Cell]
    sentence_tokens: list[Cell]
    node_index: int  # index of the node inside ``sentence_tokens``

    @property
    def coordinate(self) -> str:
        return f"ch {self.ch_no} · p {self.p_no} · s {self.s_no} · tok {self.ti}"

    def left_text(self) -> str:
        return " ".join(w for w, _ in self.left)

    def right_text(self) -> str:
        return " ".join(w for w, _ in self.right)


@dataclass
class ConcordanceResult:
    lines: list[KwicLine]
    span: tuple[int, int]
    view_label: str
    query_description: str
    sentence_clamped: bool
    total_hits: int = 0
    meta: dict[str, object] = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.lines)

    def sorted(self, by: SortKey = "position") -> "ConcordanceResult":
        """Return a copy sorted by node form, n-th word left/right of node, or text order."""
        def key(ln: KwicLine) -> tuple[str, ...]:
            if by == "node":
                return (ln.node[0].lower(),)
            if by[0] in "LR" and by[1:].isdigit():
                n = int(by[1:])
                side = ln.left[::-1] if by[0] == "L" else ln.right
                return (side[n - 1][0].lower() if len(side) >= n else "",)
            if by == "text":
                return (ln.code, f"{ln.ch_no:06d}{ln.p_no:06d}{ln.s_no:08d}{ln.ti:04d}")
            return ()
        if by == "position":
            return self
        out = sorted(self.lines, key=key)
        return ConcordanceResult(out, self.span, self.view_label, self.query_description,
                                 self.sentence_clamped, self.total_hits, dict(self.meta))

    def to_frame(self) -> pd.DataFrame:
        """Plain table (also what the reporter exports)."""
        return pd.DataFrame([{
            "text": ln.title, "code": ln.code, "author_translator": ln.focal_name,
            "type": ln.corpus_type, "ch": ln.ch_no, "p": ln.p_no, "s": ln.s_no, "tok": ln.ti,
            "left": ln.left_text(), "node": ln.node[0], "right": ln.right_text(),
        } for ln in self.lines])


def _cells(forms: np.ndarray, classes: np.ndarray, lo: int, hi: int) -> list[Cell]:
    return [(str(forms[i]), int(classes[i])) for i in range(lo, hi)]


def build_concordance(text: LazyCorpusText, view: TokenView, positions: np.ndarray,
                      span: tuple[int, int], sentence_clamped: bool = True,
                      max_lines: int | None = None) -> list[KwicLine]:
    """Create :class:`KwicLine` objects for ``positions`` (view indices) of one text."""
    if len(positions) == 0:
        return []
    left, right = span
    tab, sent = text.tokens, text.sentences
    forms = tab["tok"].astype(str).to_numpy()
    classes = tab["fcl"].to_numpy()
    ti_arr = tab["ti"].to_numpy()
    lo_b, hi_b = view.sentence_bounds() if sentence_clamped else (None, None)
    s_start, s_ntok = sent["start"].to_numpy(), sent["ntok"].to_numpy()
    rec = text.record
    out: list[KwicLine] = []
    use = positions if max_lines is None else positions[:max_lines]
    for p in use.tolist():
        row = int(view.rows[p])
        lo = max(p - left, int(lo_b[p]) if lo_b is not None else 0)
        hi = min(p + right, int(hi_b[p]) if hi_b is not None else len(view.rows) - 1)
        left_row = int(view.rows[lo]) if lo < p else row
        right_row = int(view.rows[hi]) if hi > p else row
        sid = int(view.sid[p])
        st, nt = int(s_start[sid]), int(s_ntok[sid])
        if lo_b is not None and lo == int(lo_b[p]):
            left_row = st  # span reaches the sentence start: include leading punctuation
        if hi_b is not None and hi == int(hi_b[p]):
            right_row = st + nt - 1  # ... or the sentence end (final '.', '?', quotes)
        out.append(KwicLine(
            code=rec.code, title=rec.title, language=rec.language,
            corpus_type=rec.corpus_type, focal_name=rec.focal_name,
            ch_no=int(sent["ch_no"].iat[sid]), p_no=int(sent["p_no"].iat[sid]),
            s_no=int(sent["s_no"].iat[sid]), ti=int(ti_arr[row]) + 1,
            left=_cells(forms, classes, left_row, row),
            node=(str(forms[row]), int(classes[row])),
            right=_cells(forms, classes, row + 1, right_row + 1),
            sentence_tokens=_cells(forms, classes, st, st + nt),
            node_index=row - st))
    return out


class Concordancer:
    """Facade: ``Concordancer().run(result, texts, span='collocation')``."""

    def run(self, result: SearchResult, texts: "list[LazyCorpusText]",
            span: "int | tuple[int, int] | str" = "collocation", sentence_clamped: bool = True,
            max_lines_per_text: int | None = 200, evict: bool = True) -> ConcordanceResult:
        """Build concordance lines for every hit of ``result`` in ``texts``."""
        q = result.query
        resolved = resolve_span(span)
        clamp = True if resolved == SENTENCE_SPAN else sentence_clamped
        lines: list[KwicLine] = []
        label = ""
        for text in texts:
            positions = result.positions(text.record.code)
            if len(positions):
                view = TokenView(text, q.field, q.filter_function_words, q.mode,
                                 case_fold=not q.case_sensitive, punct=q.punct)
                label = view.label
                lines.extend(build_concordance(text, view, positions, resolved, clamp,
                                               max_lines_per_text))
            if evict:
                text.evict()
        if not label:
            base = ("content" if q.filter_function_words else "raw") + f"/{q.field}"
            if q.punct != "drop":
                base += f"+punct_{q.punct}"
            label = base
        return ConcordanceResult(lines, resolved, label, q.describe(), clamp,
                                 total_hits=len(result))
