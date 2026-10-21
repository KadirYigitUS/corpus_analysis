/**
 * tab_09_viz.js - Tab 9 Collocation visualizations: GraphColl 2D Scatter, Ölçüt Duyarlılığı, NLTK.
 */
(function(window) {
  'use strict';

  function initTab09Viz() {
    const subtabs = new window.SubtabController('t9-subtabs');

    // Pill 2: Şekil 5 GraphColl 2D Scatter (MI vs log10 G2)
    subtabs.onFirstShow('t9-pane-scatter', async () => {
      const container = document.getElementById('t9-scatter-chart-container');
      if (container && !container.dataset.loaded) {
        const node = document.getElementById('t9-input-node')?.value || 'robot';
        const code = document.getElementById('t9-select-text')?.value || 'BR-SM';
        const data = await window.VizAPI.postJSON('/api/v1/lexicon/collocation/scatter', { code, node });

        const card = window.ChartHost.createChartCard(`Şekil 5: GraphColl Dağılım Grafiği ('${node}' — Güç vs Kanıt)`, 't9-scatter-canvas', 300);
        container.appendChild(card.card);

        const chart = new window.ChartScatter(card.canvas, { marginLeft: 55, marginBottom: 40 });
        chart.renderScatter(data.series, 'MI (Çekim Gücü: Etki Büyüklüğü)', 'log10 G2 (Kanıt: Güvenilirlik)');
        container.dataset.loaded = 'true';
      }
    });

    // Pill 3: Ölçüt & Pencere Duyarlılığı
    subtabs.onFirstShow('t9-pane-sensitivity', async () => {
      const measDiv = document.getElementById('t9-measures-table');
      const winDiv = document.getElementById('t9-window-table');
      if (measDiv && !measDiv.dataset.loaded) {
        const node = document.getElementById('t9-input-node')?.value || 'robot';
        const code = document.getElementById('t9-select-text')?.value || 'BR-SM';
        const data = await window.VizAPI.postJSON('/api/v1/lexicon/collocation/sensitivity', { code, node });

        window.DataTableRenderer.render(measDiv, data.measures_table, 10);
        window.DataTableRenderer.render(winDiv, data.window_table, 10);
        measDiv.dataset.loaded = 'true';
      }
    });

    // Pill 4: NLTK Bigram Doğrulama
    subtabs.onFirstShow('t9-pane-nltk', async () => {
      const collDiv = document.getElementById('t9-nltk-collocs-table');
      const ngramDiv = document.getElementById('t9-nltk-ngrams-table');
      if (collDiv && !collDiv.dataset.loaded) {
        const code = document.getElementById('t9-select-text')?.value || 'BR-SM';
        const data = await window.VizAPI.postJSON('/api/v1/lexicon/collocation/nltk', { code });

        window.DataTableRenderer.render(collDiv, data.collocations, 10);
        window.DataTableRenderer.render(ngramDiv, data.ngrams, 10);
        collDiv.dataset.loaded = 'true';
      }
    });
  }

  window.initTab09Viz = initTab09Viz;
})(window);
