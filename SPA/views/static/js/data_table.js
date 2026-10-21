/**
 * data_table.js - Lightweight TableGrid builder for dynamic TablePayload objects.
 */
(function(window) {
  'use strict';

  class DataTableRenderer {
    static render(containerId, tablePayload, pageSize = 20) {
      const container = typeof containerId === 'string' ? document.getElementById(containerId) : containerId;
      if (!container) return;

      container.innerHTML = '';
      const gridDiv = document.createElement('div');
      container.appendChild(gridDiv);

      const columns = (tablePayload.columns || []).map(col => ({
        key: col.key,
        label: col.label || col.key,
        sortable: true,
        type: col.type || 'str'
      }));

      const rows = tablePayload.rows || [];
      const grid = new window.TableGrid(gridDiv, {
        columns: columns,
        data: rows,
        pageSize: pageSize,
        enableSearch: true
      });

      return grid;
    }
  }

  window.DataTableRenderer = DataTableRenderer;
})(window);
