/**
 * chart_core.js - HiDPI canvas initialization, Theme observer, tooltips, and base layout.
 */
(function(window) {
  'use strict';

  class ChartCore {
    constructor(canvas, options = {}) {
      this.canvas = typeof canvas === 'string' ? document.getElementById(canvas) : canvas;
      this.ctx = this.canvas.getContext('2d');
      this.options = Object.assign({
        marginTop: 25,
        marginRight: 25,
        marginBottom: 45,
        marginLeft: 55,
        title: ''
      }, options);
      this.dpr = window.devicePixelRatio || 1;
      this.hitBoxes = [];
      this.tooltipEl = null;
      this.initThemeObserver();
      this.initTooltip();
      this.setupCanvas();
    }

    setupCanvas() {
      const rect = this.canvas.getBoundingClientRect();
      const w = rect.width || this.canvas.width || 600;
      const h = rect.height || this.canvas.height || 260;
      this.canvas.width = Math.round(w * this.dpr);
      this.canvas.height = Math.round(h * this.dpr);
      this.width = w;
      this.height = h;
      this.ctx.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
    }

    getThemeColors() {
      const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
      return {
        isDark,
        text: isDark ? '#e2e8f0' : '#1e293b',
        textMuted: isDark ? '#94a3b8' : '#64748b',
        border: isDark ? '#334155' : '#e2e8f0',
        grid: isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)',
        bg: isDark ? '#0f172a' : '#ffffff'
      };
    }

    clear() {
      this.setupCanvas();
      const theme = this.getThemeColors();
      this.ctx.fillStyle = theme.bg;
      this.ctx.fillRect(0, 0, this.width, this.height);
      this.hitBoxes = [];
    }

    plotArea() {
      return {
        x: this.options.marginLeft,
        y: this.options.marginTop,
        w: Math.max(10, this.width - this.options.marginLeft - this.options.marginRight),
        h: Math.max(10, this.height - this.options.marginTop - this.options.marginBottom)
      };
    }

    initTooltip() {
      const container = this.canvas.parentElement;
      if (!container) return;
      this.tooltipEl = container.querySelector('.chart-tooltip');
      if (!this.tooltipEl) {
        this.tooltipEl = document.createElement('div');
        this.tooltipEl.className = 'chart-tooltip';
        container.style.position = 'relative';
        container.appendChild(this.tooltipEl);
      }
      this.canvas.onmousemove = (e) => this.handleMouseMove(e);
      this.canvas.onmouseleave = () => this.hideTooltip();
    }

    handleMouseMove(e) {
      const rect = this.canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const hit = this.hitBoxes.find(b => x >= b.x && x <= b.x + b.w && y >= b.y && y <= b.y + b.h);
      if (hit && hit.text) {
        this.tooltipEl.innerHTML = hit.text;
        this.tooltipEl.style.display = 'block';
        this.tooltipEl.style.left = `${Math.min(rect.width - 150, Math.max(10, x + 10))}px`;
        this.tooltipEl.style.top = `${Math.min(rect.height - 40, Math.max(10, y - 28))}px`;
      } else {
        this.hideTooltip();
      }
    }

    hideTooltip() {
      if (this.tooltipEl) this.tooltipEl.style.display = 'none';
    }

    addHitBox(x, y, w, h, text) {
      this.hitBoxes.push({ x, y, w, h, text });
    }

    initThemeObserver() {
      ChartCore._instances.add(this);
      if (!ChartCore._themeObserver) {
        ChartCore._themeObserver = new MutationObserver(() => {
          ChartCore._instances.forEach((inst) => {
            if (!inst.canvas || !inst.canvas.isConnected) {
              ChartCore._instances.delete(inst);
              return;
            }
            if (typeof inst.onRedraw === 'function') inst.onRedraw();
          });
        });
        ChartCore._themeObserver.observe(document.documentElement, {
          attributes: true,
          attributeFilter: ['data-theme']
        });
      }
    }
  }

  ChartCore._instances = new Set();
  ChartCore._themeObserver = null;

  window.ChartCore = ChartCore;
})(window);
