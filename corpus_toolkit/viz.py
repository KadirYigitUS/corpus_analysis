"""All figures of the notebook (matplotlib; every function returns a ``Figure``).

Visual grammar (identical across chapters, see :mod:`corpus_toolkit.style`):
author-translator colours Selma Mine = purple, Zühtü Bayar = green, Özlem Kurdoğlu = blue;
bar *style* encodes the text type (English source = light/hatched, translation = solid,
indigenous = outlined).  Figures are colour-blind-safe in grayscale because shape/hatching
carries the same information.
"""

from collections.abc import Mapping, Sequence

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure

from .alignment import ALIGN_TYPES
from .diversity import METRIC_INFO, RADAR_METRICS

AUTHOR_COLORS = {"SM": "#7c3aed", "ZB": "#16a34a", "OK": "#2563eb"}
TYPE_STYLE = {"source": {"alpha": 0.45, "hatch": "//"}, "translation": {"alpha": 0.95, "hatch": ""},
              "indigenous": {"alpha": 0.25, "hatch": "xx"}}
ALIGN_COLORS = {"1:1": "#34d399", "1:N": "#38bdf8", "N:1": "#fbbf24", "N:M": "#a78bfa",
                "omission": "#fb7185", "addition": "#94a3b8"}


def _setup() -> None:
    plt.rcParams.update({"figure.dpi": 110, "axes.spines.top": False,
                         "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.25,
                         "font.size": 10, "axes.titleweight": "bold", "axes.titlesize": 11})


def color_for(focal_code: str) -> str:
    return AUTHOR_COLORS.get(focal_code, "#64748b")


def save(fig: Figure, path: "str | object", dpi: int = 300) -> None:
    fig.savefig(str(path), dpi=dpi, bbox_inches="tight")


def alignment_stacked(summary: pd.DataFrame) -> Figure:
    """Fig 1A — share of each alignment type per pair (stacked horizontal bars)."""
    _setup()
    fig, ax = plt.subplots(figsize=(9, 0.9 * len(summary) + 1.6))
    left = np.zeros(len(summary))
    for ty in ALIGN_TYPES:
        vals = summary[f"{ty}_pct"].to_numpy(dtype=float)
        ax.barh(summary["pair"], vals, left=left, color=ALIGN_COLORS[ty], label=ty,
                edgecolor="white")
        for y, (lft, v) in enumerate(zip(left, vals)):
            if v > 4:
                ax.text(lft + v / 2, y, f"{v:.0f}", ha="center", va="center", fontsize=8)
        left += vals
    ax.set_xlabel("% of alignment groups")
    ax.set_title("Alignment structure per translation pair")
    ax.invert_yaxis()
    ax.legend(ncol=6, loc="upper center", bbox_to_anchor=(0.5, -0.18), frameon=False)
    ax.grid(False)
    return fig


def alignment_scatter(tables: Mapping[str, pd.DataFrame], max_points: int = 1500) -> Figure:
    """Fig 1B — English vs Turkish length of 1:1 alignments (words), with slope per pair."""
    _setup()
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    for i, (label, t) in enumerate(tables.items()):
        one = t[t["type"] == "1:1"]
        if len(one) > max_points:
            one = one.sample(max_points, random_state=13)
        c = matplotlib.colormaps["tab10"](i)
        ax.scatter(one["eng_words"], one["tur_words"], s=7, alpha=0.25, color=c)
        full = t[t["type"] == "1:1"]
        slope = float((full["eng_words"] * full["tur_words"]).sum()
                      / max((full["eng_words"] ** 2).sum(), 1))
        xs = np.array([0, full["eng_words"].quantile(0.99)])
        ax.plot(xs, slope * xs, color=c, lw=2, label=f"{label} (slope {slope:.2f})")
    ax.set_xlabel("English words per 1:1 alignment")
    ax.set_ylabel("Turkish words")
    ax.set_title("Length relation in 1:1 alignments")
    ax.legend(fontsize=8, frameon=False)
    return fig


