/**
 * tab_08_viz.js - Tab 8 Lexical Diversity visualizations: Duyarlılık, Karşılaştırma, Radar (4A), MATTR (4B), Zipf (4C).
 */
(function(window) {
  'use strict';

  function initTab08Viz() {
    const subtabs = new window.SubtabController('t8-subtabs');

    // Pill 2: Metin Boyu Duyarlılığı
    subtabs.onFirstShow('t8-pane-sensitivity', async () => {
      const chartDiv = document.getElementById('t8-sens-chart-container');
      const tableDiv = document.getElementById('t8-sens-table-container');
      if (chartDiv && !chartDiv.dataset.loaded) {
        const selCode = document.getElementById('t8-select-text')?.value || 'IR-IA';
        const data = await window.VizAPI.postJSON('/api/v1/lexicon/diversity/sensitivity', { code: selCode });
        const card = window.ChartHost.createChartCard(`Bölüm 9.3: TTR Metin Boyuyla Çöker, MATTR Dirençlidir (${selCode})`, 't8-sens-canvas', 260);
        chartDiv.appendChild(card.card);

        const chart = new window.ChartLines(card.canvas, { marginLeft: 50, marginBottom: 35 });
        chart.renderLines(data.series);
        chartDiv.dataset.loaded = 'true';

        if (tableDiv) {
          window.DataTableRenderer.render(tableDiv, data.table, 10);
          tableDiv.dataset.loaded = 'true';
        }
      }
    });

    // Pill 3: Token ↔ Lemma & Noktalama
    subtabs.onFirstShow('t8-pane-comparisons', async () => {
      const tokDiv = document.getElementById('t8-tok-lem-table');
      const punctDiv = document.getElementById('t8-punct-table');
      if (tokDiv && !tokDiv.dataset.loaded) {
        const data = await window.VizAPI.getJSON('/api/v1/lexicon/diversity/compare');
        window.DataTableRenderer.render(tokDiv, data.token_vs_lemma, 10);
        window.DataTableRenderer.render(punctDiv, data.punct_regimes, 10);
        tokDiv.dataset.loaded = 'true';
      }
    });

    // Pill 4: Şekil 4A Radar Grafiği
    subtabs.onFirstShow('t8-pane-radar', async () => {
      const container = document.getElementById('t8-radar-chart-container');
      if (container && !container.dataset.loaded) {
        const data = await window.VizAPI.postJSON('/api/v1/lexicon/diversity/radar', {});
        const card = window.ChartHost.createChartCard('Şekil 4A: Sözcüksel Çeşitlilik Profili (Z-Skorları Radar Grafiği)', 't8-radar-canvas', 320);
        container.appendChild(card.card);

        const chart = new window.ChartRadar(card.canvas);
        chart.renderRadar(data.axes, data.series);
        container.dataset.loaded = 'true';
      }
    });

    // Pill 5: Şekil 4B MATTR Yörüngeleri
    subtabs.onFirstShow('t8-pane-mattr', async () => {
      const container = document.getElementById('t8-mattr-curves-container');
      if (container && !container.dataset.loaded) {
        const data = await window.VizAPI.postJSON('/api/v1/lexicon/diversity/mattr-trajectories', { window: 500 });
        const card = window.ChartHost.createChartCard('Şekil 4B: Kayan Pencere MATTR Yörüngesi (w=500)', 't8-mattr-canvas', 260);
        container.appendChild(card.card);

        const chart = new window.ChartLines(card.canvas, { marginLeft: 50, marginBottom: 35 });
        chart.renderLines(data.series);
        container.dataset.loaded = 'true';
      }
    });

    // Pill 6: Şekil 4C Zipf Eğrileri
    subtabs.onFirstShow('t8-pane-zipf', async () => {
      const container = document.getElementById('t8-zipf-curves-container');
      if (container && !container.dataset.loaded) {
        const data = await window.VizAPI.postJSON('/api/v1/lexicon/diversity/zipf-curves', {});
        const card = window.ChartHost.createChartCard('Şekil 4C: Zipf Sıra-Sıklık Eğrisi (Log-Log Ekseni)', 't8-zipf-canvas', 280);
        container.appendChild(card.card);

        const chart = new window.ChartLines(card.canvas, { marginLeft: 50, marginBottom: 35 });
        chart.renderLines(data.series, true);
        container.dataset.loaded = 'true';
      }
    });
  }

  window.initTab08Viz = initTab08Viz;
})(window);
