/**
 * chart_host.js - Visual chart card container with PNG image and CSV export.
 */
(function(window) {
  'use strict';

  function exportTableCsv(filename, rows, columns) {
    if (!rows || !rows.length) return;
    const cols = columns && columns.length
      ? columns
      : Object.keys(rows[0]).map(k => ({ key: k, label: k }));
    const esc = (val) => `"${String(val ?? '').replace(/"/g, '""')}"`;
    const header = cols.map(c => esc(c.label || c.key)).join(',');
    const body = rows.map(r => cols.map(c => esc(r[c.key])).join(',')).join('\n');
    const blob = new Blob([`\uFEFF${header}\n${body}`], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
    URL.revokeObjectURL(link.href);
  }

  function extractHitboxCsvRows(canvas) {
    const rows = [];
    const container = canvas.parentElement;
    if (window.ChartCore && window.ChartCore._instances) {
      for (const inst of window.ChartCore._instances) {
        if (inst.canvas === canvas && Array.isArray(inst.hitBoxes)) {
          inst.hitBoxes.forEach((hb, idx) => {
            rows.push({
              index: idx + 1,
              label: String(hb.text || '').replace(/<[^>]+>/g, ' ').trim(),
              x: Math.round(hb.x),
              y: Math.round(hb.y)
            });
          });
        }
      }
    }
    if (!rows.length && container) {
      rows.push({ chart_id: canvas.id, status: 'rendered' });
    }
    return rows;
  }

  function createChartCard(title, canvasId, height = 260, csvRows = null, csvCols = null) {
    const card = document.createElement('div');
    card.className = 'chart-card';
    const m = String(canvasId || '').match(/^t(\d+)/i);
    const helpTab = m ? `Tab ${parseInt(m[1], 10)}` : 'Global Matrix';

    const header = document.createElement('div');
    header.className = 'chart-header';
    header.innerHTML = `
      <div class="chart-title">${title}</div>
      <div class="chart-actions">
        <button class="btn btn-sm btn-export-png" title="Download PNG">📷 PNG</button>
        <button class="btn btn-sm btn-export-csv" title="Export CSV Data">📄 CSV</button>
        <button class="btn btn-sm btn-pane-help" data-help-tab="${helpTab}" title="Contextual Formula &amp; Pane Help">?</button>
      </div>
    `;

    const container = document.createElement('div');
    container.className = 'chart-canvas-container';
    container.style.height = `${height}px`;

    const canvas = document.createElement('canvas');
    canvas.id = canvasId;
    canvas.style.width = '100%';
    canvas.style.height = '100%';
    container.appendChild(canvas);

    card.appendChild(header);
    card.appendChild(container);

    let boundRows = csvRows;
    let boundCols = csvCols;

    header.querySelector('.btn-export-png').onclick = () => {
      const link = document.createElement('a');
      link.download = `${canvasId}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
    };

    header.querySelector('.btn-export-csv').onclick = () => {
      const rows = (boundRows && boundRows.length) ? boundRows : extractHitboxCsvRows(canvas);
      exportTableCsv(`${canvasId}.csv`, rows, boundCols);
    };

    const setCsvData = (rows, columns = null) => {
      boundRows = rows;
      boundCols = columns;
    };

    return { card, canvas, header, container, setCsvData };
  }

  window.ChartHost = {
    createChartCard,
    exportTableCsv
  };
})(window);