def pos_heatmap(profile: pd.DataFrame, upos: Sequence[str]) -> Figure:
    """Fig 2A — UPOS share (%) per text."""
    _setup()
    data = profile.set_index("code")[list(upos)]
    fig, ax = plt.subplots(figsize=(10, 0.5 * len(data) + 2))
    im = ax.imshow(data.to_numpy(), aspect="auto", cmap="YlGnBu")
    ax.set_xticks(range(len(upos)), upos, rotation=45, ha="right")
    ax.set_yticks(range(len(data)), [f"{c} · {t[:26]}" for c, t in
                                     zip(profile["code"], profile["title"])])
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            v = float(data.to_numpy()[i, j])
            ax.text(j, i, f"{v:.0f}" if v >= 1 else "·", ha="center", va="center", fontsize=7,
                    color="white" if v > data.to_numpy().max() * 0.6 else "black")
    ax.grid(False)
    fig.colorbar(im, ax=ax, label="% of non-punctuation tokens")
    ax.set_title("Part-of-speech profile per text")
    return fig


def pos_pair(pair_df: pd.DataFrame, title: str) -> Figure:
    """Fig 2B — dumbbell: English vs Turkish share per UPOS."""
    _setup()
    d = pair_df.sort_values("English %")
    fig, ax = plt.subplots(figsize=(7, 5.5))
    y = np.arange(len(d))
    ax.hlines(y, d["English %"], d["Turkish %"], color="#cbd5e1", lw=2)
    ax.scatter(d["English %"], y, color="#06b6d4", s=50, label="English", zorder=3)
    ax.scatter(d["Turkish %"], y, color="#f59e0b", s=50, label="Turkish", zorder=3)
    ax.set_yticks(y, d.index)
    ax.set_xlabel("% of non-punctuation tokens")
    ax.set_title(title)
    ax.legend(frameon=False)
    return fig


def pos_group(group_df: pd.DataFrame, labels: tuple[str, str]) -> Figure:
    """Fig 2C — forest plot of mean difference (pp) with bootstrap 95% CI."""
    _setup()
    d = group_df.iloc[::-1]
    fig, ax = plt.subplots(figsize=(7, 5.5))
    y = np.arange(len(d))
    ax.errorbar(d["mean diff pp"], y,
                xerr=[d["mean diff pp"] - d["CI95 low"], d["CI95 high"] - d["mean diff pp"]],
                fmt="o", color="#334155", ecolor="#94a3b8", capsize=3)
    ax.axvline(0, color="#ef4444", lw=1)
    ax.set_yticks(y, d["UPOS"])
    ax.set_xlabel(f"mean share difference, {labels[0]} − {labels[1]} (percentage points)")
    ax.set_title("Translated vs. indigenous Turkish: POS differences (bootstrap 95% CI)")
    return fig


def diversity_radar(table: pd.DataFrame, metrics: Sequence[str] = RADAR_METRICS) -> Figure:
    """Radar of z-scored length-robust metrics (one polygon per text)."""
    _setup()
    z = (table[list(metrics)] - table[list(metrics)].mean()) / table[list(metrics)].std(ddof=0)
    z = z.fillna(0.0)
    angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
    angles += angles[:1]
    fig = plt.figure(figsize=(7, 7))
    ax = fig.add_subplot(111, polar=True)
    for i, (name, row) in enumerate(z.iterrows()):
        vals = row.tolist() + row.tolist()[:1]
        ax.plot(angles, vals, lw=1.6, color=matplotlib.colormaps["tab20"](i % 20), label=str(name))
        ax.fill(angles, vals, alpha=0.05, color=matplotlib.colormaps["tab20"](i % 20))
    ax.set_xticks(angles[:-1], [METRIC_INFO[m].label.split(" (")[0] for m in metrics], fontsize=8)
    ax.set_title("Lexical diversity profile (z-scores across selected texts)", pad=20)
    ax.legend(loc="upper left", bbox_to_anchor=(1.05, 1.0), fontsize=7, frameon=False)
    return fig


def mattr_trajectories(series: Mapping[str, np.ndarray], window: int, points: int = 400
                       ) -> Figure:
    """MATTR across the text (down-sampled) — shows *where* a book is lexically rich."""
    _setup()
    fig, ax = plt.subplots(figsize=(9, 4))
    for i, (label, s) in enumerate(series.items()):
        if len(s) == 0:
            continue
        idx = np.linspace(0, len(s) - 1, min(points, len(s))).astype(int)
        ax.plot(np.linspace(0, 100, len(idx)), s[idx], label=label, color=matplotlib.colormaps["tab10"](i % 10))
    ax.set_xlabel("position in text (%)")
    ax.set_ylabel(f"TTR of {window}-word window")
    ax.set_title(f"Moving-average TTR trajectory (w={window})")
    ax.legend(fontsize=7, frameon=False, ncol=2)
    return fig


