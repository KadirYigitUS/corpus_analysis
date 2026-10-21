"""Side-by-side aligned parallel-corpus view (English source ⇄ Turkish translation).

Layout and data flow are imported from the Neologism Dictionary Annotation (NDA) tool
(``scripts/Neologism_Dictionary_Annotation/app/views/html_annotation_view/js/ui_render.js``
and ``selection.js``) and extended for static/interactive Jupyter rendering:

* one table row per **sentence**, grouped by alignment id (``ai``), with ``C P S`` coordinate columns
  on each side (NDA's ``meta-eng`` / ``meta-tur`` columns);
* 1:N / N:1 groups use **rowspan** so a split or merged sentence visibly spans its counterparts,
  and 1:0 / 0:1 omissions/additions show an explicit empty counterpart cell;
* every token is a **2-tier vertical pill** displaying surface ``tok`` on the top line and
  ``lem · UPOS`` on a toggleable bottom sub-label, plus a rich hover tooltip with full morphology,
  dependency, NER, neologism candidate score breakdown, and NDA dictionary tags;
* **4 disjoint visual sets** following NDA's ``selection.js`` & ``ui_render.js`` hierarchy:
  1. **Linked Bilingual Pairs** (``manual`` / curated ``auto``): sky-blue highlight, ``L1..Lk`` badge,
     and **relative-stage SVG connector lines** linking the first EN token and first TR token of each
     ``L#`` link within an alignment row ``ai``.
  2. **Unlinked Single-Language Irrealia** (``single_eng`` teal / ``single_tur`` rose): category badge
     without a bilingual ``L#`` link number.
  3. **High-Salience Neologism Candidates** from ``scored_alignment_rows.pickle``: soft amber highlight
     with candidate score tooltip/badge.
  4. **Search Query Hits**: crimson outline and rose pill highlight.
* **Layer 0 Realia vs. Top-Layer Irrealia** ordering: ``SCIFI_*`` Irrealia tags take top visual priority,
  while standard ``NER`` tags (``PERSON``, ``LOC``, ``ORG``, ``PRODUCT``) appear as toggleable Layer 0
  badges;
* **Current Label Attributions (``.nda-summary-footer``)** at the bottom of each ``ai`` group summarizing
  linked bilingual pairs, single-language irrealia / top candidates, and sentence cardinality + token
  expansion ratio ($N_{\text{TR}} / N_{\text{EN}}$).

Data flow::

    *_sentence_map_{eng,tur}.pickle ─► AlignmentIndex.coords(ai) ─► (ch, p, s) per sentence
    <code>.pickle.xz (tokens + sentences frames) ─► tokens[start:start+ntok] (tok, lem, pos, morph, dep, ner)
    NDA scored_alignment_rows.pickle + initial_dictionary.pickle ─► NdaOverlay (memoized per pair_id)
"""

from __future__ import annotations

import colorsys
import importlib.util
import pickle
import re
import sys
import types
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .style import badge, esc

