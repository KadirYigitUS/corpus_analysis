/**
 * SVG Connector Drawing for Bilingual Parallel Corpora View (Tab 3).
 */
class SvgConnectorEngine {
  constructor(stageId, svgSelector = 'svg.nda-link-svg') {
    this.stageId = stageId;
    this.svgSelector = svgSelector;
  }

  drawLinks() {
    const stage = document.getElementById(this.stageId);
    if (!stage) return;
    const svg = stage.querySelector(this.svgSelector);
    if (!svg) return;

    // Clear previous paths
    while (svg.firstChild) svg.removeChild(svg.firstChild);

    const sr = stage.getBoundingClientRect();
    if (sr.width === 0 || sr.height === 0) return;

    svg.setAttribute('width', stage.scrollWidth);
    svg.setAttribute('height', stage.scrollHeight);

    const enAnchors = stage.querySelectorAll('.t-pill[data-link-first][data-lang="en"]');
    enAnchors.forEach(enEl => {
      const lid = enEl.getAttribute('data-link-first');
      const ai = enEl.getAttribute('data-ai');
      const color = enEl.getAttribute('data-link-color') || '#38bdf8';
      const trEl = stage.querySelector(`.t-pill[data-link-first="${lid}"][data-lang="tr"][data-ai="${ai}"]`);
      if (!trEl) return;

      const r1 = enEl.getBoundingClientRect();
      const r2 = trEl.getBoundingClientRect();

      const x1 = (r1.right - sr.left) + stage.scrollLeft;
      const y1 = (r1.top + r1.height / 2 - sr.top) + stage.scrollTop;
      const x2 = (r2.left - sr.left) + stage.scrollLeft;
      const y2 = (r2.top + r2.height / 2 - sr.top) + stage.scrollTop;
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

      [[x1, y1], [x2, y2]].forEach(pt => {
        const c = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        c.setAttribute('cx', pt[0].toFixed(1));
        c.setAttribute('cy', pt[1].toFixed(1));
        c.setAttribute('r', '3');
        c.setAttribute('fill', color);
        svg.appendChild(c);
      });
    });
  }

  attachResizeWatcher() {
    window.addEventListener('resize', () => {
      this.drawLinks();
    });
  }
}

window.SvgConnectorEngine = SvgConnectorEngine;