def zipf_plot(freqs: Mapping[str, pd.DataFrame]) -> Figure:
    """Rank–frequency curves on log–log axes (Zipf)."""
    _setup()
    fig, ax = plt.subplots(figsize=(6.5, 5))
    for i, (label, df) in enumerate(freqs.items()):
        ax.loglog(df["rank"], df["freq"], label=label, color=matplotlib.colormaps["tab10"](i % 10), lw=1.4)
    ax.set_xlabel("rank")
    ax.set_ylabel("frequency")
    ax.set_title("Zipf plot")
    ax.legend(fontsize=7, frameon=False)
    return fig


def heatmap(df: pd.DataFrame, title: str, cmap: str = "mako_r", center: float | None = None,
            fmt: str = ".1f", annotate: bool = True) -> Figure:
    """Generic annotated heatmap (batch KWIC rates, correlations, TF-IDF)."""
    _setup()
    import seaborn as sns

    fig, ax = plt.subplots(figsize=(max(5.5, 0.7 * df.shape[1] + 2), max(3.5, 0.45 * df.shape[0] + 1.8)))
    sns.heatmap(df, annot=annotate, fmt=fmt, cmap=cmap, center=center, ax=ax,
                cbar_kws={"shrink": 0.8}, linewidths=0.5, linecolor="white")
    ax.set_title(title)
    ax.grid(False)
    return fig


def chunk_dispersion(chunks: Mapping[str, np.ndarray], codes: Sequence[str]) -> Figure:
    """Per-text profiles (10 chunks) of each label: where in the book does the word live?"""
    _setup()
    labels = list(chunks)
    fig, axes = plt.subplots(len(labels), 1, figsize=(9, 1.9 * len(labels)), sharex=True,
                             squeeze=False)
    for ax, lab in zip(axes[:, 0], labels):
        arr = chunks[lab]
        for code, row in zip(codes, arr):
            ax.plot(np.arange(1, arr.shape[1] + 1), row, marker="o", ms=3, lw=1.2, label=code)
        ax.set_ylabel(lab + "\nper 10k")
    axes[0, 0].legend(ncol=min(len(codes), 6), fontsize=7, frameon=False,
                      bbox_to_anchor=(1, 1.4))
    axes[-1, 0].set_xlabel("chunk (10 equal parts of each text)")
    fig.suptitle("Dispersion profiles across the narrative", y=1.0)
    return fig


def collocation_scatter(table: pd.DataFrame, node: str, top_labels: int = 15,
                        x: str = "MI", y: str = "G2") -> Figure:
    """GraphColl-style scatter: association strength (MI) vs evidence (log-likelihood)."""
    _setup()
    fig, ax = plt.subplots(figsize=(7.5, 5.5))
    d = table[table[y] > 0]
    ax.scatter(d[x], np.log10(d[y]), s=14 + 2 * np.sqrt(d["O11"]), alpha=0.55, color="#6366f1")
    for _, r in d.sort_values(y, ascending=False).head(top_labels).iterrows():
        ax.annotate(str(r["collocate"]), (r[x], np.log10(r[y])), fontsize=8,
                    xytext=(3, 3), textcoords="offset points")
    ax.set_xlabel(f"{x} (effect size: how strong?)")
    ax.set_ylabel(f"log10 {y} (evidence: how sure?)")
    ax.set_title(f"Collocates of '{node}'")
    return fig


def dispersion_barcode(points: Mapping[str, Sequence[float]], title: str = "Lexical dispersion"
                       ) -> Figure:
    """NLTK-style dispersion plot with relative positions (0–1)."""
    _setup()
    fig, ax = plt.subplots(figsize=(9, 0.55 * max(len(points), 1) + 1.4))
    for i, xs in enumerate(points.values()):
        ax.vlines(xs, i - 0.35, i + 0.35, color=matplotlib.colormaps["tab10"](i % 10), lw=0.8)
    ax.set_yticks(range(len(points)), list(points))
    ax.set_xlim(0, 1)
    ax.set_xlabel("relative position in text")
    ax.set_title(title)
    ax.grid(False)
    return fig


def figure_to_png_bytes(fig: Figure) -> bytes:
    import io

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    return buf.getvalue()


def use_agg_if_headless() -> None:
    """Switch to the non-interactive backend when no display is available (CI / nbconvert)."""
    import os

    if not os.environ.get("DISPLAY") and matplotlib.get_backend().lower() not in {"agg"}:
        try:
            matplotlib.use("Agg", force=False)
        except Exception:  # pragma: no cover
            pass
