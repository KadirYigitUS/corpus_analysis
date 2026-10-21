/**
 * chart_bars.js - Vertical, horizontal, and stacked bar chart renderer.
 */
(function(window) {
  'use strict';

  class ChartBars extends window.ChartCore {
    renderVerticalBars(items, xKey, yKey, colorKey = 'color_key') {
      this.clear();
      const theme = this.getThemeColors();
      const p = this.plotArea();
      const maxVal = Math.max(1, ...items.map(d => Number(d[yKey]) || 0));
      const ticks = window.ChartScales.calculateTicks(0, maxVal, 5);
      const topTick = ticks[ticks.length - 1];

      // Y-axis grid and ticks
      this.ctx.font = '10px sans-serif';
      this.ctx.fillStyle = theme.textMuted;
      this.ctx.textAlign = 'right';
      ticks.forEach(t => {
        const y = p.y + p.h - (t / topTick) * p.h;
        this.ctx.strokeStyle = theme.grid;
        this.ctx.beginPath();
        this.ctx.moveTo(p.x, y);
        this.ctx.lineTo(p.x + p.w, y);
        this.ctx.stroke();
        this.ctx.fillText(t.toLocaleString(), p.x - 8, y + 3);
      });

      // Bars
      const n = items.length;
      const barWidth = Math.max(8, (p.w / n) * 0.72);
      const gap = p.w / n;

      items.forEach((item, i) => {
        const val = Number(item[yKey]) || 0;
        const barH = (val / topTick) * p.h;
        const x = p.x + i * gap + (gap - barWidth) / 2;
        const y = p.y + p.h - barH;
        const color = item.color || window.ChartScales.getAuthorColor(item[colorKey]);

        this.ctx.fillStyle = color;
        this.ctx.fillRect(x, y, barWidth, barH);
        this.ctx.strokeStyle = theme.border;
        this.ctx.strokeRect(x, y, barWidth, barH);

        // Tooltip hit-box
        this.addHitBox(x, y, barWidth, barH, `<b>${item.code || item[xKey]}</b>: ${val.toLocaleString()}`);

        // Rotated X label
        this.ctx.save();
        this.ctx.translate(x + barWidth / 2, p.y + p.h + 10);
        this.ctx.rotate(Math.PI / 4);
        this.ctx.fillStyle = theme.text;
        this.ctx.textAlign = 'left';
        this.ctx.fillText(item[xKey] || '', 0, 0);
        this.ctx.restore();
      });
    }

    renderStackedHorizontal(pairs, types, pctMap, colorsMap) {
      this.clear();
      const theme = this.getThemeColors();
      const p = this.plotArea();
      const n = pairs.length;
      const rowHeight = Math.max(16, p.h / n * 0.65);
      const rowGap = p.h / n;

      pairs.forEach((pair, i) => {
        const y = p.y + i * rowGap + (rowGap - rowHeight) / 2;
        let leftX = p.x;

        // Label on left
        this.ctx.font = '11px sans-serif';
        this.ctx.fillStyle = theme.text;
        this.ctx.textAlign = 'right';
        this.ctx.fillText(pair, p.x - 10, y + rowHeight / 2 + 4);

        types.forEach(ty => {
          const pct = (pctMap[ty] && pctMap[ty][i]) ? Number(pctMap[ty][i]) : 0;
          const w = (pct / 100) * p.w;
          const col = colorsMap[ty] || '#94a3b8';

          this.ctx.fillStyle = col;
          this.ctx.fillRect(leftX, y, w, rowHeight);
          this.ctx.strokeStyle = '#ffffff';
          this.ctx.strokeRect(leftX, y, w, rowHeight);

          if (pct > 4) {
            this.ctx.fillStyle = '#ffffff';
            this.ctx.textAlign = 'center';
            this.ctx.font = 'bold 9px sans-serif';
            this.ctx.fillText(`${Math.round(pct)}%`, leftX + w / 2, y + rowHeight / 2 + 3);
          }

          this.addHitBox(leftX, y, w, rowHeight, `<b>${pair}</b><br/>${ty}: ${pct.toFixed(1)}%`);
          leftX += w;
        });
      });
    }
  }

  window.ChartBars = ChartBars;
})(window);