PV_CSS = """
<style>
.pv { margin: 10px 0; }
.pv .pv-toolbar { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; justify-content: space-between;
                  background: #f8fafc; border: 1px solid #cbd5e1; border-bottom: none;
                  padding: 7px 12px; border-radius: 8px 8px 0 0; font-size: 12px; }
.pv .pv-toolbar .pv-toggles { display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }
.pv .pv-btn { cursor: pointer; border: 1px solid #cbd5e1; background: #ffffff; color: #334155;
              border-radius: 6px; padding: 3px 9px; font-size: 11.5px; font-weight: 600;
              transition: all .12s ease; user-select: none; }
.pv .pv-btn.active { background: #e0e7ff; color: #1e40af; border-color: #818cf8; }
.pv .pv-btn:hover { background: #f1f5f9; }
.pv .nda-table-stage { position: relative; overflow-x: auto; border: 1px solid #cbd5e1;
                       border-radius: 0 0 8px 8px; background: #ffffff; }
.pv .nda-link-svg { position: absolute; inset: 0; width: 100%; height: 100%;
                    pointer-events: none; overflow: visible; z-index: 3; }
.pv.hide-svg .nda-link-svg { display: none; }
.pv table.pv-grid { border-collapse: collapse; width: 100%; table-layout: fixed; position: relative; z-index: 2; }
.pv table.pv-grid th { background: #f1f5f9; padding: 7px 10px; font-size: 12px; text-align: left;
                       border-bottom: 2px solid #cbd5e1; position: sticky; top: 0; z-index: 4; }
.pv table.pv-grid td { border-top: 1px solid #e2e8f0; padding: 7px 10px; vertical-align: top; line-height: 1.55; }
.pv td.ai { width: 88px; font: 11px 'DejaVu Sans Mono', monospace; color: #334155;
            background: #f8fafc; border-right: 1px solid #e2e8f0; }
.pv td.cps { width: 72px; font: 11px 'DejaVu Sans Mono', monospace; white-space: nowrap;
             background: #fcfdff; border-right: 1px solid #eef2f6; }
.pv td.cps.en { color: #0e7490; font-weight: 600; }
.pv td.cps.tr { color: #b45309; font-weight: 600; }
.pv td.sent.en { background: rgba(207, 250, 254, .18); border-right: 2px solid #cbd5e1; }
.pv td.sent.tr { background: rgba(254, 243, 199, .20); }
.pv td.none { color: #94a3b8; font-style: italic; text-align: center; background: #f8fafc; }
.pv .tok-stream { display: flex; flex-wrap: wrap; gap: 3px 4px; align-items: flex-start; }
.pv .t { display: inline-flex; flex-direction: column; align-items: center; padding: 2px 5px;
         border-radius: 5px; border: 1px solid transparent; border-bottom: 2px solid transparent;
         cursor: help; position: relative; transition: transform .08s ease, box-shadow .12s ease;
         background: rgba(255, 255, 255, .65); }
.pv .t:hover { transform: translateY(-1px); box-shadow: 0 2px 5px rgba(15, 23, 42, .12); z-index: 5; }
.pv .t.fw { opacity: .68; }
.pv .t .surf { font-size: 13.5px; line-height: 1.25; color: #0f172a; white-space: nowrap; }
.pv .t .sub { font-size: 9.5px; font-family: 'DejaVu Sans Mono', monospace; color: #64748b;
              line-height: 1.15; margin-top: 1px; white-space: nowrap; }
.pv.hide-lemma .t .sub { display: none; }
.pv .t .ner-b { font-size: 8.5px; font-family: 'DejaVu Sans Mono', monospace; font-weight: 700;
                padding: 0 4px; border-radius: 3px; background: #e2e8f0; color: #475569;
                margin-top: 1px; white-space: nowrap; }
.pv.hide-ner .t .ner-b { display: none; }
.pv .t.NOUN { border-bottom-color: #60a5fa; }
.pv .t.VERB { border-bottom-color: #f87171; }
.pv .t.ADJ  { border-bottom-color: #34d399; }
.pv .t.ADV  { border-bottom-color: #fbbf24; }
.pv .t.PROPN { border-bottom-color: #a78bfa; }
.pv .t.lk { background: #bfdbfe; border-color: #3b82f6; border-bottom-width: 2px; font-weight: 600; }
.pv .t.single-en { background: #99f6e4; border-color: #0d9488; font-weight: 600; }
.pv .t.single-tr { background: #fecdd3; border-color: #e11d48; font-weight: 600; }
.pv .t.cand { background: #fef08a; border-color: #eab308; }
.pv.hide-cand .t.cand:not(.lk):not(.single-en):not(.single-tr):not(.hit) {
    background: rgba(255, 255, 255, .65); border-color: transparent; }
.pv .t.hit { outline: 2px solid #e11d48; background: #ffe0e6 !important; font-weight: 700; }
.pv .t.lk-hover { box-shadow: 0 0 0 3px rgba(59, 130, 246, .45); transform: translateY(-1px); }
.pv sup.lk-b { font-size: 9px; font-weight: 700; padding: 0 3px; border-radius: 4px;
               background: #1d4ed8; color: #ffffff; margin-left: 2px; line-height: 1.1; }
.pv sup.irr-b { font-size: 8.5px; font-weight: 700; padding: 0 3px; border-radius: 4px;
                background: #0f766e; color: #ffffff; margin-left: 2px; line-height: 1.1; }
.pv .t.single-tr sup.irr-b { background: #be123c; }
.pv .ty { display: inline-block; margin-top: 3px; padding: 1px 5px; border-radius: 4px;
          background: #e2e8f0; color: #1e293b; font-size: 10px; font-weight: 700; }
.pv .exp-b { display: block; margin-top: 3px; font-size: 10px; color: #64748b; }
.pv tr.nda-summary-row td { background: #f8fafc; border-top: 1px dashed #cbd5e1;
                            border-bottom: 2px solid #cbd5e1; padding: 5px 10px; font-size: 11.5px; }
.pv .nda-summary-footer { display: flex; flex-wrap: wrap; gap: 6px 14px; align-items: center; color: #334155; }
.pv .nda-summary-footer .sf-group { display: inline-flex; flex-wrap: wrap; gap: 5px; align-items: center; }
.pv .nda-summary-footer .sf-pill { display: inline-block; padding: 1px 7px; border-radius: 999px;
                                   font-size: 11px; font-weight: 600; border: 1px solid transparent; }
.pv .sf-pill.sf-link { background: #dbeafe; color: #1e40af; border-color: #93c5fd; }
.pv .sf-pill.sf-en { background: #ccfbf1; color: #115e59; border-color: #5eead4; }
.pv .sf-pill.sf-tr { background: #ffe4e6; color: #9f1239; border-color: #fda4af; }
.pv .sf-pill.sf-cand { background: #fef9c3; color: #854d0e; border-color: #fde047; }
.pv .sf-pill.sf-stat { background: #f1f5f9; color: #475569; border-color: #cbd5e1;
                       font-family: 'DejaVu Sans Mono', monospace; }
.pv .legend { margin: 6px 2px; font-size: 11.5px; line-height: 1.8; color: #475569;
              display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.pv .legend .lg-item { display: inline-flex; align-items: center; gap: 4px; padding: 1px 8px;
                       border-radius: 6px; font-weight: 600; font-size: 11px; border: 1px solid transparent; }
</style>
"""

