/**
 * tab_04_viz.js - Tab 4 sub-tab visualizations: Şekil 2A Heatmap, Şekil 2B Dumbbell, and Şekil 2C Forest plot.
 */
(function(window) {
  'use strict';

  function initTab04Viz() {
    const subtabs = new window.SubtabController('t4-subtabs');

    // Pill 1: Şekil 2A UPOS Heatmap
    subtabs.onFirstShow('t4-pane-heatmap', async () => {
      const container = document.getElementById('t4-heatmap-chart-container');
      if (!container || container.dataset.loaded) return;

      const card = window.ChartHost.createChartCard('Şekil 2A: 13 Metnin UPOS Profil Isı Haritası (%)', 't4-heatmap-canvas', 340);
      container.appendChild(card.card);

      const isContentOnly = document.getElementById('t4-check-content-only')?.checked || false;
      const payload = await window.VizAPI.getJSON(`/api/v1/syntax/pos/matrix?content_only=${isContentOnly}`);
      const chart = new window.ChartHeatmap(card.canvas, { marginLeft: 140, marginBottom: 35 });
      chart.renderHeatmap(payload);
      container.dataset.loaded = 'true';
    });

    // Pill 2: Şekil 2B Çift Ayrışımı Dumbbell Plot
    subtabs.onFirstShow('t4-pane-dumbbell', async () => {
      const container = document.getElementById('t4-dumbbell-chart-container');
      if (!container || container.dataset.loaded) return;

      const card = window.ChartHost.createChartCard('Şekil 2B: Çeviri Çifti UPOS Ayrışımı (Dumbbell: EN vs TR)', 't4-dumbbell-canvas', 300);
      container.appendChild(card.card);

      const pairCode = document.getElementById('t4-select-pair-2b')?.value || 'IR-IA_BR-SM';
      const isContentOnly = document.getElementById('t4-check-content-only')?.checked || false;
      const data = await window.VizAPI.getJSON(`/api/v1/syntax/pos/pair-delta/${pairCode}?content_only=${isContentOnly}`);
      const chart = new window.ChartDumbbellForest(card.canvas, { marginLeft: 65 });
      chart.renderDumbbell(data.items || [], 'eng_pct', 'tur_pct', 'upos');
      container.dataset.loaded = 'true';
    });

    // Pill 3: Şekil 2C Forest Plot with Bootstrap 95% CIs
    subtabs.onFirstShow('t4-pane-forest', async () => {
      const container = document.getElementById('t4-forest-chart-container');
      if (!container || container.dataset.loaded) return;

      const card = window.ChartHost.createChartCard('Şekil 2C: Çeviri vs Yerli Türkçe UPOS Farkı (Bootstrap %95 GA Forest Plot)', 't4-forest-canvas', 300);
      container.appendChild(card.card);

      const compKey = document.getElementById('t4-select-comp-2c')?.value || 'ALL';
      const isContentOnly = document.getElementById('t4-check-content-only')?.checked || false;
      const data = await window.VizAPI.postJSON('/api/v1/syntax/pos/group-comparison', {
        group_a: 'trans_tr',
        group_b: 'indig_tr',
        comparison_key: compKey,
        content_only: isContentOnly,
        n_bootstrap: 800
      });

      const chart = new window.ChartDumbbellForest(card.canvas, { marginLeft: 65 });
      chart.renderForest(data.items || [], 'mean_diff_pp', 'ci_low', 'ci_high', 'upos');
      container.dataset.loaded = 'true';
    });
  }

  window.initTab04Viz = initTab04Viz;
})(window);
