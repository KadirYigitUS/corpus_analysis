/**
 * chart_heatmap.js - Annotated matrix heatmap renderer with sequential and diverging scales.
 */
(function(window) {
  'use strict';

  class ChartHeatmap extends window.ChartCore {
    renderHeatmap(matrixPayload) {
      this.clear();
      const theme = this.getThemeColors();
      const p = this.plotArea();
      const rows = matrixPayload.rows || [];
      const cols = matrixPayload.cols || [];
      const values = matrixPayload.values || [];
      const isDiv = matrixPayload.scale === 'div';

      let minVal = 0, maxVal = 1;
      values.flat().forEach(v => {
        if (v !== null && !isNaN(v)) {
          if (v < minVal) minVal = v;
          if (v > maxVal) maxVal = v;
        }
      });

      const cellW = p.w / Math.max(1, cols.length);
      const cellH = p.h / Math.max(1, rows.length);

      rows.forEach((rowName, r) => {
        // Row label
        this.ctx.font = '10px sans-serif';
        this.ctx.fillStyle = theme.text;
        this.ctx.textAlign = 'right';
        this.ctx.fillText(rowName, p.x - 8, p.y + r * cellH + cellH / 2 + 3);

        cols.forEach((colName, c) => {
          const val = (values[r] && values[r][c] !== undefined) ? values[r][c] : null;
          const x = p.x + c * cellW;
          const y = p.y + r * cellH;

          if (val === null || isNaN(val)) {
            this.ctx.fillStyle = theme.border;
          } else if (isDiv) {
            const norm = Math.max(-1, Math.min(1, val));
            this.ctx.fillStyle = window.ChartScales.sampleDivergingVlag(norm);
          } else {
            const norm = (val - minVal) / Math.max(1e-4, maxVal - minVal);
            this.ctx.fillStyle = window.ChartScales.sampleYlGnBu(norm);
          }

          this.ctx.fillRect(x, y, cellW, cellH);
          this.ctx.strokeStyle = '#ffffff';
          this.ctx.strokeRect(x, y, cellW, cellH);

          // Cell value text
          if (val !== null && !isNaN(val)) {
            this.ctx.fillStyle = Math.abs(val) > (maxVal * 0.6) ? '#ffffff' : '#000000';
            this.ctx.textAlign = 'center';
            this.ctx.font = '9px sans-serif';
            const displayTxt = Math.abs(val) < 1 && matrixPayload.fmt !== '.2f' ? '·' : val.toFixed(1);
            this.ctx.fillText(displayTxt, x + cellW / 2, y + cellH / 2 + 3);
          }

          this.addHitBox(x, y, cellW, cellH,
            `<b>${rowName}</b> × <b>${colName}</b><br/>Value: ${val !== null ? val.toFixed(2) : 'N/A'}`);
        });
      });
    }
  }

  window.ChartHeatmap = ChartHeatmap;
})(window);
