"""Command-line interface: ``python -m corpus_toolkit <command> …`` (see README for examples)."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

import pandas as pd

from . import __version__
from .analysis import diversity_for, standard_report
from .collocation import collocates
from .depviz import DependencyVisualizer
from .explorer import CATEGORIES, _select_texts
from .kwic import Concordancer
from .loader import CorpusLoader
from .pos import PosComparativeAnalyzer
from .render import console_view
from .search import CorpusSearchEngine, SearchQuery
from .tfidf import TfidfAnalyzer
from .tokenview import PunctMode, TokenView

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 40)


def _add_scope(p: argparse.ArgumentParser) -> None:
    p.add_argument("--category", default="All texts", choices=list(CATEGORIES),
                   help="which texts to use (default: All texts)")
    p.add_argument("--author", default=None, help="author code or full name, e.g. SM or 'Selma Mine'")
    p.add_argument("--field", default="lem", choices=["lem", "tok"], help="lemma or token")
    p.add_argument("--content", action="store_true", help="hide function words (content view)")
    p.add_argument("--mode", default="drop", choices=["drop", "mask"])
    p.add_argument("--punct", default="drop", choices=["keep", "drop", "strip", "split"],
                   help="punctuation handling: drop (default), keep (with punct), strip (collapse in-token), split (retokenize in-token)")
    p.add_argument("--with-punct", action="store_true", help="alias for --punct keep")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="corpus_toolkit", description=__doc__)
    ap.add_argument("--version", action="version", version=__version__)
    ap.add_argument("--cache-policy", default="keep", choices=["keep", "clear", "ask"])

    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("inventory", help="list all texts with full names")

    s = sub.add_parser("search", help="KWIC concordance")
    s.add_argument("terms", nargs="+")
    _add_scope(s)
    s.add_argument("--match", default="exact", choices=["exact", "glob", "regex"])
    s.add_argument("--span", default="collocation", help="phrase|collocation|extended|discourse|"
                   "sentence|N|L5R2")
    s.add_argument("--pos", nargs="*", help="UPOS filter, e.g. NOUN VERB")
    s.add_argument("--with", dest="collocate", nargs="*", help="require these context words")
    s.add_argument("--max", type=int, default=20)

    d = sub.add_parser("diversity", help="lexical diversity table")
    _add_scope(d)

    c = sub.add_parser("collocate", help="collocates of a node word")
    c.add_argument("node")
    c.add_argument("--text", required=True, help="text code or title, e.g. BR-SM")
    c.add_argument("--left", type=int, default=5)
    c.add_argument("--right", type=int, default=5)
    c.add_argument("--min-freq", type=int, default=3)
    c.add_argument("--sort", default="G2", choices=["MI", "MI2", "MI3", "T", "G2", "LogDice"])
    c.add_argument("--top", type=int, default=15)
    c.add_argument("--field", default="lem", choices=["lem", "tok"])
    c.add_argument("--content", action="store_true")
    c.add_argument("--punct", default="drop", choices=["keep", "drop", "strip", "split"])
    c.add_argument("--with-punct", action="store_true")

    sub.add_parser("pos", help="POS profile of every text")
    sub.add_parser("align", help="alignment structure per translation pair")

    dep = sub.add_parser("dep", help="dependency table (and SVG) of one sentence")
    dep.add_argument("text")
    dep.add_argument("--coord", nargs=3, type=int, default=[1, 1, 1], metavar=("CH", "P", "S"))
    dep.add_argument("--svg", default=None, help="write displaCy SVG to this path")

    t = sub.add_parser("tfidf", help="top TF-IDF terms per text")
    t.add_argument("--lang", default="tr", choices=["en", "tr"])
    t.add_argument("--top", type=int, default=10)
    t.add_argument("--chunks", type=int, default=1)
    t.add_argument("--punct", default="drop", choices=["keep", "drop", "strip", "split"])
    t.add_argument("--with-punct", action="store_true")

    r = sub.add_parser("report", help="write the standard report to data/corpus_analysis/reports")
    r.add_argument("--name", default="standard")
    r.add_argument("--punct", default="drop", choices=["keep", "drop", "strip", "split"])
    r.add_argument("--with-punct", action="store_true")

    ca = sub.add_parser("cache", help="cache info / clear")
    ca.add_argument("action", choices=["info", "clear"])
    return ap


def _scope_texts(loader: CorpusLoader, args: Any) -> list[Any]:
    return _select_texts(loader, args.category, args.author)


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "cache":
        loader = CorpusLoader(cache_policy="keep", verbose=False)
        if args.action == "clear":
            print(f"removed {loader.cache.clear()} item(s)")
        else:
            print(loader.cache.info())
        return 0
    loader = CorpusLoader(cache_policy=args.cache_policy, verbose=False)
    raw_punct = "keep" if getattr(args, "with_punct", False) else getattr(args, "punct", "drop")
    punct: PunctMode = cast(PunctMode, raw_punct if raw_punct in ("keep", "drop", "strip", "split") else "drop")
    if args.cmd == "inventory":
        print(loader.registry.inventory().to_string())
    elif args.cmd == "search":
        texts = _scope_texts(loader, args)
        q = SearchQuery(args.terms, args.field, args.match, pos=set(args.pos or []) or None,
                        collocate=args.collocate, filter_function_words=args.content,
                        mode=args.mode, punct=punct)
        res = CorpusSearchEngine().search(q, texts)
        print(res.summary().to_string(index=False))
        print(console_view(Concordancer().run(res, texts, args.span), args.max))
    elif args.cmd == "diversity":
        texts = _scope_texts(loader, args)
        print(diversity_for(loader, texts, args.field, args.content, punct=punct).round(3).T.to_string())
    elif args.cmd == "collocate":
        text = loader.load_text(args.text)
        tab = collocates(TokenView(text, args.field, args.content, punct=punct), args.node, args.left,
                         args.right, True, args.min_freq, args.sort)
        print(f"node={args.node} f={tab.attrs.get('f_node')} N={tab.attrs.get('N')} "
              f"R1={tab.attrs.get('R1')}")
        print(tab.head(args.top).round(3).to_string(index=False))
    elif args.cmd == "pos":
        print(PosComparativeAnalyzer().profile_table(loader.load_all()).round(1).to_string())
    elif args.cmd == "align":
        from .alignment import AlignmentStructureAnalyzer

        pairs = [p for p, _, _ in loader.load_translation_pairs()]
        print(AlignmentStructureAnalyzer(loader.cache).summary(pairs).round(2).T.to_string())
    elif args.cmd == "dep":
        text = loader.load_text(args.text)
        dv = DependencyVisualizer(loader)
        sid = dv.sid_of(text, tuple(args.coord))  # type: ignore[arg-type]
        print(dv.table(text, sid).to_string(index=False))
        if args.svg:
            Path(args.svg).write_text(dv.svg(text, sid), encoding="utf-8")
            print(f"SVG written to {args.svg}")
    elif args.cmd == "tfidf":
        selection = loader.load_all_english() if args.lang == "en" else loader.load_all_turkish()
        tf_res = TfidfAnalyzer().fit(selection, "lem", True, punct=punct, n_chunks=args.chunks)
        for d in tf_res.doc_ids:
            top = tf_res.top_terms(d, args.top)
            print(f"{d}: " + ", ".join(f"{t}({w:.3f})" for t, w in zip(top.term, top.tfidf)))
    elif args.cmd == "report":
        print(f"report written: {standard_report(loader, args.name, punct=punct)}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
