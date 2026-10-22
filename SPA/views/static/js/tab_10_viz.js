/**
 * tab_10_viz.js - Tab 10 TF-IDF heatmap (Şekil 6) and Chapter 12 structured HTML report preview.
 */
(function(window) {
  'use strict';

  function formatReportHtml(data) {
    const k = data.kpis || {};
    const sections = Array.isArray(data.sections) ? data.sections : [];
    let html = `
      <div style="display:flex; flex-wrap:wrap; gap:6px; margin-bottom:10px;">
        <span class="stat-badge-math">Scope: <b>${k.scope || 'all'}</b> (${k.text_count ?? '-'} texts)</span>
        <span class="stat-badge-math">MTLD Max: <b>${k.top_id || '-'} (${k.top_val ?? '-'})</b></span>
        <span class="stat-badge-math">MTLD Min: <b>${k.bot_id || '-'} (${k.bot_val ?? '-'})</b></span>
        <span class="stat-badge-math">&mu; &pm; &sigma;: <b>${k.mean_val ?? '-'} &pm; ${k.std_val ?? '-'}</b></span>
      </div>
    `;
    if (sections.length) {
      for (const sec of sections) {
        html += `
          <div class="report-section-card">
            <h4>${sec.title}</h4>
            <ul>${(sec.items || []).map(it => `<li>${it}</li>`).join('')}</ul>
          </div>
        `;
      }
    } else if (data.markdown) {
      const blocks = String(data.markdown).split(/\n##\s+/);
      for (const blk of blocks) {
        const lines = blk.trim().split('\n');
        const heading = lines[0].replace(/^#\s*/, '');
        const items = lines.slice(1).filter(l => l.trim()).map(l => l.replace(/^-\s*/, '').replace(/\*\*(.*?)\*\*/g, '<b>$1</b>'));
        html += `<div class="report-section-card"><h4>${heading}</h4><ul>${items.map(i => `<li>${i}</li>`).join('')}</ul></div>`;
      }
    }
    return html;
  }

  function initTab10Viz() {
    const subtabs = new window.SubtabController('t10-subtabs');

    // Pill 2: Şekil 6 TF-IDF Keyness Heatmap
    subtabs.onFirstShow('t10-pane-heatmap', async () => {
      const container = document.getElementById('t10-heatmap-chart-container');
      if (container && !container.dataset.loaded) {
        const topK = parseInt(document.getElementById('t10-input-topk')?.value || '5', 10);
        const excludePropn = document.getElementById('t10-check-exclude-propn')?.checked ?? true;

        const res = await window.VizAPI.postJSON('/api/v1/lexicon/tfidf/dense', {
          top_k: topK,
          exclude_pos: excludePropn ? ['PROPN'] : [],
          sublinear_tf: true,
          smooth_idf: true
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
        mdDiv.innerHTML = formatReportHtml(data);
        if (tableDiv && data.summary_table) {
          window.DataTableRenderer.render(tableDiv, data.summary_table, 10);
        }
        mdDiv.dataset.loaded = 'true';
      }
    });
  }

  window.initTab10Viz = initTab10Viz;
})(window);