PV_JS = """
<script>
(function() {
  if (!window._ctPvDrawLinks) {
    window._ctPvDrawLinks = function(stageId) {
      var stage = document.getElementById(stageId);
      if (!stage) return;
      var root = stage.closest('.pv');
      var svg = stage.querySelector('svg.nda-link-svg');
      if (!svg) return;
      while (svg.firstChild) svg.removeChild(svg.firstChild);
      if (root && root.classList.contains('hide-svg')) return;
      var sr = stage.getBoundingClientRect();
      if (sr.width === 0 || sr.height === 0) return;
      svg.setAttribute('width', stage.scrollWidth);
      svg.setAttribute('height', stage.scrollHeight);
      var enAnchors = stage.querySelectorAll('.t[data-link-first][data-lang="en"]');
      enAnchors.forEach(function(enEl) {
        var lid = enEl.getAttribute('data-link-first');
        var ai = enEl.getAttribute('data-ai');
        var color = enEl.getAttribute('data-link-color') || '#3b82f6';
        var trEl = stage.querySelector('.t[data-link-first="' + lid + '"][data-lang="tr"][data-ai="' + ai + '"]');
        if (!trEl) return;
        var r1 = enEl.getBoundingClientRect();
        var r2 = trEl.getBoundingClientRect();
        var x1 = (r1.right - sr.left) + stage.scrollLeft;
        var y1 = (r1.top + r1.height / 2 - sr.top) + stage.scrollTop;
        var x2 = (r2.left - sr.left) + stage.scrollLeft;
        var y2 = (r2.top + r2.height / 2 - sr.top) + stage.scrollTop;
        var midX = (x1 + x2) / 2;
        var path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        var d = 'M ' + x1.toFixed(1) + ' ' + y1.toFixed(1) +
                ' C ' + midX.toFixed(1) + ' ' + y1.toFixed(1) + ', ' +
                        midX.toFixed(1) + ' ' + y2.toFixed(1) + ', ' +
                        x2.toFixed(1) + ' ' + y2.toFixed(1);
        path.setAttribute('d', d);
        path.setAttribute('fill', 'none');
        path.setAttribute('stroke', color);
        path.setAttribute('stroke-width', '2');
        path.setAttribute('stroke-dasharray', '4,2');
        path.setAttribute('opacity', '0.72');
        svg.appendChild(path);
        [[x1, y1], [x2, y2]].forEach(function(pt) {
          var c = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
          c.setAttribute('cx', pt[0].toFixed(1));
          c.setAttribute('cy', pt[1].toFixed(1));
          c.setAttribute('r', '3');
          c.setAttribute('fill', color);
          svg.appendChild(c);
        });
      });
    };
    window._ctPvToggle = function(btn, stageId, clsName) {
      var stage = document.getElementById(stageId);
      if (!stage) return;
      var root = stage.closest('.pv');
      if (!root) return;
      root.classList.toggle(clsName);
      btn.classList.toggle('active');
      window._ctPvDrawLinks(stageId);
    };
    window._ctPvHoverLink = function(el, enter) {
      var stage = el.closest('.nda-table-stage');
      if (!stage) return;
      var lid = el.getAttribute('data-link-id');
      var ai = el.getAttribute('data-ai');
      if (!lid) return;
      stage.querySelectorAll('.t[data-link-id="' + lid + '"][data-ai="' + ai + '"]').forEach(function(peer) {
        if (enter) peer.classList.add('lk-hover');
        else peer.classList.remove('lk-hover');
      });
    };
    window.addEventListener('resize', function() {
      document.querySelectorAll('.nda-table-stage[id]').forEach(function(st) {
        window._ctPvDrawLinks(st.id);
      });
    });
  }
  setTimeout(function() {
    document.querySelectorAll('.nda-table-stage[id]').forEach(function(st) {
      window._ctPvDrawLinks(st.id);
    });
  }, 40);
})();
</script>
"""

_FUNCTION_POS = {"ADP", "AUX", "CCONJ", "SCONJ", "DET", "PART", "PRON", "PUNCT", "SYM", "X", "NUM"}
_TAG_RE = re.compile(r"^([A-Za-z0-9_]+)(?:\s*\[([^\]]+)\])?")
Coord = tuple[int, int, int]
TokenKey = tuple[str, int, int, int, int]


def _link_color(n: int) -> str:
    h, s, v = colorsys.hsv_to_rgb((n * 0.61803) % 1, 0.38, 0.98)
    return f"rgb({int(h * 255)},{int(s * 255)},{int(v * 255)})"


def _link_stroke(n: int) -> str:
    h, s, v = colorsys.hsv_to_rgb((n * 0.61803) % 1, 0.78, 0.78)
    return f"rgb({int(h * 255)},{int(s * 255)},{int(v * 255)})"


def _parse_tags(tags: list[str]) -> tuple[list[str], list[str]]:
    """Split NDA tags into Top-Layer Irrealia (``SCIFI_*``) and Layer 0 Realia (standard NER)."""
    irrealia: list[str] = []
    realia: list[str] = []
    for raw in tags:
        m = _TAG_RE.match(str(raw).strip())
        if not m:
            continue
        base, sub = m.group(1), m.group(2)
        label = f"{base}[{sub}]" if sub else base
        if base.startswith("SCIFI_"):
            irrealia.append(label)
        elif base != "O":
            realia.append(label)
    return irrealia, realia


