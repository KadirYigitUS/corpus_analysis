/**
 * tab_10_viz.js - Tab 10 TF-IDF heatmap (Şekil 6) and Chapter 12 live Markdown report preview.
 */
(function(window) {
  'use strict';

  function initTab10Viz() {
    const subtabs = new window.SubtabController('t10-subtabs');

    // Pill 2: Şekil 6 TF-IDF Keyness Heatmap
    subtabs.onFirstShow('t10-pane-heatmap', async () => {
      const container = document.getElementById('t10-heatmap-chart-container');
      if (container && !container.dataset.loaded) {
        const topK = parseInt(document.getElementById('t10-input-topk')?.value || '5');
        const excludePropn = document.getElementById('t10-check-exclude-propn')?.checked ?? true;

        const res = await window.VizAPI.postJSON('/api/v1/lexicon/tfidf/dense', {
          tfidf_params: { top_k: topK, exclude_propn: excludePropn },
          view_params: { field: 'lem', filter_function_words: true }
        });

        const matrix = {
          title: 'Şekil 6: TF-IDF Ayırt Edici Sözvarlığı (Keyness Heatmap)',
          rows: res.documents || [],
          cols: res.terms || [],
          values: res.matrix || [],
          fmt: '.2f',
          scale: 'seq'
        };

        const card = window.ChartHost.createChartCard(matrix.title, 't10-heatmap-canvas', 320);
        container.appendChild(card.card);

        const chart = new window.ChartHeatmap(card.canvas, { marginLeft: 120, marginBottom: 35 });
        chart.renderHeatmap(matrix);
        container.dataset.loaded = 'true';
      }
    });

    // Pill 3: Canlı Araştırma Raporu Önizleme (Bölüm 12)
    subtabs.onFirstShow('t10-pane-report-preview', async () => {
      const mdDiv = document.getElementById('t10-report-markdown-preview');
      const tableDiv = document.getElementById('t10-report-summary-table');
      if (mdDiv && !mdDiv.dataset.loaded) {
        const data = await window.VizAPI.getJSON('/api/v1/lexicon/report/preview');
        mdDiv.innerHTML = `<pre style="font-family:var(--font-mono);font-size:11.5px;background:#0f172a;color:#e2e8f0;padding:12px;border-radius:4px;white-space:pre-wrap;">${data.markdown}</pre>`;
        if (tableDiv && data.summary_table) {
          window.DataTableRenderer.render(tableDiv, data.summary_table, 10);
        }
        mdDiv.dataset.loaded = 'true';
      }
    });
  }

  window.initTab10Viz = initTab10Viz;
})(window);
