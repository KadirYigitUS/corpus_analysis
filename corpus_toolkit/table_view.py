"""Flexible, self-contained interactive columnar table view (Task 6).

Provides an air-gapped, zero-dependency HTML5 + vanilla-ES6 DataGrid for Jupyter Notebooks
(`Corpus_Analysis.ipynb` and `Corpus_Analysis_tr.ipynb`) that works seamlessly inside
JupyterLab, classic Notebook, VS Code / Antigravity Notebook, and static HTML exports without
installing any external Python or npm libraries (strictly adhering to ``AGENTS.md`` Mandate #2).

Features:
* **Client-side pagination** with **20 rows per page** by default and a page-size selector
  (``10 | 20 | 50 | 100 | All``), First / Prev / Next / Last buttons, and ``Rows X–Y of Z`` indicator;
* **Multi-type ascending / descending / reset sorting** (``▲ / ▼ / ⇅``) with numeric ``NaN``/``—``
  values pushed to the bottom and ``Intl.Collator('tr', {numeric: true, sensitivity: 'base'})``
  locale-aware Turkish string ordering;
* **Interactive column width drag-resizing** via ``.ct-col-resizer`` header handles (double-click to
  auto-fit) plus three layout mode presets (``Auto-Fit``, ``Wrap Text``, ``Compact``);
* **Instant substring filter** across all columns and a **Copy TSV** button;
* **UUID-scoped lazy state initialization** (``root._ctState``) attached via inline DOM handlers so
  tables remain interactive even when injected dynamically via ``ipywidgets.Output``;
* **``max_rows=2000`` safety cap** to prevent Jupyter ZMQ IOPub payload bloat.
"""

from __future__ import annotations

import math
import uuid
from typing import Any

import numpy as np
import pandas as pd

from .style import CSS, esc

TABLE_CSS = """
<style>
.ct-tbl-wrap { margin: 10px 0; border: 1px solid #cbd5e1; border-radius: 8px;
               background: #ffffff; box-shadow: 0 1px 2px rgba(15, 23, 42, .05); overflow: hidden; }
.ct-tbl-bar { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; justify-content: space-between;
              padding: 7px 12px; background: #f8fafc; border-bottom: 1px solid #cbd5e1; font-size: 12px; }
.ct-tbl-title { font-weight: 700; color: #1e293b; font-size: 12.5px; margin-right: 6px; }
.ct-tbl-ctrls { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.ct-tbl-input { border: 1px solid #cbd5e1; border-radius: 6px; padding: 3px 8px; font-size: 12px;
                min-width: 165px; background: #ffffff; color: #0f172a; }
.ct-tbl-select, .ct-tbl-btn { border: 1px solid #cbd5e1; border-radius: 6px; padding: 3px 8px;
                              font-size: 11.5px; background: #ffffff; color: #334155; cursor: pointer;
                              font-weight: 600; user-select: none; }
.ct-tbl-btn:hover:not(:disabled), .ct-tbl-select:hover { background: #f1f5f9; }
.ct-tbl-btn:disabled { opacity: .45; cursor: default; }
.ct-tbl-btn.active { background: #e0e7ff; color: #1e40af; border-color: #818cf8; }
.ct-tbl-scroll { overflow-x: auto; max-height: 620px; overflow-y: auto; width: 100%; }
.ct-tbl-wrap table.ct-grid { border-collapse: collapse; width: 100%; table-layout: auto; }
.ct-tbl-wrap.layout-fixed table.ct-grid { table-layout: fixed; }
.ct-tbl-wrap table.ct-grid th { position: sticky; top: 0; z-index: 3; background: #f1f5f9; color: #1e293b;
                                font-size: 11.5px; font-weight: 700; padding: 7px 18px 7px 10px;
                                border-bottom: 2px solid #cbd5e1; border-right: 1px solid #e2e8f0;
                                user-select: none; white-space: nowrap; overflow: hidden;
                                text-overflow: ellipsis; cursor: pointer; }
.ct-tbl-wrap table.ct-grid th:hover { background: #e2e8f0; }
.ct-tbl-wrap table.ct-grid th .sort-ind { font-size: 10px; color: #64748b; margin-left: 4px; }
.ct-tbl-wrap table.ct-grid th.sorted-asc .sort-ind,
.ct-tbl-wrap table.ct-grid th.sorted-desc .sort-ind { color: #1d4ed8; font-weight: 800; }
.ct-col-resizer { position: absolute; right: 0; top: 0; bottom: 0; width: 6px;
                  cursor: col-resize; z-index: 4; }
.ct-col-resizer:hover { background: rgba(59, 130, 246, .45); }
.ct-tbl-wrap table.ct-grid td { padding: 5px 10px; border-top: 1px solid #eef2f6;
                                border-right: 1px solid #f8fafc; font-size: 12.5px;
                                vertical-align: top; max-width: 420px; overflow: hidden;
                                text-overflow: ellipsis; white-space: nowrap; }
.ct-tbl-wrap.layout-wrap table.ct-grid td { white-space: normal; word-break: break-word; }
.ct-tbl-wrap.layout-compact table.ct-grid td { padding: 2px 7px; font-size: 11.5px; }
.ct-tbl-wrap table.ct-grid tbody tr:nth-child(even) td { background: rgba(248, 250, 252, .65); }
.ct-tbl-wrap table.ct-grid tbody tr:hover td { background: rgba(59, 130, 246, .08); }
.ct-tbl-wrap td.num { text-align: right; font-family: 'DejaVu Sans Mono', monospace;
                      font-variant-numeric: tabular-nums; }
.ct-tbl-foot { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; justify-content: space-between;
               padding: 6px 12px; background: #f8fafc; border-top: 1px solid #cbd5e1;
               font-size: 11.5px; color: #475569; }
.ct-tbl-pager { display: flex; gap: 4px; align-items: center; }
</style>
"""

