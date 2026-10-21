/**
 * SVG Connector Drawing & PV_JS Global Handlers for Bilingual Parallel Corpora View (Tab 3).
 */
class SvgConnectorEngine {
  constructor(stageId, svgSelector = 'svg.nda-link-svg') {
    this.stageId = stageId;
    this.svgSelector = svgSelector;
  }

  static drawStageLinks(stageEl) {
    if (!stageEl) return;
    const root = stageEl.closest('.pv');
    const svg = stageEl.querySelector('svg.nda-link-svg');
    if (!svg) return;
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    if (root && root.classList.contains('hide-svg')) return;

    const sr = stageEl.getBoundingClientRect();
    if (sr.width === 0 || sr.height === 0) return;

    svg.setAttribute('width', stageEl.scrollWidth);
    svg.setAttribute('height', stageEl.scrollHeight);

    const enAnchors = stageEl.querySelectorAll('.t[data-link-first][data-lang="en"], .t-pill[data-link-first][data-lang="en"]');
    enAnchors.forEach((enEl) => {
      const lid = enEl.getAttribute('data-link-first');
      const ai = enEl.getAttribute('data-ai');
      const color = enEl.getAttribute('data-link-color') || '#3b82f6';
      const trEl = stageEl.querySelector(
        `.t[data-link-first="${lid}"][data-lang="tr"][data-ai="${ai}"], .t-pill[data-link-first="${lid}"][data-lang="tr"][data-ai="${ai}"]`
      );
      if (!trEl) return;

      const r1 = enEl.getBoundingClientRect();
      const r2 = trEl.getBoundingClientRect();

      const x1 = (r1.right - sr.left) + stageEl.scrollLeft;
      const y1 = (r1.top + r1.height / 2 - sr.top) + stageEl.scrollTop;
      const x2 = (r2.left - sr.left) + stageEl.scrollLeft;
      const y2 = (r2.top + r2.height / 2 - sr.top) + stageEl.scrollTop;
      const midX = (x1 + x2) / 2;

      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      const d = `M ${x1.toFixed(1)} ${y1.toFixed(1)} C ${midX.toFixed(1)} ${y1.toFixed(1)}, ${midX.toFixed(1)} ${y2.toFixed(1)}, ${x2.toFixed(1)} ${y2.toFixed(1)}`;
      path.setAttribute('d', d);
      path.setAttribute('fill', 'none');
      path.setAttribute('stroke', color);
      path.setAttribute('stroke-width', '2');
      path.setAttribute('stroke-dasharray', '4,2');
      path.setAttribute('opacity', '0.75');
      svg.appendChild(path);

      [[x1, y1], [x2, y2]].forEach((pt) => {
        const c = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        c.setAttribute('cx', pt[0].toFixed(1));
        c.setAttribute('cy', pt[1].toFixed(1));
        c.setAttribute('r', '3');
        c.setAttribute('fill', color);
        svg.appendChild(c);
      });
    });
  }

  drawLinks() {
    const outer = document.getElementById(this.stageId);
    if (!outer) return;
    const innerStages = outer.querySelectorAll('.nda-table-stage[id]');
    if (innerStages.length > 0) {
      innerStages.forEach((st) => SvgConnectorEngine.drawStageLinks(st));
    } else {
      SvgConnectorEngine.drawStageLinks(outer);
    }
  }

  attachResizeWatcher() {
    window.addEventListener('resize', () => {
      this.drawLinks();
    });
  }
}

window._ctPvDrawLinks = function (stageId) {
  const st = document.getElementById(stageId);
  if (st) SvgConnectorEngine.drawStageLinks(st);
};

window._ctPvToggle = function (btn, stageId, clsName) {
  const stage = document.getElementById(stageId);
  if (!stage) return;
  const root = stage.closest('.pv');
  if (!root) return;
  root.classList.toggle(clsName);
  btn.classList.toggle('active');
  window._ctPvDrawLinks(stageId);
};

window._ctPvHoverLink = function (el, enter) {
  const stage = el.closest('.nda-table-stage');
  if (!stage) return;
  const lid = el.getAttribute('data-link-id');
  const ai = el.getAttribute('data-ai');
  if (!lid) return;
  stage.querySelectorAll(`.t[data-link-id="${lid}"][data-ai="${ai}"]`).forEach((peer) => {
    if (enter) peer.classList.add('lk-hover');
    else peer.classList.remove('lk-hover');
  });
};

window.SvgConnectorEngine = SvgConnectorEngine;