class _NdaSafeUnpickler(pickle.Unpickler):
    """Resolve ``app.models.*`` classes against ``scripts/Neologism_Dictionary_Annotation``."""

    def __init__(self, file: Any, nda_root: Path) -> None:
        super().__init__(file)
        self._nda_root = nda_root

    def find_class(self, module: str, name: str) -> Any:
        if module.startswith("app."):
            rel = Path(*module.split(".")).with_suffix(".py")
            mod_path = self._nda_root / rel
            if mod_path.is_file() and module not in sys.modules:
                added = str(self._nda_root) not in sys.path
                if added:
                    sys.path.insert(0, str(self._nda_root))
                try:
                    spec = importlib.util.spec_from_file_location(module, mod_path)
                    if spec and spec.loader:
                        mod = importlib.util.module_from_spec(spec)
                        sys.modules[module] = mod
                        spec.loader.exec_module(mod)
                finally:
                    if added and str(self._nda_root) in sys.path:
                        sys.path.remove(str(self._nda_root))
        return super().find_class(module, name)


@dataclass
class TokenOverlayInfo:
    """Rich NDA metadata attached to a single sentence-local token ``(lang, ch, p, s, sent_idx)``."""

    visual_set: str = ""  # "linked" | "single_eng" | "single_tur" | "candidate" | ""
    link_no: int = 0
    link_label: str = ""  # e.g. "L1"
    link_type: str = ""  # "manual" | "auto" | "single_eng" | "single_tur"
    is_link_first: bool = False  # True for the first EN / first TR token of L# within its alignment row
    irrealia_tags: list[str] = field(default_factory=list)
    realia_tags: list[str] = field(default_factory=list)
    ner: str = ""
    dep: str = ""
    morph: str = ""
    neologism_score: float = 0.0
    score_breakdown: dict[str, float] = field(default_factory=dict)
    is_candidate: bool = False


@dataclass
class RowAttributionSummary:
    """Structured attribution footer for one alignment row ``ai``."""

    linked_pairs: list[tuple[int, str, str, str, str]] = field(default_factory=list)
    single_eng: list[tuple[str, str]] = field(default_factory=list)
    single_tur: list[tuple[str, str]] = field(default_factory=list)
    top_candidates: list[tuple[str, str, float]] = field(default_factory=list)


