"""Small text helpers shared by every module.

Turkish needs special care when case-folding: Python's ``str.lower()`` maps ``I`` to
``i`` and ``İ`` to ``i̇`` (two code points), whereas Turkish maps ``I`` -> ``ı`` and
``İ`` -> ``i``.  Counting *types* (Chapter 9) or matching a query (Chapter 6) with the
wrong rule silently merges or splits word forms, so every module goes through here.
"""

import re
import unicodedata

LANG_EN = "en"
LANG_TR = "tr"

_TR_UPPER_TO_LOWER = str.maketrans({"I": "ı", "İ": "i"})
_WORD_RE = re.compile(r"\w", re.UNICODE)


def fold(text: str, language: str) -> str:
    """Lower-case ``text`` following the rules of ``language`` (``'en'`` or ``'tr'``)."""
    if language == LANG_TR:
        return unicodedata.normalize("NFC", text.translate(_TR_UPPER_TO_LOWER)).lower()
    return text.lower()


def turkish_lower(text: str) -> str:
    """Turkish-aware lower-casing (``İstanbul`` -> ``istanbul``, ``ISIK`` -> ``ısık``)."""
    return fold(text, LANG_TR)


def loose_key(text: str) -> str:
    """Diacritic- and case-insensitive key (``Zühtü`` -> ``zuhtu``) for forgiving lookups."""
    decomposed = unicodedata.normalize("NFKD", turkish_lower(text).replace("ı", "i"))
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub(r"[^0-9a-z]+", " ", stripped).strip()


def is_wordlike(token: str) -> bool:
    """True when ``token`` contains at least one letter/digit (i.e. is not punctuation)."""
    return bool(_WORD_RE.search(token))
