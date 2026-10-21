/**
 * chart_radar.js - 6-axis polar radar chart renderer for z-scored diversity metrics.
 */
(function(window) {
  'use strict';

  class ChartRadar extends window.ChartCore {
    renderRadar(axes, seriesList) {
      this.clear();
      const theme = this.getThemeColors();
      const cx = this.width / 2;
      const cy = this.height / 2;
      const radius = Math.min(cx, cy) - 35;
      const numAxes = axes.length;
      const angleStep = (Math.PI * 2) / numAxes;

      // Draw polar concentric web
      for (let level = 1; level <= 4; level++) {
        const r = (radius / 4) * level;
        this.ctx.strokeStyle = theme.grid;
        this.ctx.lineWidth = 1;
        this.ctx.beginPath();
        for (let a = 0; a < numAxes; a++) {
          const angle = a * angleStep - Math.PI / 2;
          const x = cx + r * Math.cos(angle);
          const y = cy + r * Math.sin(angle);
          if (a === 0) this.ctx.moveTo(x, y);
          else this.ctx.lineTo(x, y);
        }
        this.ctx.closePath();
        this.ctx.stroke();
      }

      // Draw axis spokes and labels
      axes.forEach((axisName, a) => {
        const angle = a * angleStep - Math.PI / 2;
        const x = cx + radius * Math.cos(angle);
        const y = cy + radius * Math.sin(angle);
        this.ctx.strokeStyle = theme.border;
        this.ctx.beginPath();
        this.ctx.moveTo(cx, cy);
        this.ctx.lineTo(x, y);
        this.ctx.stroke();

        this.ctx.font = '10px sans-serif';
        this.ctx.fillStyle = theme.text;
        this.ctx.textAlign = 'center';
        const lx = cx + (radius + 15) * Math.cos(angle);
        const ly = cy + (radius + 15) * Math.sin(angle);
        this.ctx.fillText(axisName, lx, ly);
      });

      // Draw series polygons
      seriesList.forEach((s, idx) => {
        const color = window.ChartScales.CATEGORICAL_10[idx % 10];
        this.ctx.strokeStyle = color;
        this.ctx.fillStyle = color.replace(')', ', 0.15)').replace('rgb', 'rgba');
        this.ctx.lineWidth = 2;
        this.ctx.beginPath();

        s.z.forEach((zVal, a) => {
          const clampedZ = Math.max(-2.5, Math.min(2.5, zVal));
          const r = radius * ((clampedZ + 2.5) / 5.0);
          const angle = a * angleStep - Math.PI / 2;
          const x = cx + r * Math.cos(angle);
          const y = cy + r * Math.sin(angle);
          if (a === 0) this.ctx.moveTo(x, y);
          else this.ctx.lineTo(x, y);
        });

        this.ctx.closePath();
        this.ctx.stroke();
        this.ctx.fill();
      });
    }
  }

  window.ChartRadar = ChartRadar;
})(window);
