"""Cached high-level workflows shared by the notebook and the command-line interface.

Each function evicts texts after use (memory-safe) and stores small results in the on-disk cache
so a second call with the same options returns instantly.
"""

from collections.abc import Iterable

import numpy as np
import pandas as pd

from .cache import file_signature
from .diversity import diversity_metrics, mattr_series, rank_frequency
from .lazy import LazyCorpusText
from .loader import CorpusLoader
from .tokenview import Field, Mode, PunctMode, TokenView


def _label(text: LazyCorpusText) -> str:
    r = text.record
    return f"{r.code} · {r.title}"


def diversity_for(loader: CorpusLoader, texts: Iterable[LazyCorpusText], field: Field = "lem",
                  filter_function_words: bool = False, mode: Mode = "drop",
                  punct: PunctMode | bool = "drop") -> pd.DataFrame:
    """Lexical-diversity table (rows = texts, columns = metrics), cached per text."""
    rows: dict[str, dict[str, float]] = {}
    p_norm = ("keep" if punct else "drop") if isinstance(punct, bool) else punct
    for t in texts:
        key = loader.cache.key("div", t.record.code, file_signature(t.record.pickle_path),
                               field, filter_function_words, mode, p_norm)
        res = loader.cache.load_json(key)
        if res is None:
            res = diversity_metrics(TokenView(t, field, filter_function_words, mode,
                                              punct=p_norm).analysed())
            loader.cache.save_json(key, res)
        rows[_label(t)] = res
        t.evict()
    return pd.DataFrame(rows).T


def mattr_trajectories_for(texts: Iterable[LazyCorpusText], window: int = 100,
                           field: Field = "lem", filter_function_words: bool = False,
                           punct: PunctMode | bool = "drop") -> dict[str, np.ndarray]:
    out: dict[str, np.ndarray] = {}
    for t in texts:
        out[t.record.code] = mattr_series(
            TokenView(t, field, filter_function_words, punct=punct).analysed(), window)
        t.evict()
    return out


def zipf_for(texts: Iterable[LazyCorpusText], field: Field = "lem",
             filter_function_words: bool = False,
             punct: PunctMode | bool = "drop") -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    for t in texts:
        out[t.record.code] = rank_frequency(
            TokenView(t, field, filter_function_words, punct=punct).analysed())
        t.evict()
    return out


def standard_report(loader: CorpusLoader, run_name: str = "standard", field: Field = "lem",
                    filter_function_words: bool = False,
                    punct: PunctMode | bool = "drop") -> "object":
    """Inventory + alignment + POS + diversity report with figures (the CLI ``report`` command)."""
    from . import viz
    from .alignment import AlignmentStructureAnalyzer
    from .pos import UPOS_ORDER, PosComparativeAnalyzer
    from .reporter import CorpusReporter, top_bottom_summary

    viz.use_agg_if_headless()
    rep = CorpusReporter(loader.config, loader.registry, run_name)
    rep.note(field=field, function_words=("hidden" if filter_function_words else "kept"),
             punct=str(punct))
    rep.add_section("1. Inventory", "Every text with full author-translator and book names.")
    rep.add_table("inventory", loader.registry.inventory())

    pairs = [p for p, _, _ in loader.load_translation_pairs()]
    ana = AlignmentStructureAnalyzer(loader.cache)
    summary = ana.summary(pairs)
    rep.add_section("2. Sentence alignment structure")
    rep.add_table("alignment_summary", summary.round(3))
    rep.add_figure("alignment_stacked", viz.alignment_stacked(summary))
    rep.add_summary(top_bottom_summary(summary, "R_sent", "pair"))

    allsel = loader.load_all()
    prof = PosComparativeAnalyzer().profile_table(allsel)
    rep.add_section("3. Part-of-speech profiles")
    rep.add_table("pos_profile", prof.round(2))
    rep.add_figure("pos_heatmap", viz.pos_heatmap(prof, UPOS_ORDER))
    rep.add_summary(top_bottom_summary(prof, "lexical_density", "title", "%"))

    div = diversity_for(loader, allsel, field, filter_function_words, punct=punct)
    rep.add_section("4. Lexical diversity")
    rep.add_table("diversity", div.round(3), index=True)
    rep.add_figure("diversity_radar", viz.diversity_radar(div))
    rep.add_summary(top_bottom_summary(div.reset_index(), "MTLD", "index"))
    return rep.finalize()