TABLE_JS = """
<script>
(function() {
  if (!window._ctTblEnsure) {
    var trCollator = (typeof Intl !== 'undefined' && Intl.Collator)
      ? new Intl.Collator('tr', { numeric: true, sensitivity: 'base' })
      : null;

    window._ctTblEnsure = function(id) {
      var root = document.getElementById(id);
      if (!root) return null;
      if (!root._ctState) {
        var tbody = root.querySelector('tbody');
        var allRows = tbody ? Array.prototype.slice.call(tbody.querySelectorAll('tr')) : [];
        var ps = parseInt(root.getAttribute('data-page-size') || '20', 10);
        root._ctState = {
          allRows: allRows,
          filteredRows: allRows.slice(),
          pageSize: isNaN(ps) ? 20 : ps,
          page: 1,
          sortCol: -1,
          sortDir: 0,
          query: ''
        };
      }
      return root;
    };

    window._ctTblRender = function(id) {
      var root = window._ctTblEnsure(id);
      if (!root) return;
      var st = root._ctState;
      var total = st.filteredRows.length;
      var ps = st.pageSize <= 0 ? (total || 1) : st.pageSize;
      var maxPage = Math.max(1, Math.ceil(total / ps));
      if (st.page > maxPage) st.page = maxPage;
      if (st.page < 1) st.page = 1;
      var start = (st.page - 1) * ps;
      var end = Math.min(total, start + ps);
      var tbody = root.querySelector('tbody');
      if (tbody) {
        while (tbody.firstChild) tbody.removeChild(tbody.firstChild);
        for (var i = start; i < end; i++) {
          tbody.appendChild(st.filteredRows[i]);
        }
      }
      var info = root.querySelector('.ct-page-info');
      if (info) {
        var capNote = root.getAttribute('data-cap-note') || '';
        info.textContent = (total === 0 ? '0 rows' : ('Rows ' + (start + 1) + '–' + end + ' of ' + total))
          + ' (Page ' + st.page + '/' + maxPage + ')' + (capNote ? ' · ' + capNote : '');
      }
      var btns = root.querySelectorAll('.ct-pg-btn');
      if (btns.length === 4) {
        btns[0].disabled = (st.page <= 1);
        btns[1].disabled = (st.page <= 1);
        btns[2].disabled = (st.page >= maxPage);
        btns[3].disabled = (st.page >= maxPage);
      }
    };

    window._ctTblFilter = function(id, q) {
      var root = window._ctTblEnsure(id);
      if (!root) return;
      var st = root._ctState;
      st.query = (q || '').trim().toLowerCase();
      if (!st.query) {
        st.filteredRows = st.allRows.slice();
      } else {
        st.filteredRows = st.allRows.filter(function(tr) {
          return (tr.textContent || '').toLowerCase().indexOf(st.query) !== -1;
        });
      }
      if (st.sortCol >= 0 && st.sortDir !== 0) {
        window._ctTblApplySort(root);
      }
      st.page = 1;
      window._ctTblRender(id);
    };

    window._ctTblApplySort = function(root) {
      var st = root._ctState;
      var col = st.sortCol;
      var dir = st.sortDir;
      var ths = root.querySelectorAll('thead th');
      var isNum = ths[col] && ths[col].getAttribute('data-type') === 'num';
      st.filteredRows.sort(function(ra, rb) {
        var ca = ra.children[col];
        var cb = rb.children[col];
        var va = ca ? (ca.getAttribute('data-val') || ca.textContent || '') : '';
        var vb = cb ? (cb.getAttribute('data-val') || cb.textContent || '') : '';
        if (isNum) {
          var na = parseFloat(va);
          var nb = parseFloat(vb);
          var aNan = isNaN(na);
          var bNan = isNaN(nb);
          if (aNan && bNan) return 0;
          if (aNan) return 1;
          if (bNan) return -1;
          return (na - nb) * dir;
        }
        var cmp = trCollator ? trCollator.compare(va, vb) : va.localeCompare(vb);
        return cmp * dir;
      });
    };

    window._ctTblSort = function(id, col, ev) {
      if (ev && ev.target && ev.target.classList.contains('ct-col-resizer')) return;
      var root = window._ctTblEnsure(id);
      if (!root) return;
      var st = root._ctState;
      if (st.sortCol === col) {
        st.sortDir = st.sortDir === 1 ? -1 : (st.sortDir === -1 ? 0 : 1);
      } else {
        st.sortCol = col;
        st.sortDir = 1;
      }
      var ths = root.querySelectorAll('thead th');
      ths.forEach(function(th, idx) {
        th.classList.remove('sorted-asc', 'sorted-desc');
        var ind = th.querySelector('.sort-ind');
        if (!ind) return;
        if (idx === st.sortCol && st.sortDir !== 0) {
          th.classList.add(st.sortDir === 1 ? 'sorted-asc' : 'sorted-desc');
          ind.textContent = st.sortDir === 1 ? '▲' : '▼';
        } else {
          ind.textContent = '⇅';
        }
      });
      if (st.sortDir === 0) {
        window._ctTblFilter(id, st.query);
        return;
      }
      window._ctTblApplySort(root);
      st.page = 1;
      window._ctTblRender(id);
    };

    window._ctTblPage = function(id, action) {
      var root = window._ctTblEnsure(id);
      if (!root) return;
      var st = root._ctState;
      var total = st.filteredRows.length;
      var ps = st.pageSize <= 0 ? (total || 1) : st.pageSize;
      var maxPage = Math.max(1, Math.ceil(total / ps));
      if (action === 'first') st.page = 1;
      else if (action === 'prev') st.page = Math.max(1, st.page - 1);
      else if (action === 'next') st.page = Math.min(maxPage, st.page + 1);
      else if (action === 'last') st.page = maxPage;
      window._ctTblRender(id);
    };

    window._ctTblPageSize = function(id, val) {
      var root = window._ctTblEnsure(id);
      if (!root) return;
      var st = root._ctState;
      st.pageSize = val === 'all' ? 0 : parseInt(val, 10);
      st.page = 1;
      window._ctTblRender(id);
    };

    window._ctTblLayout = function(id, mode, btn) {
      var root = window._ctTblEnsure(id);
      if (!root) return;
      root.classList.remove('layout-wrap', 'layout-compact', 'layout-fixed');
      if (mode === 'wrap') root.classList.add('layout-wrap');
      else if (mode === 'compact') root.classList.add('layout-compact');
      else if (mode === 'auto') {
        root.querySelectorAll('thead th').forEach(function(th) { th.style.width = ''; });
      }
      if (btn && btn.parentElement) {
        btn.parentElement.querySelectorAll('.ct-layout-btn').forEach(function(b) {
          b.classList.remove('active');
        });
        btn.classList.add('active');
      }
    };

    window._ctTblStartResize = function(ev, id, colIdx) {
      ev.stopPropagation();
      ev.preventDefault();
      var root = window._ctTblEnsure(id);
      if (!root) return;
      var ths = root.querySelectorAll('thead th');
      var th = ths[colIdx];
      if (!th) return;
      root.classList.add('layout-fixed');
      var startX = ev.clientX;
      var startW = th.getBoundingClientRect().width;
      function onMove(e) {
        var w = Math.max(48, startW + (e.clientX - startX));
        th.style.width = w + 'px';
      }
      function onUp() {
        document.removeEventListener('mousemove', onMove);
        document.removeEventListener('mouseup', onUp);
      }
      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', onUp);
    };

    window._ctTblAutoFitCol = function(ev, id, colIdx) {
      ev.stopPropagation();
      var root = window._ctTblEnsure(id);
      if (!root) return;
      var ths = root.querySelectorAll('thead th');
      if (ths[colIdx]) ths[colIdx].style.width = '';
    };

    window._ctTblCopyTsv = function(id, btn) {
      var root = window._ctTblEnsure(id);
      if (!root) return;
      var st = root._ctState;
      var headers = [];
      root.querySelectorAll('thead th .th-lbl').forEach(function(el) {
        headers.push((el.textContent || '').trim());
      });
      var lines = [headers.join('\\t')];
      st.filteredRows.forEach(function(tr) {
        var cells = [];
        Array.prototype.forEach.call(tr.children, function(td) {
          cells.push((td.textContent || '').replace(/[\\r\\n\\t]+/g, ' ').trim());
        });
        lines.push(cells.join('\\t'));
      });
      var tsv = lines.join('\\n');
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(tsv).then(function() {
          var old = btn.textContent;
          btn.textContent = '✓ Copied';
          setTimeout(function() { btn.textContent = old; }, 1200);
        });
      }
    };
  }
  setTimeout(function() {
    document.querySelectorAll('.ct-tbl-wrap[id]').forEach(function(el) {
      if (!el._ctState) window._ctTblRender(el.id);
    });
  }, 20);
})();
</script>
"""


