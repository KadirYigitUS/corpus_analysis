"""Analysis *views* over a text: tokens vs. lemmas, raw vs. content, drop vs. mask.

Every statistic in the toolkit is computed on a :class:`TokenView`, which answers three
questions the student must always be able to state explicitly:

1. **Which field?**  ``field='tok'`` (surface forms) or ``'lem'`` (lemmas).
2. **Are function words removed?**  ``filter_function_words=True`` gives the *content* view
   (Passim ``UposFilterService`` rules, see :mod:`corpus_toolkit.filters`); ``False`` is *raw*.
3. **How are windows counted when they are removed?**  ``mode='drop'`` deletes them from the
   sequence (a ±5 span then means five *content* words); ``mode='mask'`` keeps them in the
   sequence so spans stay in running words, but they can no longer be a node or collocate.

Punctuation is never part of any view (it would inflate every denominator).
"""

from dataclasses import dataclass
from dataclasses import field as dc_field
from typing import Literal

import numpy as np
import pandas as pd

from .filters import CONTENT, PUNCT
from .lazy import LazyCorpusText
from .textutil import fold, split_in_token_punct, strip_in_token_punct

Field = Literal["tok", "lem"]
Mode = Literal["drop", "mask"]
PunctMode = Literal["keep", "drop", "strip", "split"]


@dataclass
class TokenView:
    """Immutable-ish snapshot of the positions/forms analysed for one text."""

    text: LazyCorpusText
    field: Field = "tok"
    filter_function_words: bool = False
    mode: Mode = "drop"
    case_fold: bool = True
    punct: PunctMode | bool = "drop"
    rows: np.ndarray = dc_field(init=False, repr=False)  # token-table row of each position
    forms: np.ndarray = dc_field(init=False, repr=False)  # analysed string at each position
    eligible: np.ndarray = dc_field(init=False, repr=False)  # may be node/collocate/type?
    sid: np.ndarray = dc_field(init=False, repr=False)  # sentence index of each position

    def __post_init__(self) -> None:
        if self.field not in ("tok", "lem"):
            raise ValueError("field must be 'tok' or 'lem'")
        if self.mode not in ("drop", "mask"):
            raise ValueError("mode must be 'drop' or 'mask'")
        if isinstance(self.punct, bool):
            self.punct = "keep" if self.punct else "drop"
        if self.punct not in ("keep", "drop", "strip", "split"):
            raise ValueError("punct must be 'keep', 'drop', 'strip', or 'split'")
        tab = self.text.tokens
        fcl = tab["fcl"].to_numpy()
        if self.punct == "keep":
            if self.filter_function_words and self.mode == "drop":
                keep = fcl == CONTENT
            else:
                keep = np.ones(len(fcl), dtype=bool)
        else:
            non_punct = fcl != PUNCT
            if self.filter_function_words and self.mode == "drop":
                keep = fcl == CONTENT
            else:
                keep = non_punct
        self.rows = np.flatnonzero(keep)
        if self.filter_function_words and self.mode == "mask":
            self.eligible = fcl[self.rows] == CONTENT
        else:
            self.eligible = np.ones(len(self.rows), dtype=bool)
        col = tab[self.field]
        cats = col.cat.categories
        lang = self.text.record.language
        folded = np.asarray([fold(str(c), lang) if self.case_fold else str(c) for c in cats],
                            dtype=object)
        base_forms = folded[col.cat.codes.to_numpy()[self.rows]]
        base_sid = tab["sid"].to_numpy()[self.rows]

        if self.punct in ("keep", "drop"):
            self.forms = base_forms
            self.sid = base_sid
        elif self.punct == "strip":
            new_forms: list[str] = []
            valid_idx: list[int] = []
            for i, f in enumerate(base_forms):
                s = strip_in_token_punct(str(f))
                if s:
                    new_forms.append(s)
                    valid_idx.append(i)
            self.forms = np.asarray(new_forms, dtype=object)
            self.rows = self.rows[valid_idx]
            self.eligible = self.eligible[valid_idx]
            self.sid = base_sid[valid_idx]
        elif self.punct == "split":
            new_forms_list: list[str] = []
            new_rows: list[int] = []
            new_elig: list[bool] = []
            new_sid: list[int] = []
            for i, f in enumerate(base_forms):
                parts = split_in_token_punct(str(f))
                if not parts:
                    continue
                r_val = int(self.rows[i])
                e_val = bool(self.eligible[i])
                s_val = int(base_sid[i])
                for p in parts:
                    new_forms_list.append(p)
                    new_rows.append(r_val)
                    new_elig.append(e_val)
                    new_sid.append(s_val)
            self.forms = np.asarray(new_forms_list, dtype=object)
            self.rows = np.asarray(new_rows, dtype=np.int64)
            self.eligible = np.asarray(new_elig, dtype=bool)
            self.sid = np.asarray(new_sid, dtype=np.int64)

    # ----------------------------------------------------------------- stats
    @property
    def label(self) -> str:
        base = ("content" if self.filter_function_words else "raw") + f"/{self.field}"
        if self.punct != "drop":
            base += f"+punct_{self.punct}"
        return base

    def analysed(self) -> np.ndarray:
        """Forms of the *eligible* positions (the 'running words' of this view)."""
        return self.forms[self.eligible]

    def __len__(self) -> int:
        return int(self.eligible.sum())

    def freq(self) -> pd.Series:
        """Frequency list (descending) of eligible forms."""
        vals, counts = np.unique(self.analysed().astype(str), return_counts=True)
        return pd.Series(counts, index=vals, name="freq").sort_values(ascending=False,
                                                                    kind="mergesort")

    def pos_of(self, positions: np.ndarray) -> np.ndarray:
        """UPOS tag for given view positions."""
        return self.text.tokens["pos"].to_numpy()[self.rows[positions]].astype(str)

    def sentence_bounds(self) -> tuple[np.ndarray, np.ndarray]:
        """For every position, the first and last position of its sentence (inclusive).

        Used for *sentence-clamped* windows: a span never crosses a sentence boundary.
        """
        n = len(self.sid)
        if n == 0:
            return np.empty(0, dtype=np.int64), np.empty(0, dtype=np.int64)
        change = np.flatnonzero(np.diff(self.sid)) + 1
        starts = np.concatenate([[0], change])
        ends = np.concatenate([change - 1, [n - 1]])
        lens = ends - starts + 1
        return np.repeat(starts, lens), np.repeat(ends, lens)

    def occurrences(self, nodes: "list[str] | tuple[str, ...]") -> np.ndarray:
        """Positions of eligible tokens whose analysed form is one of ``nodes`` (folded)."""
        lang = self.text.record.language
        wanted: set[str] = set()
        for n in nodes:
            w = fold(n, lang) if self.case_fold else n
            if self.punct == "strip":
                s = strip_in_token_punct(w)
                if s:
                    wanted.add(s)
            elif self.punct == "split":
                for part in split_in_token_punct(w):
                    wanted.add(part)
            else:
                wanted.add(w)
        mask = np.isin(self.forms, list(wanted)) & self.eligible
        return np.flatnonzero(mask)
