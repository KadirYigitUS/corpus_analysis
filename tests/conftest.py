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
def real_config() -> CorpusPathConfig:
    cfg = CorpusPathConfig.from_env()
    if not cfg.translation_tsv.is_file():
        pytest.skip("thesis corpus not available")
    return cfg
