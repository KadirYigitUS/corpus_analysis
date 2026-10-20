"""NLTK bridge: the classic toolbox applied to our analysis views.

The toolkit's own concordancer/collocation code is the *teaching implementation*; NLTK is the
reference everyone knows, so this adapter lets students cross-check results (Chapter 7/10)
and use ``nltk.Text`` conveniences (``similar``, ``dispersion``, ``ngrams``).
"""

from collections import Counter

import nltk
import pandas as pd
from nltk.collocations import BigramAssocMeasures, BigramCollocationFinder
from nltk.text import ContextIndex

from .tokenview import TokenView


def as_nltk_text(view: TokenView) -> nltk.Text:
    """``nltk.Text`` over the eligible forms of a view (name = text title + view label)."""
    return nltk.Text(view.analysed().astype(str).tolist(),
                     name=f"{view.text.record.title} [{view.label}]")


def freq_dist(view: TokenView) -> nltk.FreqDist:
    return nltk.FreqDist(view.analysed().astype(str).tolist())


def nltk_concordance(view: TokenView, word: str, width: int = 60, lines: int = 10) -> list[str]:
    """NLTK's own concordance lines (a *different* algorithm: no sentence clamping)."""
    text = as_nltk_text(view)
    return [f"{c.left_print:>{width // 2}} {c.query} {c.right_print:<{width // 2}}"
            for c in text.concordance_list(word, width=width, lines=lines)]


def nltk_similar(view: TokenView, word: str, n: int = 10) -> list[str]:
    """Words sharing the most left/right contexts with ``word`` (distributional similarity)."""
    idx = ContextIndex(view.analysed().astype(str).tolist())
    return list(idx.similar_words(word, n))


def nltk_collocations(view: TokenView, n: int = 15, min_freq: int = 3,
                      measure: str = "likelihood_ratio", window: int = 2) -> pd.DataFrame:
    """Bigram collocations scored with an NLTK association measure (``pmi``/``likelihood_ratio``)."""
    finder = BigramCollocationFinder.from_words(view.analysed().astype(str).tolist(),
                                                window_size=window)
    finder.apply_freq_filter(min_freq)
    scorer = getattr(BigramAssocMeasures, measure)
    rows = [{"bigram": " ".join(b), measure: s} for b, s in finder.score_ngrams(scorer)[:n]]
    return pd.DataFrame(rows)


def top_ngrams(view: TokenView, n: int = 2, top: int = 15) -> pd.DataFrame:
    """Most frequent word n-grams (``n=2`` bigrams, ``n=3`` trigrams, ...)."""
    grams = Counter(nltk.ngrams(view.analysed().astype(str).tolist(), n))
    return pd.DataFrame([{"ngram": " ".join(g), "freq": c} for g, c in grams.most_common(top)])


def dispersion_points(view: TokenView, words: list[str]) -> dict[str, list[float]]:
    """Relative positions (0–1) of each word across the text — data for a dispersion plot."""
    forms = view.analysed().astype(str)
    n = max(len(forms), 1)
    out: dict[str, list[float]] = {}
    for w in words:
        out[w] = [i / n for i in range(len(forms)) if forms[i] == w.lower()]
    return out
