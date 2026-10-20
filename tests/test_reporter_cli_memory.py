"""Reporter output layout, batch KWIC counts, CLI parser and the < 3.5 GB memory gate."""

import resource

import matplotlib
import pandas as pd
import pytest

matplotlib.use("Agg")

from corpus_toolkit.batch_kwic import BatchKwicAnalyzer  # noqa: E402
from corpus_toolkit.cli import build_parser  # noqa: E402
from corpus_toolkit.config import CorpusPathConfig  # noqa: E402
from corpus_toolkit.loader import CorpusLoader  # noqa: E402
from corpus_toolkit.reporter import CorpusReporter, slug  # noqa: E402


def test_slug():
    assert slug("Ben, Robot / 1983!") == "ben_robot_1983"


def test_reporter_writes_into_separate_dirs(tmp_path):
    cfg = CorpusPathConfig(data_root=tmp_path)
    rep = CorpusReporter(cfg, run_name="unit test")
    rep.note(view="content", span="L5R2")
    rep.add_section("Toy", "hello")
    rep.add_table("toy table", pd.DataFrame({"a": [1, 2], "b": [0.5, 0.25]}))
    rep.add_summary("a sums to 3.")
    path = rep.finalize(xlsx=False)
    text = path.read_text(encoding="utf-8")
    assert path.parent == cfg.reports_dir
    assert "view: `content`" in text and "a sums to 3." in text
    assert list(cfg.tables_dir.glob("unit_test_*_toy_table.tsv"))


def test_batch_kwic_counts(mini_text):
    res = BatchKwicAnalyzer().analyze(["cat", "dog", "saw"], [mini_text], "tok", n_chunks=2)
    counts = res.counts[mini_text.record.code]
    assert counts["cat"] == 2 and counts["dog"] == 2 and counts["saw"] == 2
    assert res.chunks["cat"].shape == (1, 2)


def test_cli_parser_accepts_documented_commands():
    ap = build_parser()
    assert ap.parse_args(["search", "robot", "--span", "L5R2", "--content"]).span == "L5R2"
    assert ap.parse_args(["collocate", "robot", "--text", "BR-SM"]).sort == "G2"
    assert ap.parse_args(["cache", "info"]).action == "info"
    with pytest.raises(SystemExit):
        ap.parse_args(["nonsense"])


@pytest.mark.data
def test_peak_rss_below_gate(real_config):
    """Stream all 13 texts one by one (evicting) — the process must stay under 3.5 GB."""
    loader = CorpusLoader(cache_policy="keep", verbose=False)
    for text in loader.load_all():
        _ = text.tokens
        text.evict()
    peak_gb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 / 1024  # kB → GB
    assert peak_gb < 3.5
