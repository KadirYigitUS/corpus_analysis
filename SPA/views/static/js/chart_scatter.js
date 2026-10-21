/**
 * chart_scatter.js - 2D scatter plots, OLS regression slope lines, and GraphColl bubble plots.
 */
(function(window) {
  'use strict';

  class ChartScatter extends window.ChartCore {
    renderScatter(seriesList, xLabel = 'X', yLabel = 'Y', showSlope = false) {
      this.clear();
      const theme = this.getThemeColors();
      const p = this.plotArea();

      let maxX = 1, maxY = 1;
      seriesList.forEach(s => {
        s.points.forEach(pt => {
          if (pt.x > maxX) maxX = pt.x;
          if (pt.y > maxY) maxY = pt.y;
        });
      });

      const mapX = (x) => p.x + (x / maxX) * p.w;
      const mapY = (y) => p.y + p.h - (y / maxY) * p.h;

      seriesList.forEach((s, idx) => {
        const color = s.color || window.ChartScales.CATEGORICAL_10[idx % 10];
        this.ctx.fillStyle = color;

        s.points.forEach(pt => {
          const px = mapX(pt.x);
          const py = mapY(pt.y);
          const r = pt.r || 3;
          this.ctx.beginPath();
          this.ctx.arc(px, py, r, 0, Math.PI * 2);
          this.ctx.fill();

          if (pt.label) {
            this.ctx.font = '9px sans-serif';
            this.ctx.fillStyle = theme.text;
            this.ctx.fillText(pt.label, px + 5, py + 2);
          }

          this.addHitBox(px - r - 2, py - r - 2, (r + 2) * 2, (r + 2) * 2,
            `<b>${pt.label || s.name}</b><br/>X: ${pt.x.toFixed(1)} | Y: ${pt.y.toFixed(1)}`);
        });

        // OLS Regression line if slope present
        if (showSlope && s.slope !== undefined) {
          const slope = s.slope;
          const endX = maxX;
          const endY = slope * endX;
          this.ctx.strokeStyle = color;
          this.ctx.lineWidth = 2;
          this.ctx.beginPath();
          this.ctx.moveTo(mapX(0), mapY(0));
          this.ctx.lineTo(mapX(endX), mapY(endY));
          this.ctx.stroke();
        }
      });
    }
  }

  window.ChartScatter = ChartScatter;
})(window);
