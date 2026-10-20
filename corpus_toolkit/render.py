"""Renderers for :class:`~corpus_toolkit.kwic.ConcordanceResult` (Chapter 7 UI/UX).

Three notebook views and one console view, all driven by the same data:

``kwic``    classic *aligned* KWIC table – node centred, left right-aligned, source badge
``chips``   coordinate-chip table – every hit carries ``ch · p · s · tok`` so it can be cited
``cards``   sentence cards – full sentence with node marked; for translation pairs the aligned
            counterpart sentence in the other language is shown underneath
``parallel`` side-by-side EN ⇄ TR sentence table (NDA-style C·P·S layout, see ``parallel_view``)
``console`` plain-text KWIC (works in a terminal, CI logs, nbconvert text output)
"""

from typing import Any

from .kwic import ConcordanceResult, KwicLine
from .style import CSS, badge, detok, esc


def _header(res: ConcordanceResult) -> str:
    left, right = res.span
    span = "sentence" if res.span[0] > 1000 else f"−{left} / +{right}"
    clamp = "sentence-clamped" if res.sentence_clamped else "may cross sentence borders"
    shown = f"{len(res)} of {res.total_hits} hit(s) shown"
    return (f'<div class="meta">🔎 <b>{esc(res.query_description)}</b><br>'
            f"span {span} · {clamp} · view <code>{esc(res.view_label)}</code> · {shown}</div>")


def _source(line: KwicLine) -> str:
    return (f'{badge(line.corpus_type)} <span title="{esc(line.focal_name)}">'
            f"{esc(line.title)}</span>")


def kwic_html(res: ConcordanceResult, max_lines: int = 40) -> str:
    dim = res.view_label.startswith("content")
    rows = []
    for i, ln in enumerate(res.lines[:max_lines], 1):
        rows.append(
            f'<tr><td class="idx">{i}</td><td>{_source(ln)}</td>'
            f'<td class="l">{detok(ln.left, dim)}</td>'
            f'<td class="n"><mark class="node">{esc(ln.node[0])}</mark></td>'
            f'<td class="r">{detok(ln.right, dim)}</td></tr>')
    table = ("<div class='scroll'><table><tr><th>#</th><th>Text</th>"
             "<th style='text-align:right'>Left context</th><th style='text-align:center'>Node"
             "</th><th>Right context</th></tr>" + "".join(rows) + "</table></div>")
    return f"<div class='ct'>{_header(res)}{table}</div>"


def chips_html(res: ConcordanceResult, max_lines: int = 40) -> str:
    dim = res.view_label.startswith("content")
    rows = []
    for i, ln in enumerate(res.lines[:max_lines], 1):
        rows.append(
            f'<tr><td class="idx">{i}</td><td>{_source(ln)}</td>'
            f'<td><span class="chip">{esc(ln.coordinate)}</span></td>'
            f'<td class="n"><mark class="node">{esc(ln.node[0])}</mark></td>'
            f"<td>{detok(ln.left[-3:], dim)} <b>·</b> {detok(ln.right[:3], dim)}</td></tr>")
    table = ("<div class='scroll'><table><tr><th>#</th><th>Text</th><th>Coordinate</th>"
             "<th>Node</th><th>Mini-context</th></tr>" + "".join(rows) + "</table></div>")
    return f"<div class='ct'>{_header(res)}{table}</div>"


def _counterpart(line: KwicLine, loader: Any) -> tuple[str, str, str] | None:
    """(alignment id, English text, Turkish text) for a hit inside a translation pair."""
    rec = loader.registry.texts[line.code]
    if not rec.pair_id:
        return None
    idx = loader.alignment_index(loader.registry.pairs[rec.pair_id])
    ai = idx.ai_of(rec.language, (line.ch_no, line.p_no, line.s_no))
    if ai is None:
        return None
    eng, tur = idx.texts(ai)
    return str(ai), eng, tur


def cards_html(res: ConcordanceResult, loader: Any = None, max_lines: int = 8) -> str:
    dim = res.view_label.startswith("content")
    cards = []
    for ln in res.lines[:max_lines]:
        body = (f'<p><span class="lang">{ln.language.upper()}</span> '
                f"{detok(ln.sentence_tokens, dim, ln.node_index)}</p>")
        other = _counterpart(ln, loader) if loader is not None else None
        if other:
            ai, eng, tur = other
            lang_other, txt = ("TR", tur) if ln.language == "en" else ("EN", eng)
            body += (f'<p><span class="lang">{lang_other} · aligned group {ai}</span> '
                     f"{esc(txt)}</p>")
        cards.append(f'<div class="card"><div class="head">{_source(ln)} '
                     f'<span class="chip">{esc(ln.coordinate)}</span></div>{body}</div>')
    return f"<div class='ct'>{_header(res)}{''.join(cards)}</div>"


def console_view(res: ConcordanceResult, max_lines: int = 30, width: int = 38) -> str:
    out = [f"🔎 {res.query_description}",
           f"   span={res.span if res.span[0] < 1000 else 'sentence'} view={res.view_label} "
           f"hits shown {min(len(res), max_lines)}/{res.total_hits}"]
    for i, ln in enumerate(res.lines[:max_lines], 1):
        left = ln.left_text()[-width:].rjust(width)
        right = ln.right_text()[:width].ljust(width)
        out.append(f"{i:>3} {ln.code:<8} {left}  [{ln.node[0]}]  {right}  ({ln.coordinate})")
    return "\n".join(out)


def show(res: ConcordanceResult, view: str = "kwic", loader: Any = None, max_lines: int = 30
         ) -> None:
    """Display in a notebook (falls back to console text outside IPython)."""
    try:
        from IPython.display import HTML, display

        if view == "console":
            print(console_view(res, max_lines))
            return
        if view == "parallel":
            from .parallel_view import hits_to_view

            display(HTML(hits_to_view(res, loader, max_groups=max_lines)))
            return
        if view == "table":
            from .table_view import show_table

            show_table(res, page_size=min(max_lines, 20) or 20)
            return
        fn = {"kwic": lambda: kwic_html(res, max_lines), "chips": lambda: chips_html(res, max_lines),
              "cards": lambda: cards_html(res, loader, max_lines)}[view]
        display(HTML(CSS + fn()))
    except ImportError:  # pragma: no cover
        print(console_view(res, max_lines))


from .parallel_view import show_parallel  # noqa: E402
from .table_view import (  # noqa: E402
    disable_interactive_tables,
    enable_interactive_tables,
    show_table,
    table_html,
)

__all__ = [
    "kwic_html",
    "chips_html",
    "cards_html",
    "console_view",
    "show",
    "show_parallel",
    "show_table",
    "table_html",
    "enable_interactive_tables",
    "disable_interactive_tables",
]
