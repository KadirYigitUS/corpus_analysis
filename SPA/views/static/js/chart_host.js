/**
 * chart_host.js - Visual chart card container with PNG image and CSV export.
 */
(function(window) {
  'use strict';

  function createChartCard(title, canvasId, height = 260) {
    const card = document.createElement('div');
    card.className = 'chart-card';

    const header = document.createElement('div');
    header.className = 'chart-header';
    header.innerHTML = `
      <div class="chart-title">${title}</div>
      <div class="chart-actions">
        <button class="btn btn-sm btn-export-png" title="Download PNG">📷 PNG</button>
        <button class="btn btn-sm btn-export-csv" title="Export CSV Data">📄 CSV</button>
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

    header.querySelector('.btn-export-png').onclick = () => {
      const link = document.createElement('a');
      link.download = `${canvasId}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
    };

    return { card, canvas, header, container };
  }

  function exportTableCsv(filename, rows, columns) {
    if (!rows || !rows.length) return;
    const header = columns.map(c => `"${c.label || c.key}"`).join(',');
    const body = rows.map(r => columns.map(c => `"${r[c.key] !== undefined ? r[c.key] : ''}"`).join(',')).join('\n');
    const blob = new Blob([`${header}\n${body}`], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
  }

  window.ChartHost = {
    createChartCard,
    exportTableCsv
  };
})(window);
