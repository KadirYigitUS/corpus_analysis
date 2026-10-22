/**
 * data_table.js - Lightweight TableGrid builder for dynamic TablePayload objects.
 */
(function(window) {
  'use strict';

  function downloadCsvWithBom(filename, rows, columns) {
    if (!rows || !rows.length) return;
    const esc = (val) => `"${String(val ?? '').replace(/"/g, '""')}"`;
    const header = columns.map(c => esc(c.label || c.key)).join(',');
    const body = rows.map(r => columns.map(c => esc(r[c.key])).join(',')).join('\n');
    const blob = new Blob([`\uFEFF${header}\n${body}`], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
    URL.revokeObjectURL(link.href);
  }

  class DataTableRenderer {
    static render(containerOrId, tablePayload, optionsOrPageSize = 15) {
      const container = typeof containerOrId === 'string'
        ? document.getElementById(containerOrId)
        : containerOrId;
      if (!container || !tablePayload) return null;

      const options = typeof optionsOrPageSize === 'number'
        ? { pageSize: optionsOrPageSize }
        : (optionsOrPageSize || {});

      container.innerHTML = '';

      const columns = (tablePayload.columns || []).map(col => ({
        key: col.key,
        label: col.label || col.key,
        sortable: true,
        type: col.type || 'str'
      }));
      const rows = tablePayload.rows || [];

      const headerBar = document.createElement('div');
      headerBar.className = 'chart-header';
      headerBar.style.marginBottom = '6px';
      const titleText = tablePayload.title || options.title || 'Data Table';
      headerBar.innerHTML = `
        <div class="chart-title">${titleText}</div>
        <div class="chart-actions">
          <button class="btn btn-sm btn-export-csv" title="Export CSV Data">📄 CSV</button>
        </div>
      `;
      container.appendChild(headerBar);

      const gridDiv = document.createElement('div');
      container.appendChild(gridDiv);

      const grid = new window.TableGrid(gridDiv, columns, {
        pageSize: options.pageSize || 15,
        searchable: true,
        data: rows
      });
      grid.render();

      const csvBtn = headerBar.querySelector('.btn-export-csv');
      if (csvBtn) {
        const slug = String(titleText).toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '') || 'table';
        csvBtn.onclick = () => downloadCsvWithBom(`${slug}.csv`, rows, columns);
      }

      return grid;
    }
  }

  window.DataTableRenderer = DataTableRenderer;
})(window);

