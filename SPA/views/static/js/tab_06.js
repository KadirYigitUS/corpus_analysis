/**
 * Tab 6 Controller: Corpus Search & 5-View KWIC Concordancer.
 */
class Tab06Controller {
  constructor() {
    this.grid = null;
    this.hasSearched = false;
  }

  init() {
    this.attachEvents();
    if (typeof window.initTab06Viz === 'function') window.initTab06Viz();
  }

  attachEvents() {
    const searchBtn = document.getElementById('t6-btn-search');
    if (searchBtn) {
      searchBtn.addEventListener('click', () => {
        if (window.SubtabController) window.SubtabController.invalidateAll('t6-subtabs');
        this.executeSearch();
      });
    }

    const punctBtn = document.getElementById('t6-btn-punct-compare');
    if (punctBtn) {
      punctBtn.addEventListener('click', () => this.comparePunctuation());
    }

    if (window.appState) {
      const onRefresh = () => {
        if (this.hasSearched) this.executeSearch();
      };
      window.appState.on('scopeChanged', onRefresh);
      window.appState.on('viewParamsChanged', onRefresh);
    }
  }

  async executeSearch() {
    this.hasSearched = true;
    const query = document.getElementById('t6-input-query')?.value || 'robot';
    const matchMode = document.getElementById('t6-select-match')?.value || 'exact';
    const sortBy = document.getElementById('t6-select-sort')?.value || 'position';
    const spanL = parseInt(document.getElementById('t6-input-span-l')?.value || '5');
    const spanR = parseInt(document.getElementById('t6-input-span-r')?.value || '5');

    const payload = {
      query: query,
      match_mode: matchMode,
      window_left: spanL,
      window_right: spanR,
      view_params: window.appState ? window.appState.state.view_params : {},
      scope: window.appState ? window.appState.state.scope : { scope: 'all' },
      sort_by: sortBy
    };

    try {
      const resp = await fetch('/api/v1/concordance/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const result = await resp.json();
      if (resp.ok && !result.error) {
        document.getElementById('t6-hit-count').innerText = `${result.total_hits} hits`;
        this.renderKwicTable(result.lines || []);
      } else {
        document.getElementById('t6-hit-count').innerText = 'Error';
        const gridEl = document.getElementById('t6-kwic-grid');
        if (gridEl) {
          gridEl.innerHTML = `<div class="kpi-card" id="t6-search-error" style="color:var(--accent-rose); border-color:var(--accent-rose);">${result.error || 'Invalid search expression'}</div>`;
        }
      }
    } catch (err) {
      console.error('Failed to execute concordance search:', err);
    }
  }

  renderKwicTable(lines) {
    this.grid = new TableGrid('t6-kwic-grid', {
      columns: [
        { key: 'hit_id', label: '#' },
        { key: 'text_code', label: 'Text' },
        {
          key: 'left',
          label: 'Left Context',
          render: v => `<div style="text-align:right; color:var(--text-secondary); max-width:240px; overflow:hidden; text-overflow:ellipsis;">${v}</div>`
        },
        {
          key: 'node',
          label: 'Node Word',
          render: v => `<span class="chip chip-active" style="font-weight:700;">${v}</span>`
        },
        {
          key: 'right',
          label: 'Right Context',
          render: v => `<div style="text-align:left; color:var(--text-secondary); max-width:240px; overflow:hidden; text-overflow:ellipsis;">${v}</div>`
        },
        { key: 'coords', label: 'Coords' }
      ],
      data: lines,
      pageSize: 20
    });
    this.grid.render();
  }

  async comparePunctuation() {
    const query = document.getElementById('t6-input-query')?.value || 'robot';
    const payload = {
      query: query,
      scope: window.appState ? window.appState.state.scope : { scope: 'all' }
    };

    try {
      const resp = await fetch('/api/v1/concordance/punct-compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (resp.ok) {
        const data = await resp.json();
        const pane = document.getElementById('t6-punct-pane');
        if (pane) {
          pane.style.display = 'block';
          pane.innerHTML = `
            <div style="font-size:12px; margin-bottom:4px; font-weight:600;">4-Punctuation Regime Comparison for "${query}":</div>
            <div style="display:flex; gap:8px;">
              ${Object.entries(data.counts || {}).map(([mode, cnt]) => `
                <div class="kpi-card" style="padding:6px 12px; font-size:12px;">
                  <b>${mode.toUpperCase()}</b>: <span class="chip">${cnt} hits</span>
                </div>
              `).join('')}
            </div>
          `;
        }
      }
    } catch (err) {
      console.error('Failed to compare punctuation regimes:', err);
    }
  }
}

window.tab06 = new Tab06Controller();
