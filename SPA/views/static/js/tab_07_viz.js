/**
 * tab_07_viz.js - Tab 7 subtabs for Batch Dispersion: Sayımlar, Isı Haritası (Şekil 3A), Bağıntı (Şekil 3B), Dağılım (Şekil 3C).
 */
(function(window) {
  'use strict';

  function initTab07Viz() {
    const subtabs = new window.SubtabController('t7-subtabs');

    async function loadBatchData() {
      const rawInput = document.getElementById('t7-input-terms')?.value || 'robot, insan, dünya, uzay';
      const isContent = document.getElementById('t7-check-content')?.checked || false;
      return await window.VizAPI.postJSON('/api/v1/concordance/batch-matrices', { raw_input: rawInput, content_only: isContent });
    }

    // Pill 1: Sayımlar & Oranlar Tabloları
    subtabs.onFirstShow('t7-pane-tables', async () => {
      const countsDiv = document.getElementById('t7-counts-table');
      const ratesDiv = document.getElementById('t7-rates-table');
      if (countsDiv && !countsDiv.dataset.loaded) {
        const data = await loadBatchData();
        window.DataTableRenderer.render(countsDiv, data.counts, 10);
        window.DataTableRenderer.render(ratesDiv, data.rates, 10);
        countsDiv.dataset.loaded = 'true';
      }
    });

    // Pill 2: Şekil 3A Per10k Isı Haritası
    subtabs.onFirstShow('t7-pane-rates-heatmap', async () => {
      const container = document.getElementById('t7-rates-heatmap-container');
      if (container && !container.dataset.loaded) {
        const data = await loadBatchData();
        const card = window.ChartHost.createChartCard('Şekil 3A: 10 000 Akan Sözcük Başına Sıklık (Per10k)', 't7-rates-canvas', 280);
        container.appendChild(card.card);

        const chart = new window.ChartHeatmap(card.canvas, { marginLeft: 110, marginBottom: 35 });
        chart.renderHeatmap(data.rates_matrix);
        container.dataset.loaded = 'true';
      }
    });

    // Pill 3: Şekil 3B Bağıntı Matrisi Isı Haritası
    subtabs.onFirstShow('t7-pane-corr-matrix', async () => {
      const container = document.getElementById('t7-corr-heatmap-container');
      if (container && !container.dataset.loaded) {
        const data = await loadBatchData();
        const card = window.ChartHost.createChartCard('Şekil 3B: Sözcük Profilleri Arasında Pearson r Bağıntısı', 't7-corr-canvas', 280);
        container.appendChild(card.card);

        const chart = new window.ChartHeatmap(card.canvas, { marginLeft: 110, marginBottom: 35 });
        chart.renderHeatmap(data.corr_matrix);
        container.dataset.loaded = 'true';
      }
    });

    // Pill 4: Şekil 3C 10-Dilim Dağılım Çizgileri
    subtabs.onFirstShow('t7-pane-dispersion-curves', async () => {
      const container = document.getElementById('t7-chunk-curves-container');
      if (container && !container.dataset.loaded) {
        const data = await loadBatchData();
        const card = window.ChartHost.createChartCard(`Şekil 3C: Anlatı Boyunca Dağılım Eğrisi (${data.label_name || 'Terim'})`, 't7-chunk-canvas', 260);
        container.appendChild(card.card);

        const chart = new window.ChartLines(card.canvas, { marginLeft: 50, marginBottom: 35 });
        chart.renderLines(data.chunk_series);
        container.dataset.loaded = 'true';
      }
    });
  }

  window.initTab07Viz = initTab07Viz;
})(window);