@dataclass
class NdaOverlay:
    """Read-only index of NDA dictionary links and scored candidate rows (memoized per ``pair_id``)."""

    tokens: dict[TokenKey, TokenOverlayInfo] = field(default_factory=dict)
    row_summaries: dict[int, RowAttributionSummary] = field(default_factory=dict)
    legend: dict[int, str] = field(default_factory=dict)
    status: str = "NDA overlay: not loaded"

    # Backward-compatibility alias mapping token coordinate -> link_no
    @property
    def cells(self) -> dict[TokenKey, int]:
        return {k: v.link_no for k, v in self.tokens.items() if v.link_no > 0}

    @classmethod
    def load(cls, loader: Any, pair_id: str) -> NdaOverlay:
        cached = _NDA_OVERLAY_CACHE.get(pair_id)
        if cached is not None:
            return cached
        cfg = loader.config
        cache_dir = cfg.thesis_root / "data" / "Neologism_Dictionary_Annotation_Cache" / pair_id
        dict_path = cache_dir / "initial_dictionary.pickle"
        rows_path = cache_dir / "scored_alignment_rows.pickle"
        if not dict_path.is_file() and not rows_path.is_file():
            ov = cls(status=f"NDA overlay: no cache directory for {pair_id}")
            _NDA_OVERLAY_CACHE[pair_id] = ov
            return ov

        nda_root = cfg.thesis_root / "scripts" / "Neologism_Dictionary_Annotation"
        added = [str(p) for p in (nda_root, cfg.thesis_root) if str(p) not in sys.path]
        sys.path[:0] = added
        orig_app = sys.modules.get("app")
        app_pkg = types.ModuleType("app")
        app_pkg.__path__ = [str(nda_root / "app")]
        sys.modules["app"] = app_pkg
        entries: list[Any] = []
        scored_rows: dict[int, Any] = {}
        try:
            if dict_path.is_file():
                with open(dict_path, "rb") as fh:
                    dm = _NdaSafeUnpickler(fh, nda_root).load()
                entries = list(getattr(dm, "entries", {}).values())
            if rows_path.is_file():
                with open(rows_path, "rb") as fh:
                    raw_rows = _NdaSafeUnpickler(fh, nda_root).load()
                if isinstance(raw_rows, dict):
                    scored_rows = raw_rows
        except Exception as exc:  # noqa: BLE001 - overlay is optional; never break the view
            ov = cls(status=f"NDA overlay unavailable ({type(exc).__name__})")
            _NDA_OVERLAY_CACHE[pair_id] = ov
            return ov
        finally:
            if orig_app is not None:
                sys.modules["app"] = orig_app
            else:
                sys.modules.pop("app", None)
            for p in added:
                if p in sys.path:
                    sys.path.remove(p)

        ov = cls()
        # 1. Hydrate baseline token scores, NER, DEP, and candidates from scored_alignment_rows.pickle
        for ai, row in scored_rows.items():
            row_cands: list[tuple[str, str, float]] = []
            for lang, tok_list in (("en", getattr(row, "eng_tokens", [])),
                                   ("tr", getattr(row, "tur_tokens", []))):
                sent_counters: dict[Coord, int] = {}
                for t in tok_list:
                    coord = (int(t.ch_no), int(t.p_no), int(t.s_no))
                    s_idx = int(getattr(t, "sent_idx", -1))
                    if s_idx < 0:
                        s_idx = sent_counters.get(coord, 0)
                    sent_counters[coord] = s_idx + 1

                    score = float(getattr(t, "neologism_score", 0.0) or 0.0)
                    bd = dict(getattr(t, "score_breakdown", {}) or {})
                    ner_raw = str(getattr(t, "ner", "") or "")
                    ner_clean = ner_raw.replace("B-", "").replace("I-", "") if ner_raw not in ("", "O") else ""
                    is_cand = bool(getattr(t, "is_neologism_candidate", False))
                    # Highlight high-salience candidates (unknown lemma, NER-bearing, or score >= 0.85)
                    salient_cand = is_cand and (
                        "unknown_lemma" in bd or bool(ner_clean) or score >= 0.85
                    )
                    key: TokenKey = (lang, coord[0], coord[1], coord[2], s_idx)
                    info = TokenOverlayInfo(
                        visual_set="candidate" if salient_cand else "",
                        ner=ner_clean,
                        dep=str(getattr(t, "dep", "") or ""),
                        morph=str(getattr(t, "morph", "") or ""),
                        neologism_score=score,
                        score_breakdown=bd,
                        is_candidate=salient_cand,
                    )
                    if ner_clean:
                        info.realia_tags.append(ner_clean)
                    ov.tokens[key] = info
                    if salient_cand:
                        row_cands.append((lang.upper(), str(getattr(t, "surface", "")), score))
            if row_cands:
                row_cands.sort(key=lambda x: x[2], reverse=True)
                ov.row_summaries.setdefault(int(ai), RowAttributionSummary()).top_candidates = row_cands[:5]

        # 2. Hydrate curated dictionary entries from initial_dictionary.pickle
        link_counter = 0
        single_counter = 0
        for e in entries:
            ltype = str(getattr(e, "link_type", "") or "manual")
            ai = int(getattr(e, "alignment_idx", -1))
            eng_toks = list(getattr(e, "eng_tokens", []) or [])
            tur_toks = list(getattr(e, "tur_tokens", []) or [])
            irr_tags, real_tags = _parse_tags(list(getattr(e, "tags", []) or []))
            summary = ov.row_summaries.setdefault(ai, RowAttributionSummary())
            en_str = " ".join(str(getattr(t, "surface", "")) for t in eng_toks)
            tr_str = " ".join(str(getattr(t, "surface", "")) for t in tur_toks)
            tag_label = irr_tags[0] if irr_tags else (real_tags[0] if real_tags else ltype)

            if ltype in ("manual", "auto") and eng_toks and tur_toks:
                link_counter += 1
                lno = link_counter
                ov.legend[lno] = f"{en_str} ⇄ {tr_str} ({tag_label})"
                summary.linked_pairs.append((lno, en_str, tr_str, tag_label, ltype))
                for lang, tlist in (("en", eng_toks), ("tr", tur_toks)):
                    # Sort by (ch_no, p_no, s_no, sent_idx) so the earliest token is the SVG anchor
                    sorted_t = sorted(
                        tlist,
                        key=lambda x: (int(x.ch_no), int(x.p_no), int(x.s_no), int(getattr(x, "sent_idx", 0))),
                    )
                    for idx_in_entry, t in enumerate(sorted_t):
                        key = (lang, int(t.ch_no), int(t.p_no), int(t.s_no), max(int(getattr(t, "sent_idx", 0)), 0))
                        info = ov.tokens.setdefault(key, TokenOverlayInfo())
                        info.visual_set = "linked"
                        info.link_no = lno
                        info.link_label = f"L{lno}"
                        info.link_type = ltype
                        if idx_in_entry == 0:
                            info.is_link_first = True
                        for tg in irr_tags:
                            if tg not in info.irrealia_tags:
                                info.irrealia_tags.append(tg)
                        for tg in real_tags:
                            if tg not in info.realia_tags:
                                info.realia_tags.append(tg)
            elif ltype == "single_eng" or (eng_toks and not tur_toks):
                single_counter += 1
                summary.single_eng.append((en_str, tag_label))
                for t in eng_toks:
                    key = ("en", int(t.ch_no), int(t.p_no), int(t.s_no), max(int(getattr(t, "sent_idx", 0)), 0))
                    info = ov.tokens.setdefault(key, TokenOverlayInfo())
                    if info.visual_set != "linked":
                        info.visual_set = "single_eng"
                        info.link_type = "single_eng"
                    for tg in irr_tags:
                        if tg not in info.irrealia_tags:
                            info.irrealia_tags.append(tg)
            elif ltype == "single_tur" or (tur_toks and not eng_toks):
                single_counter += 1
                summary.single_tur.append((tr_str, tag_label))
                for t in tur_toks:
                    key = ("tr", int(t.ch_no), int(t.p_no), int(t.s_no), max(int(getattr(t, "sent_idx", 0)), 0))
                    info = ov.tokens.setdefault(key, TokenOverlayInfo())
                    if info.visual_set != "linked":
                        info.visual_set = "single_tur"
                        info.link_type = "single_tur"
                    for tg in irr_tags:
                        if tg not in info.irrealia_tags:
                            info.irrealia_tags.append(tg)

        ov.status = (
            f"NDA overlay: {link_counter} linked pair(s), {single_counter} single-lang irrealia, "
            f"{len(scored_rows)} scored row(s)"
        )
        _NDA_OVERLAY_CACHE[pair_id] = ov
        return ov


_NDA_OVERLAY_CACHE: dict[str, NdaOverlay] = {}