def _is_numeric_dtype(s: pd.Series) -> bool:
    return bool(
        pd.api.types.is_numeric_dtype(s.dtype) and not pd.api.types.is_bool_dtype(s.dtype)
    )


def _format_cell(val: Any, is_num: bool, precision: int) -> tuple[str, str]:
    """Return ``(raw_sort_value, display_html)``."""
    if val is None or (isinstance(val, float) and (math.isnan(val) or math.isinf(val))):
        return ("NaN", "—")
    try:
        if pd.isna(val):
            return ("NaN", "—")
    except Exception:  # noqa: BLE001
        pass
    if is_num and isinstance(val, (int, float, np.number)) and not isinstance(val, bool):
        fval = float(val)
        if math.isnan(fval) or math.isinf(fval):
            return ("NaN", "—")
        if isinstance(val, (int, np.integer)) or (fval.is_integer() and abs(fval) < 1e12 and "." not in str(val)):
            return (str(int(round(fval))), f"{int(round(fval)):,}")
        return (f"{fval:.8g}", f"{fval:,.{precision}f}")
    s = str(val)
    return (s, esc(s))


def table_html(
    df_or_conc: Any,
    page_size: int = 20,
    title: str | None = None,
    layout: str = "auto",
    precision: int = 3,
    max_rows: int = 2000,
    include_index: bool | None = None,
) -> str:
    """Render a :class:`pandas.DataFrame` or :class:`ConcordanceResult` as an interactive paged HTML table.

    Parameters
    ----------
    df_or_conc:
        A :class:`pandas.DataFrame` or an object exposing ``.to_dataframe()`` (such as
        :class:`~corpus_toolkit.kwic.ConcordanceResult`).
    page_size:
        Default number of rows per page (default ``20``; user can switch ``10 / 20 / 50 / 100 / All``).
    title:
        Optional header title shown in the table toolbar.
    layout:
        Initial layout preset: ``'auto'`` (Auto-Fit), ``'wrap'`` (Wrap Text), or ``'compact'`` (Compact).
    precision:
        Decimal places for floating-point cells.
    max_rows:
        Safety cap on serialized HTML rows to prevent Jupyter IOPub payload overflow.
    include_index:
        Whether to include the DataFrame index as the first column. By default included when the
        index has a name or is not a default ``RangeIndex``.
    """
    if hasattr(df_or_conc, "to_dataframe"):
        df = df_or_conc.to_dataframe()
        if title is None and hasattr(df_or_conc, "query_description"):
            title = f"Concordance — {df_or_conc.query_description}"
    elif isinstance(df_or_conc, pd.Series):
        df = df_or_conc.to_frame()
    elif isinstance(df_or_conc, pd.DataFrame):
        df = df_or_conc.copy()
    else:
        df = pd.DataFrame(df_or_conc)

    if include_index is None:
        include_index = bool(df.index.name) or not isinstance(df.index, pd.RangeIndex)
    if include_index:
        df = df.reset_index()

    total_df_rows = len(df)
    capped = total_df_rows > max_rows
    if capped:
        df = df.iloc[:max_rows]
    cap_note = f"showing first {max_rows:,} of {total_df_rows:,} total rows" if capped else ""

    uid = f"ct-tbl-{uuid.uuid4().hex[:8]}"
    cols = [str(c) for c in df.columns]
    num_flags = [_is_numeric_dtype(df.iloc[:, idx]) for idx in range(len(cols))]

    th_cells: list[str] = []
    for c_idx, (c_name, is_num) in enumerate(zip(cols, num_flags)):
        dtype_attr = "num" if is_num else "str"
        align_style = ' style="text-align:right"' if is_num else ""
        th_cells.append(
            f'<th data-col="{c_idx}" data-type="{dtype_attr}"{align_style} '
            f'onclick="window._ctTblSort(\'{uid}\',{c_idx},event)" '
            f'title="Click to sort ascending / descending / reset · Drag right edge to resize">'
            f'<span class="th-lbl">{esc(c_name)}</span><span class="sort-ind">⇅</span>'
            f'<span class="ct-col-resizer" '
            f'onmousedown="window._ctTblStartResize(event,\'{uid}\',{c_idx})" '
            f'ondblclick="window._ctTblAutoFitCol(event,\'{uid}\',{c_idx})"></span></th>'
        )

    body_rows: list[str] = []
    for row_vals in df.itertuples(index=False, name=None):
        tds: list[str] = []
        for c_idx, val in enumerate(row_vals):
            is_num = num_flags[c_idx]
            raw_v, disp_v = _format_cell(val, is_num, precision)
            cls_attr = ' class="num"' if is_num else ""
            title_attr = f' title="{esc(str(val))}"' if (not is_num and val is not None and len(str(val)) > 28) else ""
            tds.append(f'<td{cls_attr} data-val="{esc(raw_v)}"{title_attr}>{disp_v}</td>')
        body_rows.append(f"<tr>{''.join(tds)}</tr>")

    layout_cls = {"wrap": " layout-wrap", "compact": " layout-compact"}.get(layout, "")
    title_html = f'<span class="ct-tbl-title">📊 {esc(title)}</span>' if title else '<span class="ct-tbl-title">📊 Table View</span>'

    size_opts = []
    for opt_val, opt_lbl in ((10, "10 / page"), (20, "20 / page"), (50, "50 / page"), (100, "100 / page"), (0, "All rows")):
        sel = " selected" if opt_val == page_size else ""
        val_str = "all" if opt_val == 0 else str(opt_val)
        size_opts.append(f'<option value="{val_str}"{sel}>{opt_lbl}</option>')

    n_shown = min(len(body_rows), page_size if page_size > 0 else len(body_rows))
    max_pg = max(1, math.ceil(len(body_rows) / (page_size if page_size > 0 else max(len(body_rows), 1))))
    init_info = (
        "0 rows (Page 1/1)"
        if not body_rows
        else f"Rows 1–{n_shown} of {len(body_rows)} (Page 1/{max_pg})"
        + (f" · {cap_note}" if cap_note else "")
    )

    toolbar = (
        f'<div class="ct-tbl-bar">'
        f"<div>{title_html}</div>"
        f'<div class="ct-tbl-ctrls">'
        f'<input type="search" class="ct-tbl-input" placeholder="Filter rows…" '
        f'oninput="window._ctTblFilter(\'{uid}\',this.value)">'
        f'<select class="ct-tbl-select" onchange="window._ctTblPageSize(\'{uid}\',this.value)" title="Rows per page">'
        f'{"".join(size_opts)}</select>'
        f'<button type="button" class="ct-tbl-btn ct-layout-btn{" active" if layout == "auto" else ""}" '
        f'onclick="window._ctTblLayout(\'{uid}\',\'auto\',this)">Auto-Fit</button>'
        f'<button type="button" class="ct-tbl-btn ct-layout-btn{" active" if layout == "wrap" else ""}" '
        f'onclick="window._ctTblLayout(\'{uid}\',\'wrap\',this)">Wrap Text</button>'
        f'<button type="button" class="ct-tbl-btn ct-layout-btn{" active" if layout == "compact" else ""}" '
        f'onclick="window._ctTblLayout(\'{uid}\',\'compact\',this)">Compact</button>'
        f'<button type="button" class="ct-tbl-btn" onclick="window._ctTblCopyTsv(\'{uid}\',this)">📋 Copy TSV</button>'
        f"</div></div>"
    )

    footer = (
        f'<div class="ct-tbl-foot">'
        f'<div class="ct-page-info">{esc(init_info)}</div>'
        f'<div class="ct-tbl-pager">'
        f'<button type="button" class="ct-tbl-btn ct-pg-btn" onclick="window._ctTblPage(\'{uid}\',\'first\')">⏮ First</button>'
        f'<button type="button" class="ct-tbl-btn ct-pg-btn" onclick="window._ctTblPage(\'{uid}\',\'prev\')">◀ Prev</button>'
        f'<button type="button" class="ct-tbl-btn ct-pg-btn" onclick="window._ctTblPage(\'{uid}\',\'next\')">Next ▶</button>'
        f'<button type="button" class="ct-tbl-btn ct-pg-btn" onclick="window._ctTblPage(\'{uid}\',\'last\')">Last ⏭</button>'
        f"</div></div>"
    )

    return (
        f'<div class="ct ct-tbl-wrap{layout_cls}" id="{uid}" data-page-size="{page_size}" '
        f'data-cap-note="{esc(cap_note)}">'
        f"{toolbar}"
        f'<div class="ct-tbl-scroll">'
        f'<table class="ct-grid"><thead><tr>{"".join(th_cells)}</tr></thead>'
        f'<tbody>{"".join(body_rows)}</tbody></table>'
        f"</div>"
        f"{footer}{TABLE_JS}</div>"
    )


