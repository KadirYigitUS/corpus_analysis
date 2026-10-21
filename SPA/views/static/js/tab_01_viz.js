/**
 * tab_01_viz.js - Tab 1 sub-tab pills: Metin Boyutları (Şekil), Doğrulama, Boyut Özeti, Bellek.
 */
(function(window) {
  'use strict';

  function initTab01Viz() {
    const subtabs = new window.SubtabController('t1-subtabs');

    // Pill 2: Metin Boyutları Bar Chart (Şekil 1)
    subtabs.onFirstShow('t1-pane-sizes-chart', async () => {
      const container = document.getElementById('t1-sizes-chart-container');
      if (!container || container.dataset.loaded) return;

      const card = window.ChartHost.createChartCard('Metin Boyutları Dağılımı (Sözcük Sayısı)', 't1-sizes-canvas', 280);
      container.appendChild(card.card);

      const data = await window.VizAPI.getJSON('/api/v1/corpus/sizes-chart');
      const chart = new window.ChartBars(card.canvas);
      chart.renderVerticalBars(data.items, 'code', 'tokens', 'color_key');
      container.dataset.loaded = 'true';
    });

    // Pill 3: Doğrulama (verify_files)
    subtabs.onFirstShow('t1-pane-verify', async () => {
      const container = document.getElementById('t1-verify-grid');
      if (!container || container.dataset.loaded) return;

      const payload = await window.VizAPI.getJSON('/api/v1/corpus/verify-files');
      window.DataTableRenderer.render(container, payload, 20);
      container.dataset.loaded = 'true';
    });

    // Pill 4: Boyut Özeti (size_summary)
    subtabs.onFirstShow('t1-pane-summary', async () => {
      const container = document.getElementById('t1-summary-grid');
      if (!container || container.dataset.loaded) return;

      const payload = await window.VizAPI.getJSON('/api/v1/corpus/size-summary');
      window.DataTableRenderer.render(container, payload, 20);
      container.dataset.loaded = 'true';
    });

    // Pill 5: Bellek & İçerik Kökleri
    subtabs.onFirstShow('t1-pane-memory', async () => {
      const memGrid = document.getElementById('t1-memory-grid');
      const lemGrid = document.getElementById('t1-lemmas-grid');
      if (memGrid && !memGrid.dataset.loaded) {
        const memPayload = await window.VizAPI.getJSON('/api/v1/corpus/memory-report');
        window.DataTableRenderer.render(memGrid, memPayload, 20);
        memGrid.dataset.loaded = 'true';
      }
      if (lemGrid && !lemGrid.dataset.loaded) {
        const lemPayload = await window.VizAPI.getJSON('/api/v1/corpus/content-lemmas');
        window.DataTableRenderer.render(lemGrid, lemPayload, 20);
        lemGrid.dataset.loaded = 'true';
      }
    });
  }

  window.initTab01Viz = initTab01Viz;
})(window);
