/**
 * tab_06_viz.js - Tab 6 sub-tabs: Sıklık Çubukları & Arama Özeti, Görünüm Karşılaştırması, NLTK.
 */
(function(window) {
  'use strict';

  function initTab06Viz() {
    const subtabs = new window.SubtabController('t6-subtabs');

    // Pill 2: Sıklık Çubukları & Arama Özeti
    subtabs.onFirstShow('t6-pane-summary', async () => {
      const term = document.getElementById('t6-input-query')?.value || 'robot';
      const match = document.getElementById('t6-select-match')?.value || 'exact';
      const container = document.getElementById('t6-summary-chart-container');
      const tableDiv = document.getElementById('t6-summary-table-container');

      if (container && !container.dataset.loaded) {
        const res = await window.VizAPI.postJSON('/api/v1/concordance/summary', { term, match });

        const card = window.ChartHost.createChartCard(`'${term}' 10 Bin Sözcük Başına Sıklık (Per10k)`, 't6-summary-bars-canvas', 240);
        container.appendChild(card.card);

        const chart = new window.ChartBars(card.canvas, { marginBottom: 35 });
        chart.renderVerticalBars(res.bars || [], 'code', 'per10k', 'color_key');
        container.dataset.loaded = 'true';

        if (tableDiv && res.table) {
          window.DataTableRenderer.render(tableDiv, res.table, 15);
          tableDiv.dataset.loaded = 'true';
        }
      }
    });

    // Pill 3: Görünüm Karşılaştırması
    subtabs.onFirstShow('t6-pane-views', async () => {
      const term = document.getElementById('t6-input-query')?.value || 'robot';
      const match = document.getElementById('t6-select-match')?.value || 'exact';
      const container = document.getElementById('t6-views-table-container');
      if (container && !container.dataset.loaded) {
        const payload = await window.VizAPI.postJSON('/api/v1/concordance/views-compare', { term, match });
        window.DataTableRenderer.render(container, payload, 10);
        container.dataset.loaded = 'true';
      }
    });

    // Pill 4: NLTK Çapraz Kontrol
    subtabs.onFirstShow('t6-pane-nltk', async () => {
      const btn = document.getElementById('t6-btn-run-nltk');
      const runNltk = async () => {
        const code = document.getElementById('t6-select-nltk-text')?.value || 'IR-IA';
        const word = document.getElementById('t6-input-nltk-word')?.value || 'robot';
        const linesDiv = document.getElementById('t6-nltk-lines-container');
        const simDiv = document.getElementById('t6-nltk-similar-container');

        if (linesDiv) linesDiv.innerHTML = 'Running NLTK concordance...';
        const data = await window.VizAPI.postJSON('/api/v1/concordance/nltk', { code, word });

        if (linesDiv) {
          linesDiv.innerHTML = `<pre style="font-family:var(--font-mono);font-size:11px;background:#0f172a;color:#38bdf8;padding:10px;border-radius:4px;overflow-x:auto;">${(data.concordance || []).join('\n') || 'No matches found.'}</pre>`;
          linesDiv.dataset.loaded = 'true';
        }
        if (simDiv) {
          simDiv.innerHTML = `<b>NLTK Dağılımsal Benzer Sözcükler:</b> ${(data.similar || []).join(', ') || 'Yok'}`;
        }
      };
      if (btn) btn.onclick = runNltk;
      const linesDiv = document.getElementById('t6-nltk-lines-container');
      if (linesDiv && !linesDiv.dataset.loaded) await runNltk();
    });
  }

  window.initTab06Viz = initTab06Viz;
})(window);
