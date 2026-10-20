"""Test configuration: headless matplotlib, non-interactive cache policy, isolated data dir."""

import lzma
import os
import pickle
from pathlib import Path

import pandas as pd
import pytest

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ["CORPUS_CACHE_POLICY"] = "keep"

from corpus_toolkit.cache import CorpusCacheManager  # noqa: E402
from corpus_toolkit.config import CorpusPathConfig  # noqa: E402
from corpus_toolkit.lazy import LazyCorpusText  # noqa: E402
from corpus_toolkit.registry import SOURCE, TextRecord  # noqa: E402


def _sentence_row(ch: int, p: int, s: int, toks: list[str], pos: list[str],
                  heads: list[int], rels: list[str]) -> dict[str, object]:
    return {
        "ch_no": ch, "p_no": p, "s_no": s, "sentence": " ".join(toks),
        "tokens": str(toks), "lemma": str([t.lower() for t in toks]), "pos": str(pos),
        "morph": str(["" for _ in toks]), "ner": str(["O" for _ in toks]),
        "dep": str(list(zip(heads, rels))),
    }


@pytest.fixture()
def mini_text(tmp_path: Path) -> LazyCorpusText:
    """Two English sentences: 'The cat saw the dog .' / 'The dog saw the cat .'"""
    pos = ["DET", "NOUN", "VERB", "DET", "NOUN", "PUNCT"]
    heads = [2, 3, 0, 5, 3, 3]
    rels = ["det", "nsubj", "root", "det", "obj", "punct"]
    rows = [
        _sentence_row(1, 1, 1, ["The", "cat", "saw", "the", "dog", "."], pos, heads, rels),
        _sentence_row(1, 1, 2, ["The", "dog", "saw", "the", "cat", "."], pos, heads, rels),
    ]
    path = tmp_path / "T-EN.pickle.xz"
    with lzma.open(path, "wb") as fh:
        pickle.dump(pd.DataFrame(rows), fh)
    rec = TextRecord(code="T-EN", language="en", corpus_type=SOURCE, title="Cat Book",
                     creator="Test Author", year=2000, focal_code="SM",
                     focal_name="Selma Mine", pickle_path=path)
    return LazyCorpusText(rec, CorpusCacheManager(tmp_path / "cache"))


@pytest.fixture()
def turkish_mini_text(tmp_path: Path) -> LazyCorpusText:
    """Two Turkish sentences containing VNLP in-token and in-lemma punctuation."""
    rows = [
        {
            "ch_no": 1, "p_no": 1, "s_no": 1,
            "sentence": "Türkiye'nin robot-bilim uzmanı Fred' geldi .",
            "tokens": str(["Türkiye'nin", "robot-bilim", "uzmanı", "Fred'", "geldi", "."]),
            "lemma": str(["türkiye'nin", "robot-bilim", "uzman", "fred'", "gel", "."]),
            "pos": str(["PROPN", "NOUN", "NOUN", "PROPN", "VERB", "PUNCT"]),
            "morph": str(["" for _ in range(6)]),
            "ner": str(["B-LOC", "O", "O", "B-PER", "O", "O"]),
            "dep": str([(5, "nmod"), (3, "nmod"), (4, "nmod"), (5, "nsubj"), (0, "root"), (5, "punct")]),
        },
        {
            "ch_no": 1, "p_no": 1, "s_no": 2,
            "sentence": "Ay'da 1882'de ne gördü ?",
            "tokens": str(["Ay'da", "1882'de", "ne", "gördü", "?"]),
            "lemma": str(["ay'da", "1882'", "ne", "gör", "?"]),
            "pos": str(["PROPN", "NUM", "PRON", "VERB", "PUNCT"]),
            "morph": str(["" for _ in range(5)]),
            "ner": str(["B-LOC", "B-DATE", "O", "O", "O"]),
            "dep": str([(4, "obl"), (4, "obl"), (4, "obj"), (0, "root"), (4, "punct")]),
        },
    ]
    path = tmp_path / "T-TR.pickle.xz"
    with lzma.open(path, "wb") as fh:
        pickle.dump(pd.DataFrame(rows), fh)
    rec = TextRecord(code="T-TR", language="tr", corpus_type=SOURCE, title="Robot Kitabı",
                     creator="Zühtü Bayar", year=1980, focal_code="ZB",
                     focal_name="Zühtü Bayar", pickle_path=path)
    return LazyCorpusText(rec, CorpusCacheManager(tmp_path / "cache_tr"))


@pytest.fixture()
def real_config() -> CorpusPathConfig:
    cfg = CorpusPathConfig.from_env()
    if not cfg.translation_tsv.is_file():
        pytest.skip("thesis corpus not available")
    return cfg
