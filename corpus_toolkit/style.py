"""Shared look & feel: one CSS block and small HTML helpers (pastel, accessible, light/dark safe).

Colour semantics (kept identical in every chapter so the student learns them once):

* **Cyan**    English source text         * **Amber**   Turkish translation
* **Emerald** Turkish indigenous novel    * **Rose**    the node / highlighted match

Author colours used in figures: Selma Mine = purple, Zühtü Bayar = green, Özlem Kurdoğlu = blue.
"""

import html

CSS = """
<style>
.ct { font-family: -apple-system, 'Segoe UI', Roboto, sans-serif; font-size: 13.5px;
      color: var(--jp-ui-font-color1, #1f2937); }
.ct .scroll { overflow-x: auto; max-width: 100%; border: 1px solid #d9dee5; border-radius: 8px; }
.ct table { border-collapse: collapse; width: 100%; }
.ct th { background: #f1f5f9; color: #334155; text-align: left; padding: 6px 10px;
         position: sticky; top: 0; font-weight: 600; font-size: 12px; letter-spacing: .02em; }
.ct td { padding: 4px 10px; border-top: 1px solid #eef1f5; vertical-align: top; }
.ct tr:hover td { background: rgba(125, 180, 255, .10); }
.ct td.l { text-align: right; white-space: nowrap; font-family: 'DejaVu Sans Mono', monospace; }
.ct td.n { text-align: center; white-space: nowrap; font-family: 'DejaVu Sans Mono', monospace; }
.ct td.r { text-align: left; white-space: nowrap; font-family: 'DejaVu Sans Mono', monospace; }
.ct td.idx { color: #94a3b8; font-size: 11px; }
.ct .fw { opacity: .45; }
.ct mark.node { background: #ffe0e6; color: #9f1239; padding: 1px 6px; border-radius: 6px;
                font-weight: 700; border: 1px solid #fecdd3; }
.ct .badge { display: inline-block; padding: 1px 8px; border-radius: 999px; font-size: 11px;
             font-weight: 600; border: 1px solid transparent; white-space: nowrap; }
.ct .b-source { background: #cffafe; color: #155e75; border-color: #a5f3fc; }
.ct .b-translation { background: #fef3c7; color: #92400e; border-color: #fde68a; }
.ct .b-indigenous { background: #d1fae5; color: #065f46; border-color: #a7f3d0; }
.ct .chip { display: inline-block; padding: 1px 7px; border-radius: 6px; background: #eef2ff;
            color: #3730a3; font-family: 'DejaVu Sans Mono', monospace; font-size: 11.5px;
            border: 1px solid #c7d2fe; }
.ct .card { border: 1px solid #d9dee5; border-radius: 10px; padding: 10px 14px; margin: 8px 0;
            background: rgba(248, 250, 252, .6); }
.ct .card .head { margin-bottom: 6px; display: flex; gap: 8px; flex-wrap: wrap;
                  align-items: center; }
.ct .card .lang { font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; }
.ct .card p { margin: 3px 0 3px 0; line-height: 1.55; }
.ct .meta { color: #64748b; font-size: 12px; margin: 6px 2px; }
.ct .learn { border-left: 4px solid #6366f1; background: #eef2ff; padding: 8px 12px;
             border-radius: 0 8px 8px 0; margin: 8px 0; }
</style>
"""

_BADGE = {"source": ("b-source", "English source"), "translation": ("b-translation",
          "Turkish translation"), "indigenous": ("b-indigenous", "Turkish indigenous")}
_NO_SPACE_BEFORE = set(".,;:!?)]}…”’'%")
_NO_SPACE_AFTER = set("([{“‘")


def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def badge(corpus_type: str) -> str:
    cls, label = _BADGE.get(corpus_type, ("b-source", corpus_type))
    return f'<span class="badge {cls}">{label}</span>'


def detok(cells: "list[tuple[str, int]]", dim_function: bool, node_index: int | None = None
          ) -> str:
    """Join (form, class) cells into readable HTML; dim function words; optionally mark a node."""
    out: list[str] = []
    prev = ""
    for i, (w, cls) in enumerate(cells):
        piece = esc(w)
        if node_index is not None and i == node_index:
            piece = f'<mark class="node">{piece}</mark>'
        elif dim_function and cls == 1:
            piece = f'<span class="fw">{piece}</span>'
        glue = "" if (not out or w in _NO_SPACE_BEFORE or prev in _NO_SPACE_AFTER) else " "
        out.append(glue + piece)
        prev = w
    return "".join(out)
