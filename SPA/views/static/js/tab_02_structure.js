/**
 * tab_02_structure.js - Tab 2 subtabs for Structure Summary (Şekil 1A) and Scatter (Şekil 1B).
 */
(function(window) {
  'use strict';

  function initTab02Structure() {
    const subtabs = new window.SubtabController('t2-subtabs');

    subtabs.onFirstShow('t2-pane-structure', async () => {
      // 1. Render Structure Summary and Stacked Bars (Şekil 1A)
      const stackedContainer = document.getElementById('t2-stacked-chart-container');
      const tableContainer = document.getElementById('t2-structure-summary-grid');

      if (stackedContainer && !stackedContainer.dataset.loaded) {
        const payload = await window.VizAPI.getJSON('/api/v1/alignment/structure-summary');

        // Card & Chart
        const card = window.ChartHost.createChartCard('Şekil 1A: Çeviri Çiftlerinde Hizalama Yapısı Dağılımı', 't2-stacked-canvas', 220);
        stackedContainer.appendChild(card.card);

        const chart = new window.ChartBars(card.canvas, { marginLeft: 80 });
        chart.renderStackedHorizontal(payload.stacked.pairs, payload.stacked.types, payload.stacked.pct, payload.stacked.colors);
        stackedContainer.dataset.loaded = 'true';

        // Summary Table
        if (tableContainer && payload.table) {
          window.DataTableRenderer.render(tableContainer, payload.table, 10);
        }
      }

      // 2. Render 1:1 Length Relation Scatter (Şekil 1B)
      const scatterContainer = document.getElementById('t2-scatter-chart-container');
      if (scatterContainer && !scatterContainer.dataset.loaded) {
        const scatterCard = window.ChartHost.createChartCard('Şekil 1B: 1:1 Hizalamalarda Sözcük Sayısı İlişkisi (OLS Regresyon Eğimi)', 't2-scatter-canvas', 300);
        scatterContainer.appendChild(scatterCard.card);

        const scatterPayload = await window.VizAPI.postJSON('/api/v1/alignment/structure-scatter', { max_points: 1500 });
        const scatterChart = new window.ChartScatter(scatterCard.canvas, { marginLeft: 50, marginBottom: 40 });
        scatterChart.renderScatter(scatterPayload.series, 'English Words', 'Turkish Words', true);
        scatterContainer.dataset.loaded = 'true';
      }
    });
  }

  window.initTab02Structure = initTab02Structure;
})(window);