def _resolve_pair(loader: Any, pair_or_code: Any) -> Any:
    """Accept a ``PairSpec``, a ``pair_id`` (``'I_Robot'``), or a book code (``'BR-SM'``, ``'IR-IA'``)."""
    if hasattr(pair_or_code, "pair_id") and hasattr(pair_or_code, "eng"):
        return pair_or_code
    key = str(pair_or_code).strip()
    if key in loader.registry.pairs:
        return loader.registry.pairs[key]
    for pid, p in loader.registry.pairs.items():
        if pid.lower() == key.lower():
            return p
        if f"{p.eng.code}_{p.tur.code}".lower() == key.lower():
            return p
    if "_" in key:
        first = key.split("_")[0]
        if first in loader.registry.texts:
            return loader.registry.pair_for(first)
    return loader.registry.pair_for(key)



def _sentence_cells(text: Any, coord: Coord) -> list[tuple[str, str, str, str]]:
    sent = text.sentences
    row = sent[(sent["ch_no"] == coord[0]) & (sent["p_no"] == coord[1]) & (sent["s_no"] == coord[2])]
    if row.empty:
        return []
    st, nt = int(row["start"].iat[0]), int(row["ntok"].iat[0])
    tab = text.tokens.iloc[st:st + nt]
    return list(zip(tab["tok"].astype(str), tab["lem"].astype(str), tab["pos"].astype(str),
                    tab["morph"].astype(str)))


def _normalize_hits(
    hits: set[tuple[str, int, int, int, int]] | set[str] | list[str] | None,
) -> tuple[set[TokenKey], set[str]]:
    if not hits:
        return set(), set()
    coord_hits: set[TokenKey] = set()
    term_hits: set[str] = set()
    for item in hits:
        if isinstance(item, tuple) and len(item) == 5:
            coord_hits.add(item)
        elif isinstance(item, str) and item.strip():
            term_hits.add(item.strip().lower())
    return coord_hits, term_hits


def _sentence_html(
    ai: int,
    lang: str,
    coord: Coord,
    cells: list[tuple[str, str, str, str]],
    ov: NdaOverlay,
    coord_hits: set[TokenKey],
    term_hits: set[str],
    used_links: set[int],
    emitted_first_anchors: set[tuple[str, int]],
) -> str:
    out: list[str] = []
    for i, (w, lem, pos, morph) in enumerate(cells):
        cls = ["t", pos]
        if pos in _FUNCTION_POS:
            cls.append("fw")
        key: TokenKey = (lang, coord[0], coord[1], coord[2], i)
        info = ov.tokens.get(key)
        style_parts: list[str] = []
        attrs: list[str] = [f'data-lang="{lang}"', f'data-ai="{ai}"', f'data-sent-idx="{i}"']
        badge_sup = ""
        ner_html = ""

        if info is not None:
            if info.visual_set == "linked" and info.link_no > 0:
                cls.append("lk")
                bg = _link_color(info.link_no)
                stroke = _link_stroke(info.link_no)
                style_parts.append(f"background:{bg};border-color:{stroke}")
                attrs.append(f'data-link-id="L{info.link_no}"')
                attrs.append(f'data-link-color="{stroke}"')
                attrs.append('onmouseenter="window._ctPvHoverLink(this,true)"')
                attrs.append('onmouseleave="window._ctPvHoverLink(this,false)"')
                anchor_key = (lang, info.link_no)
                if info.is_link_first and anchor_key not in emitted_first_anchors:
                    attrs.append(f'data-link-first="L{info.link_no}"')
                    emitted_first_anchors.add(anchor_key)
                irr_short = f"·{info.irrealia_tags[0].split('[')[0].replace('SCIFI_', '')}" if info.irrealia_tags else ""
                badge_sup = f'<sup class="lk-b">L{info.link_no}{esc(irr_short)}</sup>'
                used_links.add(info.link_no)
            elif info.visual_set == "single_eng":
                cls.append("single-en")
                lbl = info.irrealia_tags[0].replace("SCIFI_", "") if info.irrealia_tags else "IRREALIA"
                badge_sup = f'<sup class="irr-b">{esc(lbl)}</sup>'
            elif info.visual_set == "single_tur":
                cls.append("single-tr")
                lbl = info.irrealia_tags[0].replace("SCIFI_", "") if info.irrealia_tags else "IRREALIA"
                badge_sup = f'<sup class="irr-b">{esc(lbl)}</sup>'
            elif info.visual_set == "candidate":
                cls.append("cand")

            if info.realia_tags:
                ner_html = f'<span class="ner-b">{esc(info.realia_tags[0])}</span>'

        is_hit = key in coord_hits or (
            bool(term_hits) and (w.lower() in term_hits or lem.lower() in term_hits)
        )
        if is_hit:
            cls.append("hit")

        # Build rich NDA tooltip
        tip_parts = [f"Lemma: {lem}", f"POS: {pos}"]
        morph_str = (info.morph if info and info.morph else morph) or ""
        if morph_str and morph_str != "_":
            tip_parts.append(f"Morph: {morph_str}")
        if info:
            if info.dep:
                tip_parts.append(f"DEP: {info.dep}")
            if info.ner:
                tip_parts.append(f"NER: {info.ner}")
            if info.neologism_score > 0:
                bd_str = ", ".join(f"{k}:{v:.2f}" for k, v in info.score_breakdown.items())
                tip_parts.append(
                    f"Score: {info.neologism_score:.3f}" + (f" ({bd_str})" if bd_str else "")
                )
            all_tags = info.irrealia_tags + info.realia_tags
            if all_tags:
                tip_parts.append(f"Tags: {', '.join(all_tags)}")
        tip = esc(" | ".join(tip_parts))
        style_attr = f' style="{";".join(style_parts)}"' if style_parts else ""
        sub_txt = f"{lem}·{pos}" if pos not in ("PUNCT", "SYM") else pos
        out.append(
            f'<span class="{" ".join(cls)}" title="{tip}" {" ".join(attrs)}{style_attr}>'
            f'<span class="surf">{esc(w)}{badge_sup}</span>'
            f'<span class="sub">{esc(sub_txt)}</span>'
            f"{ner_html}</span>"
        )
    return f'<div class="tok-stream">{"".join(out)}</div>'


