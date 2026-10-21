/**
 * chart_dumbbell_forest.js - Dumbbell plot and Forest plot with bootstrap CIs.
 */
(function(window) {
  'use strict';

  class ChartDumbbellForest extends window.ChartCore {
    renderDumbbell(items, leftKey = 'eng_pct', rightKey = 'tur_pct', labelKey = 'upos') {
      this.clear();
      const theme = this.getThemeColors();
      const p = this.plotArea();
      const maxVal = Math.max(1, ...items.flatMap(d => [Number(d[leftKey]) || 0, Number(d[rightKey]) || 0]));
      const n = items.length;
      const rowGap = p.h / Math.max(1, n);

      items.forEach((item, i) => {
        const y = p.y + i * rowGap + rowGap / 2;
        const x1 = p.x + ((Number(item[leftKey]) || 0) / maxVal) * p.w;
        const x2 = p.x + ((Number(item[rightKey]) || 0) / maxVal) * p.w;

        // Label
        this.ctx.font = '10px sans-serif';
        this.ctx.fillStyle = theme.text;
        this.ctx.textAlign = 'right';
        this.ctx.fillText(item[labelKey], p.x - 8, y + 3);

        // Connecting line
        this.ctx.strokeStyle = '#cbd5e1';
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();
        this.ctx.moveTo(x1, y);
        this.ctx.lineTo(x2, y);
        this.ctx.stroke();

        // English dot (cyan)
        this.ctx.fillStyle = '#06b6d4';
        this.ctx.beginPath();
        this.ctx.arc(x1, y, 5, 0, Math.PI * 2);
        this.ctx.fill();

        // Turkish dot (amber)
        this.ctx.fillStyle = '#f59e0b';
        this.ctx.beginPath();
        this.ctx.arc(x2, y, 5, 0, Math.PI * 2);
        this.ctx.fill();

        this.addHitBox(Math.min(x1, x2) - 6, y - 8, Math.abs(x2 - x1) + 12, 16,
          `<b>${item[labelKey]}</b><br/>EN: ${(item[leftKey] || 0).toFixed(1)}%<br/>TR: ${(item[rightKey] || 0).toFixed(1)}%`);
      });
    }

    renderForest(items, diffKey = 'mean_diff_pp', ciLowKey = 'ci_low', ciHighKey = 'ci_high', labelKey = 'upos') {
      this.clear();
      const theme = this.getThemeColors();
      const p = this.plotArea();
      const allVals = items.flatMap(d => [d[diffKey], d[ciLowKey], d[ciHighKey]].map(Number).filter(v => !isNaN(v)));
      const absMax = Math.max(0.5, ...allVals.map(Math.abs));
      const n = items.length;
      const rowGap = p.h / Math.max(1, n);
      const zeroX = p.x + p.w / 2;

      // Zero reference line
      this.ctx.strokeStyle = '#ef4444';
      this.ctx.lineWidth = 1;
      this.ctx.beginPath();
      this.ctx.moveTo(zeroX, p.y);
      this.ctx.lineTo(zeroX, p.y + p.h);
      this.ctx.stroke();

      items.forEach((item, i) => {
        const y = p.y + i * rowGap + rowGap / 2;
        const diff = Number(item[diffKey]) || 0;
        const low = Number(item[ciLowKey]) || diff;
        const high = Number(item[ciHighKey]) || diff;

        const xCenter = zeroX + (diff / absMax) * (p.w / 2);
        const xLow = zeroX + (low / absMax) * (p.w / 2);
        const xHigh = zeroX + (high / absMax) * (p.w / 2);

        // Label
        this.ctx.font = '10px sans-serif';
        this.ctx.fillStyle = theme.text;
        this.ctx.textAlign = 'right';
        this.ctx.fillText(item[labelKey], p.x - 8, y + 3);

        // Whisker line
        this.ctx.strokeStyle = '#94a3b8';
        this.ctx.lineWidth = 1.5;
        this.ctx.beginPath();
        this.ctx.moveTo(xLow, y);
        this.ctx.lineTo(xHigh, y);
        this.ctx.stroke();

        // Caps
        this.ctx.beginPath();
        this.ctx.moveTo(xLow, y - 3); this.ctx.lineTo(xLow, y + 3);
        this.ctx.moveTo(xHigh, y - 3); this.ctx.lineTo(xHigh, y + 3);
        this.ctx.stroke();

        // Point
        this.ctx.fillStyle = '#334155';
        this.ctx.beginPath();
        this.ctx.arc(xCenter, y, 4, 0, Math.PI * 2);
        this.ctx.fill();

        this.addHitBox(xLow - 4, y - 7, Math.abs(xHigh - xLow) + 8, 14,
          `<b>${item[labelKey]}</b><br/>Diff: ${diff.toFixed(2)} pp<br/>95% CI: [${low.toFixed(2)}, ${high.toFixed(2)}]`);
      });
    }
  }

  window.ChartDumbbellForest = ChartDumbbellForest;
})(window);
