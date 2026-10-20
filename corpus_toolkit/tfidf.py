"""TF-IDF keyness (Chapter 11) with scikit-learn, plus a from-scratch twin for teaching.

*Term frequency–inverse document frequency* weights a word by how often it occurs in a
document (TF) and how rare it is across documents (IDF), so words that **characterise** one text
rank high and words used everywhere (``bir``, ``the``) rank low (Spärck Jones 1972).

scikit-learn conventions used (and reproduced in :func:`tfidf_manual`):

* ``tf = 1 + ln(count)``  (``sublinear_tf=True``)  – dampens very frequent words
* ``idf = ln((1 + n) / (1 + df)) + 1``               (``smooth_idf=True``)
* each document vector is L2-normalised.

English and Turkish are fitted **separately** (different vocabularies, different morphology), and
documents can be whole texts (default) or equal-sized chunks (``n_chunks``) so that eight Turkish
novels do not make IDF degenerate.
"""

import math
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer

from .lazy import LazyCorpusText
from .tokenview import Field, Mode, PunctMode, TokenView


@dataclass
class TfidfResult:
    matrix: sparse.csr_matrix
    vocabulary: np.ndarray
    doc_ids: list[str]
    doc_labels: list[str]
    view_label: str

    def top_terms(self, doc: str, n: int = 15) -> pd.DataFrame:
        """Highest-weighted terms of one document id (code or ``code#k`` chunk)."""
        i = self.doc_ids.index(doc)
        row = self.matrix.getrow(i).toarray().ravel()
        top = np.argsort(-row)[:n]
        return pd.DataFrame({"term": self.vocabulary[top], "tfidf": row[top]})

    def dense_top(self, n_per_doc: int = 8) -> pd.DataFrame:
        """Union of each document's top terms as a dense doc × term table (for heatmaps)."""
        terms: list[str] = []
        for d in self.doc_ids:
            for t in self.top_terms(d, n_per_doc)["term"]:
                if t not in terms:
                    terms.append(t)
        idx = {t: i for i, t in enumerate(self.vocabulary)}
        cols = [idx[t] for t in terms]
        return pd.DataFrame(self.matrix[:, cols].toarray(), index=self.doc_labels, columns=terms)


class TfidfAnalyzer:
    def fit(self, texts: Iterable[LazyCorpusText], field: Field = "lem",
            filter_function_words: bool = True, mode: Mode = "drop",
            punct: PunctMode | bool = "drop", n_chunks: int = 1,
            min_df: int = 1, exclude_pos: set[str] | None = None) -> TfidfResult:
        """Fit per-document TF-IDF; ``exclude_pos={'PROPN'}`` removes character names."""
        docs: list[list[str]] = []
        ids: list[str] = []
        labels: list[str] = []
        v_label = ("content" if filter_function_words else "raw") + f"/{field}"
        for text in texts:
            view = TokenView(text, field, filter_function_words, mode, punct=punct)
            v_label = view.label
            positions = np.flatnonzero(view.eligible)
            forms = view.forms[positions].astype(str)
            if exclude_pos:
                keep = ~np.isin(view.pos_of(positions), list(exclude_pos))
                forms = forms[keep]
            parts = np.array_split(forms, n_chunks) if n_chunks > 1 else [forms]
            for k, part in enumerate(parts, 1):
                docs.append(part.tolist())
                suffix = f"#{k}" if n_chunks > 1 else ""
                ids.append(text.record.code + suffix)
                labels.append(text.record.title + suffix)
            text.evict()
        vec = TfidfVectorizer(analyzer=lambda x: x, sublinear_tf=True, smooth_idf=True,
                              norm="l2", min_df=min_df)
        matrix = vec.fit_transform(docs)
        return TfidfResult(matrix.tocsr(), np.asarray(vec.get_feature_names_out()), ids, labels,
                           v_label)


def tfidf_manual(docs: list[list[str]]) -> pd.DataFrame:
    """The same weights as scikit-learn, computed by hand (doc × term DataFrame)."""
    n = len(docs)
    vocab = sorted({w for d in docs for w in d})
    doc_sets = [set(d) for d in docs]
    df = {w: sum(w in s for s in doc_sets) for w in vocab}
    idf = {w: math.log((1 + n) / (1 + df[w])) + 1 for w in vocab}
    rows = []
    for d in docs:
        cnt = Counter(d)
        vec = np.array([(1 + math.log(cnt[w])) * idf[w] if cnt[w] > 0 else 0.0 for w in vocab])
        norm = np.linalg.norm(vec)
        rows.append(vec / norm if norm else vec)
    return pd.DataFrame(rows, columns=vocab)

