"""Batch KWIC (Chapter 8): enter a *list* of words, get aggregate frequency, dispersion and
association statistics between them.

Pipeline for each label (a word, or a named group of words):

1. find nodes in every text (same options as :class:`~corpus_toolkit.search.SearchQuery`);
2. normalise: ``per10k = 10 000 · hits / running words`` (so long and short texts compare);
3. split each text into ``n_chunks`` equal slices (default 10) and compute the per-chunk rate —
   the *profile* of the word across the narrative;
4. summarise: pooled ``per10k``, presence, **Juilland's D** (dispersion, 0 = clumped, 1 = even),
   and pairwise **Pearson r**, **Spearman ρ**, **cosine** between label profiles, with
   Benjamini–Hochberg FDR correction over all pairs.

Interpretation caution: the profile vectors of one text are autocorrelated (neighbouring chunks
are not independent), so p-values are *screening* devices, not confirmatory tests; the notebook
shows effect sizes first.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from itertools import combinations

import numpy as np
import pandas as pd

from .lazy import LazyCorpusText
from .search import SearchQuery, find_nodes
from .stats import benjamini_hochberg, chunk_counts, cosine, juilland_d, pearson, spearman
from .tokenview import Field, Mode, TokenView


@dataclass
class BatchKwicResult:
    labels: list[str]
    codes: list[str]
    counts: pd.DataFrame  # label × text raw hits
    rates: pd.DataFrame  # label × text per10k
    running_words: pd.Series
    chunks: dict[str, np.ndarray]  # label -> (n_texts, n_chunks) per-10k rates

    def summary(self) -> pd.DataFrame:
        """Pooled frequency, presence and dispersion per label."""
        tot_words = float(self.running_words.sum())
        rows = []
        for lab in self.labels:
            total = int(self.counts.loc[lab].sum())
            per_text = self.rates.loc[lab].to_numpy()
            chunk_d = [juilland_d(row) for row in self.chunks[lab] if row.sum() > 0]
            rows.append({
                "label": lab, "hits": total, "per10k_pooled": 1e4 * total / tot_words,
                "texts_present": int((self.counts.loc[lab] > 0).sum()),
                "D_across_texts": juilland_d(per_text),
                "D_within_text(mean)": float(np.nanmean(chunk_d)) if chunk_d else np.nan,
            })
        return pd.DataFrame(rows)

    def profile_matrix(self) -> pd.DataFrame:
        """label × (text, chunk) per10k matrix — the vectors that get correlated."""
        cols = [f"{c}#{k + 1}" for c in self.codes for k in range(next(iter(self.chunks.values())).shape[1])]
        return pd.DataFrame({lab: self.chunks[lab].ravel() for lab in self.labels},
                            index=cols).T

    def pairwise(self) -> pd.DataFrame:
        """Pearson/Spearman/cosine for every label pair + BH-FDR q-values."""
        prof = self.profile_matrix()
        rows = []
        for a, b in combinations(self.labels, 2):
            r, p = pearson(prof.loc[a], prof.loc[b])
            rho, ps = spearman(prof.loc[a], prof.loc[b])
            rows.append({"a": a, "b": b, "pearson_r": r, "p_pearson": p,
                         "spearman_rho": rho, "p_spearman": ps,
                         "cosine": cosine(prof.loc[a], prof.loc[b])})
        out = pd.DataFrame(rows)
        if len(out):
            out["q_pearson(BH)"] = benjamini_hochberg(out["p_pearson"])
            out["q_spearman(BH)"] = benjamini_hochberg(out["p_spearman"])
        return out

    def matrix(self, kind: str = "pearson_r") -> pd.DataFrame:
        """Symmetric label × label matrix of a pairwise statistic (diagonal = 1)."""
        pw = self.pairwise()
        m = pd.DataFrame(np.eye(len(self.labels)), index=self.labels, columns=self.labels)
        for _, r in pw.iterrows():
            m.loc[r["a"], r["b"]] = m.loc[r["b"], r["a"]] = r[kind]
        return m


class BatchKwicAnalyzer:
    def analyze(self, terms: "list[str] | dict[str, list[str]]",
                texts: Iterable[LazyCorpusText], field: Field = "lem", match: str = "exact",
                filter_function_words: bool = False, mode: Mode = "drop", n_chunks: int = 10,
                case_sensitive: bool = False) -> BatchKwicResult:
        groups = terms if isinstance(terms, dict) else {t: [t] for t in terms}
        labels = list(groups)
        counts: dict[str, dict[str, int]] = {lab: {} for lab in labels}
        rates: dict[str, dict[str, float]] = {lab: {} for lab in labels}
        chunk_rows: dict[str, list[np.ndarray]] = {lab: [] for lab in labels}
        words: dict[str, int] = {}
        codes: list[str] = []
        for text in texts:
            code = text.record.code
            codes.append(code)
            view = TokenView(text, field, filter_function_words, mode,
                             case_fold=not case_sensitive)
            n_run = len(view)
            words[code] = n_run
            n_pos = len(view.forms)
            elig_chunk = chunk_counts(np.flatnonzero(view.eligible), n_pos, n_chunks)
            for lab in labels:
                q = SearchQuery(groups[lab], field, match, case_sensitive,  # type: ignore[arg-type]
                                filter_function_words=filter_function_words, mode=mode)
                pos = find_nodes(view, q)
                counts[lab][code] = len(pos)
                rates[lab][code] = 1e4 * len(pos) / n_run if n_run else np.nan
                hits = chunk_counts(pos, n_pos, n_chunks)
                with np.errstate(divide="ignore", invalid="ignore"):
                    chunk_rows[lab].append(np.where(elig_chunk > 0, 1e4 * hits / elig_chunk, 0.0))
            text.evict()
        return BatchKwicResult(
            labels=labels, codes=codes,
            counts=pd.DataFrame(counts).T[codes], rates=pd.DataFrame(rates).T[codes],
            running_words=pd.Series(words)[codes],
            chunks={lab: np.vstack(chunk_rows[lab]) for lab in labels})
