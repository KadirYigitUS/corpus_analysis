/**
 * Reusable Interactive DataGrid Component: Sorting, Pagination, and Search.
 */
class TableGrid {
  constructor(containerOrId, columnsOrOptions = {}, maybeOptions = {}) {
    this.container = typeof containerOrId === 'string'
      ? document.getElementById(containerOrId)
      : containerOrId;
    const options = Array.isArray(columnsOrOptions)
      ? Object.assign({}, maybeOptions, { columns: columnsOrOptions })
      : (columnsOrOptions || {});
    this.columns = options.columns || [];
    this.data = options.data || [];
    this.filteredData = [...this.data];
    this.pageSize = options.pageSize || 20;
    this.currentPage = 1;
    this.sortCol = options.initialSortCol || null;
    this.sortAsc = options.initialSortAsc !== undefined ? options.initialSortAsc : true;
    this.searchTerm = '';
    if (options.data) {
      this.render();
    }
  }

  setData(data) {
    this.data = data || [];
    this.filteredData = [...this.data];
    this.currentPage = 1;
    this.render();
  }

  getFilteredData() {
    if (!this.searchTerm) {
      this.filteredData = [...this.data];
      return this.filteredData;
    }
    const term = this.searchTerm.toLowerCase();
    this.filteredData = this.data.filter(row =>
      Object.values(row).some(v => String(v).toLowerCase().includes(term))
    );
    return this.filteredData;
  }

  getSortedData() {
    const list = [...this.getFilteredData()];
    if (!this.sortCol) return list;
    const col = this.sortCol;
    const asc = this.sortAsc ? 1 : -1;

    return list.sort((a, b) => {
      let v1 = a[col], v2 = b[col];
      if (v1 === null || v1 === undefined) return 1;
      if (v2 === null || v2 === undefined) return -1;
      if (typeof v1 === 'number' && typeof v2 === 'number') {
        return (v1 - v2) * asc;
      }
      return String(v1).localeCompare(String(v2), undefined, { numeric: true }) * asc;
    });
  }

  render() {
    if (!this.container) return;
    const sorted = this.getSortedData();
    const totalRows = sorted.length;
    const totalPages = Math.max(1, Math.ceil(totalRows / this.pageSize));
    this.currentPage = Math.min(this.currentPage, totalPages);

    const start = (this.currentPage - 1) * this.pageSize;
    const paged = sorted.slice(start, start + this.pageSize);

    const wrapper = this.container.querySelector('.datagrid-container');
    if (!wrapper) {
      this.container.innerHTML = `
        <div class="datagrid-container">
          <div class="datagrid-toolbar">
            <input type="text" class="form-input grid-search" placeholder="Search table..." value="${this.searchTerm}" style="max-width:220px;" />
            <span class="grid-stats chip">${totalRows} rows</span>
          </div>
          <div class="datagrid-table-wrapper">
            <table class="datagrid-table">
              <thead><tr>
                ${this.columns.map(c => `
                  <th data-col="${c.key}">
                    ${c.label}
                    <span class="sort-icon">${this.sortCol === c.key ? (this.sortAsc ? '▲' : '▼') : ''}</span>
                  </th>
                `).join('')}
              </tr></thead>
              <tbody></tbody>
            </table>
          </div>
          <div class="datagrid-pagination">
            <span class="page-info">Page ${this.currentPage} of ${totalPages}</span>
            <div class="pagination-controls">
              <button class="btn btn-sm prev-page" ${this.currentPage <= 1 ? 'disabled' : ''}>Prev</button>
              <button class="btn btn-sm next-page" ${this.currentPage >= totalPages ? 'disabled' : ''}>Next</button>
            </div>
          </div>
        </div>
      `;
      this.attachEvents();
    }

    const tbody = this.container.querySelector('tbody');
    if (tbody) {
      tbody.innerHTML = paged.map(row => `
        <tr>
          ${this.columns.map(c => `<td>${c.render ? c.render(row[c.key], row) : (row[c.key] ?? '')}</td>`).join('')}
        </tr>
      `).join('');
    }

    const stats = this.container.querySelector('.grid-stats');
    if (stats) stats.textContent = `${totalRows} rows`;

    const pageInfo = this.container.querySelector('.page-info');
    if (pageInfo) pageInfo.textContent = `Page ${this.currentPage} of ${totalPages}`;

    const prevBtn = this.container.querySelector('.prev-page');
    if (prevBtn) prevBtn.disabled = this.currentPage <= 1;

    const nextBtn = this.container.querySelector('.next-page');
    if (nextBtn) nextBtn.disabled = this.currentPage >= totalPages;

    const ths = this.container.querySelectorAll('th[data-col]');
    ths.forEach(th => {
      const col = th.getAttribute('data-col');
      const icon = th.querySelector('.sort-icon');
      if (icon) icon.textContent = this.sortCol === col ? (this.sortAsc ? '▲' : '▼') : '';
    });
  }

  attachEvents() {
    const searchInp = this.container.querySelector('.grid-search');
    if (searchInp) {
      searchInp.addEventListener('input', (e) => {
        this.searchTerm = e.target.value;
        this.currentPage = 1;
        this.render();
      });
    }

    const ths = this.container.querySelectorAll('th[data-col]');
    ths.forEach(th => {
      th.addEventListener('click', () => {
        const col = th.getAttribute('data-col');
        if (this.sortCol === col) {
          this.sortAsc = !this.sortAsc;
        } else {
          this.sortCol = col;
          this.sortAsc = true;
        }
        this.render();
      });
    });

    const prevBtn = this.container.querySelector('.prev-page');
    if (prevBtn) {
      prevBtn.addEventListener('click', () => {
        if (this.currentPage > 1) {
          this.currentPage--;
          this.render();
        }
      });
    }

    const nextBtn = this.container.querySelector('.next-page');
    if (nextBtn) {
      nextBtn.addEventListener('click', () => {
        this.currentPage++;
        this.render();
      });
    }
  }
}

window.TableGrid = TableGrid;