def show_table(
    df_or_conc: Any,
    page_size: int = 20,
    title: str | None = None,
    layout: str = "auto",
    precision: int = 3,
    max_rows: int = 2000,
    include_index: bool | None = None,
) -> None:
    """Display ``df_or_conc`` as an interactive paginated, sortable, resizable HTML table in Jupyter."""
    try:
        from IPython.display import HTML, display

        display(
            HTML(
                CSS
                + TABLE_CSS
                + table_html(
                    df_or_conc,
                    page_size=page_size,
                    title=title,
                    layout=layout,
                    precision=precision,
                    max_rows=max_rows,
                    include_index=include_index,
                )
            )
        )
    except ImportError:  # pragma: no cover
        if hasattr(df_or_conc, "to_dataframe"):
            print(df_or_conc.to_dataframe().head(page_size).to_string())
        else:
            print(pd.DataFrame(df_or_conc).head(page_size).to_string())


_ORIG_DF_REPR_HTML: Any = None


def enable_interactive_tables(page_size: int = 20, precision: int = 3, max_rows: int = 2000) -> None:
    """Register :func:`table_html` as the default IPython HTML formatter for :class:`pandas.DataFrame`."""
    global _ORIG_DF_REPR_HTML
    if _ORIG_DF_REPR_HTML is None:
        _ORIG_DF_REPR_HTML = getattr(pd.DataFrame, "_repr_html_", None)

    def _custom_repr_html(self: pd.DataFrame) -> str:
        return CSS + TABLE_CSS + table_html(self, page_size=page_size, precision=precision, max_rows=max_rows)

    pd.DataFrame._repr_html_ = _custom_repr_html  # type: ignore[attr-defined, method-assign]


def disable_interactive_tables() -> None:
    """Restore pandas' original ``DataFrame._repr_html_`` implementation."""
    global _ORIG_DF_REPR_HTML
    if _ORIG_DF_REPR_HTML is not None:
        pd.DataFrame._repr_html_ = _ORIG_DF_REPR_HTML  # type: ignore[attr-defined, method-assign]
        _ORIG_DF_REPR_HTML = None


__all__ = [
    "TABLE_CSS",
    "TABLE_JS",
    "table_html",
    "show_table",
    "enable_interactive_tables",
    "disable_interactive_tables",
]
