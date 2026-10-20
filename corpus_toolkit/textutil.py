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


_ALNUM_CHUNK_RE = re.compile(r"[^\W_]+", re.UNICODE)


def strip_in_token_punct(token: str) -> str:
    """Remove in-token punctuation by collapsing constituent characters (Passim style).

    In Turkish NLP (VNLP), tokens like ``Türkiye'nin``, ``Fred'``, ``robot-bilim`` retain
    punctuation inside the token or lemma.  Stripping punctuation collapses them into
    single alphanumeric units without splitting.

    Examples:
        >>> strip_in_token_punct("Türkiye'nin")
        'Türkiyenin'
        >>> strip_in_token_punct("Fred'")
        'Fred'
        >>> strip_in_token_punct("robot-bilim")
        'robotbilim'
        >>> strip_in_token_punct("sn'lik")
        'snlik'
        >>> strip_in_token_punct("1882'")
        '1882'
        >>> strip_in_token_punct("-")
        ''
    """
    return "".join(ch for ch in token if ch.isalnum())


def split_in_token_punct(token: str) -> list[str]:
    """Decompose a composite token on punctuation into constituent word tokens (Passim retokenizer style).

    Uses the Passim regex ``re.findall(r"[^\\W_]+", token)`` to decompose composite words
    (hyphens, slashes, apostrophes) into separate sub-tokens, discarding standalone
    punctuation.

    Examples:
        >>> split_in_token_punct("Türkiye'nin")
        ['Türkiye', 'nin']
        >>> split_in_token_punct("Fred'")
        ['Fred']
        >>> split_in_token_punct("robot-bilim")
        ['robot', 'bilim']
        >>> split_in_token_punct("sn'lik")
        ['sn', 'lik']
        >>> split_in_token_punct("1882'")
        ['1882']
        >>> split_in_token_punct("-")
        []
    """
    return [part for part in _ALNUM_CHUNK_RE.findall(token) if part.isalnum()]


_APOSTROPHE_SPLIT_RE = re.compile(r"['’‘`´ʼʻ]", re.UNICODE)


def clean_lemma(lemma: str, language: str = LANG_TR) -> str:
    """Normalize a lemmatized token by removing sections after an apostrophe (VNLP kesme işareti remediation).

    In Turkish NLP (VNLP), proper nouns, hyphenated compounds, and suffixed terms often retain
    the apostrophe and trailing inflectional suffix in the lemma field (e.g. raw VNLP lemma
    for token ``Türkiye'nin`` is left as ``Türkiye'nin``, ``bilim-kurgu'nun`` as ``bilim-kurgu'nun``,
    ``Fred'`` as ``Fred'``, ``ay'da`` as ``ay'da``, ``1882'de`` as ``1882'de``).


    This function strips the apostrophe and all trailing characters from the lemma, returning
    the true base stem (e.g. ``Türkiye``, ``bilim-kurgu``, ``Fred``, ``ay``, ``1882``).
    Tokens consisting entirely of punctuation or beginning with an apostrophe (e.g. ``'``)
    are preserved intact.

    Examples:
        >>> clean_lemma("Türkiye'nin")
        'Türkiye'
        >>> clean_lemma("türkiye'nin")
        'türkiye'
        >>> clean_lemma("bilim-kurgu'nun")
        'bilim-kurgu'
        >>> clean_lemma("Fred'")
        'Fred'
        >>> clean_lemma("ay'da")
        'ay'
        >>> clean_lemma("1882'de")
        '1882'
        >>> clean_lemma("1882'")
        '1882'
        >>> clean_lemma("'")
        "'"
    """
    if not lemma:
        return lemma
    if language == LANG_TR:
        m = _APOSTROPHE_SPLIT_RE.search(lemma)
        if m:
            cut = lemma[: m.start()]
            if cut:
                return cut
    return lemma


def clean_lemmas(lemmas: list[str], language: str = LANG_TR) -> list[str]:
    """Apply :func:`clean_lemma` across a list of lemmatized strings."""
    if language != LANG_TR:
        return list(lemmas)
    return [clean_lemma(lm, language) for lm in lemmas]

