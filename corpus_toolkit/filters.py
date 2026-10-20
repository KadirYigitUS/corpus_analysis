"""Function-word classification (vendored from ``passim_analysis`` ``UposFilterService``).

Each token falls into exactly one of three classes:

``CONTENT``   open-class words (NOUN, VERB, ADJ, ADV, PROPN, NUM, X)
``FUNCTION``  closed-class words (DET, PRON, CCONJ, ADP, AUX, SCONJ, INTJ, PART)
``PUNCT``     punctuation and symbols (PUNCT, SYM) -- never counted in any denominator

Turkish additionally applies a *morphological head guard*: a statistical tagger may tag a
postposition or determiner as ADV/NOUN, so a token whose Oflazer-style analysis head
(``morph.split('+')[1]``) is in ``TURKISH_FUNCTION_MORPH_HEADS`` is function-class.
English uses UPOS only (its ``morph`` strings are UD features, not Oflazer analyses).
"""

import numpy as np

from .textutil import LANG_TR

CONTENT = 0
FUNCTION = 1
PUNCT = 2
CLASS_NAMES = {CONTENT: "content", FUNCTION: "function", PUNCT: "punct"}

PUNCT_UPOS = frozenset({"PUNCT", "SYM"})
FUNCTION_UPOS = frozenset({"DET", "PRON", "CCONJ", "ADP", "AUX", "SCONJ", "INTJ", "PART"})
CONTENT_UPOS = frozenset({"NOUN", "VERB", "ADJ", "ADV", "PROPN", "NUM", "X"})
TURKISH_FUNCTION_MORPH_HEADS = frozenset(
    {"Postp", "Conj", "Det", "Pron", "Ques", "Interj", "Punc"}
)


def morph_head(morph: str) -> str:
    """Primary tag of an Oflazer analysis: ``'gel+Verb+Pos'`` -> ``'Verb'``."""
    parts = str(morph).split("+")
    return parts[1] if len(parts) > 1 else ""


def classify_token(pos: str, morph: str, language: str) -> int:
    """Return ``CONTENT`` / ``FUNCTION`` / ``PUNCT`` for a single token."""
    if pos in PUNCT_UPOS:
        return PUNCT
    if pos in FUNCTION_UPOS:
        return FUNCTION
    if language == LANG_TR and morph_head(morph) in TURKISH_FUNCTION_MORPH_HEADS:
        return PUNCT if morph_head(morph) == "Punc" else FUNCTION
    return CONTENT


def classify_arrays(pos: np.ndarray, morph: np.ndarray, language: str) -> np.ndarray:
    """Vectorised :func:`classify_token` -> ``int8`` array (memory-light)."""
    out = np.empty(len(pos), dtype=np.int8)
    for i in range(len(pos)):
        out[i] = classify_token(pos[i], morph[i], language)
    return out


def view_label(filter_function_words: bool) -> str:
    """Name of the analysis view: ``'content'`` (function words off) or ``'raw'``."""
    return "content" if filter_function_words else "raw"
