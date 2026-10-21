/**
 * chart_barcode.js - 10-chunk narrative dispersion line curves and lexical barcode ticks.
 */
(function(window) {
  'use strict';

  class ChartBarcode extends window.ChartCore {
    renderDispersionBarcode(barcodeMap) {
      this.clear();
      const theme = this.getThemeColors();
      const p = this.plotArea();
      const labels = Object.keys(barcodeMap);
      const rowGap = p.h / Math.max(1, labels.length);

      labels.forEach((label, i) => {
        const y = p.y + i * rowGap + rowGap / 2;
        const positions = barcodeMap[label] || [];
        const color = window.ChartScales.CATEGORICAL_10[i % 10];

        // Label
        this.ctx.font = '10px sans-serif';
        this.ctx.fillStyle = theme.text;
        this.ctx.textAlign = 'right';
        this.ctx.fillText(label, p.x - 8, y + 3);

        // Baseline
        this.ctx.strokeStyle = theme.border;
        this.ctx.lineWidth = 1;
        this.ctx.beginPath();
        this.ctx.moveTo(p.x, y);
        this.ctx.lineTo(p.x + p.w, y);
        this.ctx.stroke();

        // Vertical tick lines
        this.ctx.strokeStyle = color;
        this.ctx.lineWidth = 1.2;
        positions.forEach(relPos => {
          const x = p.x + Math.max(0, Math.min(1, relPos)) * p.w;
          this.ctx.beginPath();
          this.ctx.moveTo(x, y - 8);
          this.ctx.lineTo(x, y + 8);
          this.ctx.stroke();
        });

        this.addHitBox(p.x, y - 10, p.w, 20, `<b>${label}</b>: ${positions.length} occurrences`);
      });
    }
  }

  window.ChartBarcode = ChartBarcode;
})(window);