def _row_summary_html(
    ai: int,
    kind: str,
    en_tok_count: int,
    tr_tok_count: int,
    ov: NdaOverlay,
) -> str:
    ratio = f"{tr_tok_count / en_tok_count:.2f}x" if en_tok_count > 0 else "—"
    pills: list[str] = [
        f'<span class="sf-pill sf-stat">ai {ai} · {esc(kind)} · EN {en_tok_count} tok ⇄ TR {tr_tok_count} tok ({ratio})</span>'
    ]
    summary = ov.row_summaries.get(ai)
    if summary:
        for lno, en_s, tr_s, tag_lbl, ltype in summary.linked_pairs:
            pills.append(
                f'<span class="sf-pill sf-link">L{lno} [{esc(ltype)}]: '
                f"{esc(en_s)} ⇄ {esc(tr_s)} · {esc(tag_lbl)}</span>"
            )
        for en_s, tag_lbl in summary.single_eng:
            pills.append(
                f'<span class="sf-pill sf-en">Single-EN: {esc(en_s)} [{esc(tag_lbl)}]</span>'
            )
        for tr_s, tag_lbl in summary.single_tur:
            pills.append(
                f'<span class="sf-pill sf-tr">Single-TR: {esc(tr_s)} [{esc(tag_lbl)}]</span>'
            )
        for lang_lbl, surf, sc in summary.top_candidates[:3]:
            pills.append(
                f'<span class="sf-pill sf-cand">Cand ({esc(lang_lbl)}): {esc(surf)} ({sc:.2f})</span>'
            )
    return (
        f'<tr class="nda-summary-row"><td colspan="5">'
        f'<div class="nda-summary-footer"><div class="sf-group">{"".join(pills)}</div></div>'
        f"</td></tr>"
    )


