/**
 * chart_lines.js - Multi-line trajectory plots, MATTR moving averages, and Zipf log-log curves.
 */
(function(window) {
  'use strict';

  class ChartLines extends window.ChartCore {
    renderLines(seriesList, isLogLog = false) {
      this.clear();
      const theme = this.getThemeColors();
      const p = this.plotArea();

      // Find global min and max
      let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
      seriesList.forEach(s => {
        s.x.forEach(v => { if (v < minX) minX = v; if (v > maxX) maxX = v; });
        s.y.forEach(v => { if (v < minY) minY = v; if (v > maxY) maxY = v; });
      });

      if (isLogLog) {
        minX = Math.max(1, minX);
        minY = Math.max(0.1, minY);
      } else {
        minY = Math.min(0, minY);
      }

      const mapX = (val) => {
        if (isLogLog) {
          const lmin = Math.log10(minX), lmax = Math.log10(maxX);
          return p.x + ((Math.log10(Math.max(1, val)) - lmin) / Math.max(1e-4, lmax - lmin)) * p.w;
        }
        return p.x + ((val - minX) / Math.max(1e-4, maxX - minX)) * p.w;
      };

      const mapY = (val) => {
        if (isLogLog) {
          const lmin = Math.log10(minY), lmax = Math.log10(maxY);
          return p.y + p.h - ((Math.log10(Math.max(0.1, val)) - lmin) / Math.max(1e-4, lmax - lmin)) * p.h;
        }
        return p.y + p.h - ((val - minY) / Math.max(1e-4, maxY - minY)) * p.h;
      };

      // Draw series
      seriesList.forEach((s, idx) => {
        const color = s.color || window.ChartScales.CATEGORICAL_10[idx % 10];
        this.ctx.strokeStyle = color;
        this.ctx.lineWidth = 1.8;
        this.ctx.beginPath();
        s.x.forEach((xv, i) => {
          const px = mapX(xv);
          const py = mapY(s.y[i]);
          if (i === 0) this.ctx.moveTo(px, py);
          else this.ctx.lineTo(px, py);
          this.addHitBox(px - 4, py - 4, 8, 8, `<b>${s.name}</b><br/>X: ${xv.toFixed(1)} | Y: ${s.y[i].toFixed(2)}`);
        });
        this.ctx.stroke();
      });

      // Axis labels
      this.ctx.fillStyle = theme.textMuted;
      this.ctx.font = '10px sans-serif';
      this.ctx.textAlign = 'center';
      this.ctx.fillText(isLogLog ? 'log10 Rank' : 'Position in Text (%)', p.x + p.w / 2, p.y + p.h + 25);
    }
  }

  window.ChartLines = ChartLines;
})(window);
