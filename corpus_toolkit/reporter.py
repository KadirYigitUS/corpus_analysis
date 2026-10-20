"""Reporter (Chapter 12): collect results and write them to ``data/corpus_analysis/…``.

Layout (all outside the git repository):

``reports/``   one Markdown report per run (``<name>_<YYYYmmdd_HHMMSS>.md``) + optional ``.xlsx``
``tables/``    every table as UTF-8 TSV (+ the combined workbook)
``figures/``   every figure as 300-DPI PNG

Auto-summaries are generated **only from the numbers in the tables** (no free-text claims), so a
report can never state something the data do not show.
"""

from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import pandas as pd
from matplotlib.figure import Figure

from .config import SCHEMA_VERSION, TOOLKIT_VERSION, CorpusPathConfig
from .registry import CorpusRegistry
from .viz import save


def slug(text: str) -> str:
    keep = "".join(c if c.isalnum() else "_" for c in text.lower())
    return "_".join(p for p in keep.split("_") if p)[:60] or "item"


def top_bottom_summary(df: pd.DataFrame, column: str, label_col: str, unit: str = "") -> str:
    """'Highest <col>: X (v); lowest: Y (v).' computed from ``df`` only."""
    d = df[[label_col, column]].dropna()
    if d.empty:
        return f"No values for {column}."
    hi, lo = d.loc[d[column].idxmax()], d.loc[d[column].idxmin()]
    return (f"Highest {column}: {hi[label_col]} ({hi[column]:.3g}{unit}); "
            f"lowest: {lo[label_col]} ({lo[column]:.3g}{unit}).")


class CorpusReporter:
    def __init__(self, config: CorpusPathConfig, registry: CorpusRegistry | None = None,
                 run_name: str = "corpus_analysis") -> None:
        self.config = config
        self.registry = registry
        self.config.ensure_dirs()
        self.stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_name = slug(run_name)
        self._items: list[tuple[str, str]] = []  # (kind, markdown)
        self._tables: dict[str, pd.DataFrame] = {}
        self.provenance: dict[str, str] = {}

    # ------------------------------------------------------------------ add
    def note(self, **provenance: object) -> None:
        """Record analysis options (view, span, field …) shown in the report header."""
        self.provenance.update({k: str(v) for k, v in provenance.items()})

    def add_section(self, title: str, text: str = "") -> None:
        self._items.append(("section", f"\n## {title}\n\n{text}\n"))

    def add_text(self, text: str) -> None:
        self._items.append(("text", f"{text}\n"))

    def add_table(self, name: str, df: pd.DataFrame, caption: str = "", max_rows: int = 25,
                  index: bool = False) -> Path:
        fname = f"{self.run_name}_{self.stamp}_{slug(name)}.tsv"
        path = self.config.tables_dir / fname
        df.to_csv(path, sep="\t", index=index, encoding="utf-8")
        self._tables[slug(name)[:31]] = df.reset_index() if index else df
        shown = df.head(max_rows)
        md = shown.to_markdown(index=index, floatfmt=".3f") if len(shown) else "_(empty)_"
        more = f"\n\n_{len(df) - max_rows} more rows in `{fname}`._" if len(df) > max_rows else ""
        self._items.append(("table", f"\n**Table – {name}.** {caption}\n\n{md}{more}\n"
                                     f"\n_File: `tables/{fname}`_\n"))
        return path

    def add_figure(self, name: str, fig: Figure, caption: str = "") -> Path:
        fname = f"{self.run_name}_{self.stamp}_{slug(name)}.png"
        path = self.config.figures_dir / fname
        save(fig, path, dpi=300)
        self._items.append(("figure", f"\n![{name}](../figures/{fname})\n\n*Figure – {name}.* "
                                      f"{caption}\n"))
        return path

    def add_summary(self, sentence: str) -> None:
        self._items.append(("summary", f"> **Data summary.** {sentence}\n"))

    # --------------------------------------------------------------- output
    def header(self) -> str:
        lines = [f"# Corpus analysis report – {self.run_name}",
                 f"*Generated {datetime.now():%Y-%m-%d %H:%M:%S} · corpus_toolkit "
                 f"v{TOOLKIT_VERSION} · schema {SCHEMA_VERSION}*", ""]
        if self.provenance:
            lines += ["**Analysis options**", ""] + [f"- {k}: `{v}`"
                                                    for k, v in self.provenance.items()] + [""]
        if self.registry is not None:
            lines += ["**Texts in the focal sub-corpus**", ""]
            lines += [f"- {self.registry.display(r)}" for r in self.registry.select()] + [""]
        return "\n".join(lines)

    def finalize(self, xlsx: bool = True) -> Path:
        """Write the Markdown report (and workbook); returns the report path."""
        path = self.config.reports_dir / f"{self.run_name}_{self.stamp}.md"
        path.write_text(self.header() + "\n".join(md for _, md in self._items),
                        encoding="utf-8")
        if xlsx and self._tables:
            xl = self.config.reports_dir / f"{self.run_name}_{self.stamp}.xlsx"
            with pd.ExcelWriter(xl, engine="openpyxl") as writer:
                for name, df in self._tables.items():
                    df.to_excel(writer, sheet_name=name, index=False)
        return path

    def collect(self, builder: Callable[["CorpusReporter"], None]) -> Path:
        """Convenience: run ``builder(self)`` then :meth:`finalize`."""
        builder(self)
        return self.finalize()