def parallel_html(
    loader: Any,
    pair: Any,
    ais: list[int] | range,
    overlay: bool = True,
    hits: set[tuple[str, int, int, int, int]] | set[str] | list[str] | None = None,
    show_lemma: bool = True,
) -> str:
    """Render alignment groups ``ais`` of ``pair`` as an NDA-powered side-by-side table."""
    from .alignment import alignment_type

    pair_obj = _resolve_pair(loader, pair)
    idx = loader.alignment_index(pair_obj)
    en_t, tr_t = loader._lazy_for(pair_obj.eng), loader._lazy_for(pair_obj.tur)
    ov = NdaOverlay.load(loader, pair_obj.pair_id) if overlay else NdaOverlay(status="NDA overlay: off")
    coord_hits, term_hits = _normalize_hits(hits)
    used_links: set[int] = set()
    body: list[str] = []
    ai_list = list(ais)
    stage_id = f"nda-stage-{uuid.uuid4().hex[:8]}"

    for ai in ai_list:
        ce, ct = idx.coords(ai)
        ce, ct = sorted(ce), sorted(ct)
        n = max(len(ce), len(ct), 1)
        kind = alignment_type(len(ce), len(ct))
        en_cells_by_r = [_sentence_cells(en_t, (int(c[0]), int(c[1]), int(c[2]))) for c in ce]
        tr_cells_by_r = [_sentence_cells(tr_t, (int(c[0]), int(c[1]), int(c[2]))) for c in ct]
        en_tok_total = sum(len(x) for x in en_cells_by_r)
        tr_tok_total = sum(len(x) for x in tr_cells_by_r)
        ratio_str = f"{tr_tok_total / en_tok_total:.2f}x" if en_tok_total > 0 else "—"
        emitted_first_anchors: set[tuple[str, int]] = set()

        first = True
        for r in range(n):
            tds = []
            if first:
                tds.append(
                    f'<td class="ai" rowspan="{n}">ai {ai}'
                    f'<span class="ty">{esc(kind)}</span>'
                    f'<span class="exp-b">{en_tok_total}→{tr_tok_total} ({ratio_str})</span></td>'
                )
            for lang, coords, cells_list in (("en", ce, en_cells_by_r), ("tr", ct, tr_cells_by_r)):
                span_all = len(coords) == 1 and n > 1
                if span_all and r > 0:
                    continue
                rs = f' rowspan="{n}"' if span_all else ""
                if r < len(coords):
                    c = coords[r]
                    coord_tuple = (int(c[0]), int(c[1]), int(c[2]))
                    html_s = _sentence_html(
                        ai, lang, coord_tuple, cells_list[r], ov, coord_hits, term_hits,
                        used_links, emitted_first_anchors
                    )
                    tds.append(
                        f'<td class="cps {lang}"{rs}>{c[0]}:{c[1]}:{c[2]}</td>'
                        f'<td class="sent {lang}"{rs}>{html_s}</td>'
                    )
                else:
                    tds.append(f'<td class="cps {lang}"></td><td class="none">— no counterpart —</td>')
            body.append("<tr>" + "".join(tds) + "</tr>")
            first = False
        body.append(_row_summary_html(ai, kind, en_tok_total, tr_tok_total, ov))

    head = (
        "<tr><th style='width:88px'>Group</th><th style='width:72px'>C:P:S</th>"
        "<th>English (source)</th><th style='width:72px'>C:P:S</th>"
        "<th>Turkish (translation)</th></tr>"
    )
    legend_items = [
        '<span class="lg-item" style="background:#bfdbfe;border-color:#3b82f6">L# Linked Pair (EN⇄TR)</span>',
        '<span class="lg-item" style="background:#99f6e4;border-color:#0d9488">Single-EN Irrealia</span>',
        '<span class="lg-item" style="background:#fecdd3;border-color:#e11d48">Single-TR Irrealia</span>',
        '<span class="lg-item" style="background:#fef08a;border-color:#eab308">Salient Candidate</span>',
        '<span class="lg-item" style="background:#ffe0e6;border-color:#e11d48">Query Hit</span>',
    ]
    for n_link in sorted(used_links):
        if n_link in ov.legend:
            legend_items.append(
                f'<span class="lg-item" style="background:{_link_color(n_link)};'
                f'border-color:{_link_stroke(n_link)}">L{n_link} · {esc(ov.legend[n_link])}</span>'
            )

    root_cls = "ct pv" + ("" if show_lemma else " hide-lemma")
    lemma_btn_cls = "pv-btn active" if show_lemma else "pv-btn"
    toolbar = (
        f'<div class="pv-toolbar">'
        f'<div class="meta" style="margin:0">{badge("source")} ⇄ {badge("translation")} '
        f"<b>{esc(pair_obj.eng.title)}</b> [{esc(pair_obj.eng.code)}] ⇄ "
        f"<b>{esc(pair_obj.tur.title)}</b> [{esc(pair_obj.tur.code)}] · "
        f"{len(ai_list)} group(s) · {esc(ov.status)}</div>"
        f'<div class="pv-toggles">'
        f'<button type="button" class="pv-btn active" '
        f'onclick="window._ctPvToggle(this,\'{stage_id}\',\'hide-svg\')">🔗 SVG Links</button>'
        f'<button type="button" class="{lemma_btn_cls}" '
        f'onclick="window._ctPvToggle(this,\'{stage_id}\',\'hide-lemma\')">🔤 Lemmas &amp; POS</button>'
        f'<button type="button" class="pv-btn active" '
        f'onclick="window._ctPvToggle(this,\'{stage_id}\',\'hide-ner\')">🏷️ Layer 0 NER</button>'
        f'<button type="button" class="pv-btn active" '
        f'onclick="window._ctPvToggle(this,\'{stage_id}\',\'hide-cand\')">✨ Candidates</button>'
        f"</div></div>"
    )
    return (
        f'<div class="{root_cls}">{toolbar}'
        f'<div class="nda-table-stage" id="{stage_id}">'
        f'<svg class="nda-link-svg"></svg>'
        f'<table class="pv-grid">{head}{"".join(body)}</table>'
        f"</div>"
        f'<div class="legend">{"".join(legend_items)}</div>'
        f"{PV_JS}</div>"
    )


def hits_to_view(res: Any, loader: Any, max_groups: int = 8) -> str:
    """Parallel view of the alignment groups that contain the hits of a concordance."""
    from .style import CSS

    by_pair: dict[str, list[int]] = {}
    marks: set[tuple[str, int, int, int, int]] = set()
    for ln in res.lines:
        rec = loader.registry.texts[ln.code]
        if not rec.pair_id:
            continue
        idx = loader.alignment_index(loader.registry.pairs[rec.pair_id])
        ai = idx.ai_of(rec.language, (ln.ch_no, ln.p_no, ln.s_no))
        if ai is None:
            continue
        lst = by_pair.setdefault(rec.pair_id, [])
        if ai not in lst and len(lst) < max_groups:
            lst.append(ai)
        marks.add((rec.language, ln.ch_no, ln.p_no, ln.s_no, ln.node_index))
    if not by_pair:
        return CSS + PV_CSS + '<div class="ct"><div class="meta">No hit lies inside a translation pair.</div></div>'
    parts = [parallel_html(loader, loader.registry.pairs[pid], sorted(ais), hits=marks)
             for pid, ais in by_pair.items()]
    return CSS + PV_CSS + "".join(parts)


def show_parallel(
    loader: Any,
    pair_id: Any,
    ais: list[int] | range,
    overlay: bool = True,
    hits: set[tuple[str, int, int, int, int]] | set[str] | list[str] | None = None,
    show_lemma: bool = True,
) -> None:
    """Notebook helper: ``show_parallel(loader, 'I_Robot', range(10, 14))`` (also accepts ``'BR-SM'`` or a ``PairSpec``)."""
    from IPython.display import HTML, display

    from .style import CSS

    pair_obj = _resolve_pair(loader, pair_id)
    display(HTML(CSS + PV_CSS + parallel_html(loader, pair_obj, ais, overlay=overlay, hits=hits, show_lemma=show_lemma)))


__all__ = [
    "NdaOverlay",
    "TokenOverlayInfo",
    "RowAttributionSummary",
    "parallel_html",
    "hits_to_view",
    "show_parallel",
    "PV_CSS",
]
