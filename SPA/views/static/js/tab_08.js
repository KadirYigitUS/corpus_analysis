/**
 * Tab 8 Controller: Lexical Diversity & Richness Laboratory.
 */
class Tab08Controller {
  constructor() {
    this.grid = null;
  }

  async init() {
    this.attachEvents();
    if (typeof window.initTab08Viz === 'function') window.initTab08Viz();
    await this.loadDiversityTable();
  }

  async loadDiversityTable() {
    const payload = {
      view_params: window.appState ? window.appState.state.view_params : {},
      scope: window.appState ? window.appState.state.scope : { scope: 'all' }
    };

    try {
      const resp = await fetch('/api/v1/lexicon/diversity/table', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (resp.ok) {
        const data = await resp.json();
        this.renderTable(data.items || []);
      }
    } catch (err) {
      console.error('Failed to load diversity table:', err);
    }
  }

  renderTable(items) {
    this.grid = new TableGrid('t8-diversity-grid', {
      columns: [
        { key: 'text_code', label: 'Code' },
        { key: 'N', label: 'Tokens (N)' },
        { key: 'V', label: 'Types (V)' },
        { key: 'TTR', label: 'TTR', render: v => v ? v.toFixed(3) : '-' },
        { key: 'Guiraud_R', label: 'Guiraud R', render: v => v ? v.toFixed(2) : '-' },
        { key: 'Yule_K', label: 'Yule K', render: v => v ? v.toFixed(2) : '-' },
        { key: 'Simpson_D', label: 'Simpson D', render: v => v ? v.toFixed(4) : '-' },
        { key: 'MATTR_500', label: 'MATTR (500)', render: v => v ? v.toFixed(3) : '-' },
        { key: 'MTLD', label: 'MTLD', render: v => v ? v.toFixed(2) : '-' },
        { key: 'HD_D', label: 'HD-D', render: v => v ? v.toFixed(3) : '-' }
      ],
      data: items,
      pageSize: 15
    });
    this.grid.render();
  }

  attachEvents() {
    const refreshBtn = document.getElementById('t8-btn-refresh-diversity');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', () => {
        if (window.SubtabController) window.SubtabController.invalidateAll('t8-subtabs');
        this.loadDiversityTable();
      });
    }

    const mattrBtn = document.getElementById('t8-btn-view-mattr');
    if (mattrBtn) {
      mattrBtn.addEventListener('click', () => this.loadMattrTrajectory());
    }

    const textSel = document.getElementById('t8-select-text');
    if (textSel) {
      textSel.addEventListener('change', () => {
        if (window.SubtabController) window.SubtabController.invalidateAll('t8-subtabs');
        const pane = document.getElementById('t8-mattr-pane');
        if (pane && pane.style.display !== 'none') this.loadMattrTrajectory();
      });
    }

    if (window.appState) {
      const onRefresh = () => {
        this.loadDiversityTable();
        const pane = document.getElementById('t8-mattr-pane');
        if (pane && pane.style.display !== 'none') this.loadMattrTrajectory();
      };
      window.appState.on('scopeChanged', onRefresh);
      window.appState.on('viewParamsChanged', onRefresh);
    }
  }

  async loadMattrTrajectory() {
    const textCode = document.getElementById('t8-select-text')?.value || 'BR-SM';
    const payload = {
      text_code: textCode,
      view_params: window.appState ? window.appState.state.view_params : {},
      window: 500
    };

    try {
      const resp = await fetch('/api/v1/lexicon/diversity/mattr', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (resp.ok) {
        const res = await resp.json();
        const pane = document.getElementById('t8-mattr-pane');
        if (pane) {
          pane.style.display = 'block';
          pane.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:8px;">
              <div style="font-size:12px;">
                <b>MATTR Curve (W=${res.window || 500}) for ${res.text_code}:</b> ${res.total_windows} rolling windows calculated.
              </div>
              <div style="display:flex; flex-wrap:wrap; gap:6px;">
                <span class="stat-badge-math">W = <b>${res.window || 500}</b></span>
                <span class="stat-badge-math">&mu; = <b>${res.mean_ttr ?? '-'}</b></span>
                <span class="stat-badge-math">&sigma; = <b>${res.std_ttr ?? '-'}</b></span>
                <span class="stat-badge-math">Min = <b>${res.min_ttr ?? '-'}</b></span>
                <span class="stat-badge-math">Max = <b>${res.max_ttr ?? '-'}</b></span>
              </div>
            </div>
            <div style="font-size:11px; color:var(--text-muted);">
              Sample Points: ${res.points.slice(0, 10).map(p => `[#${p.window_idx}: ${p.ttr}]`).join(', ')} ...
            </div>
          `;
        }
      }
    } catch (err) {
      console.error('Failed to load MATTR trajectory:', err);
    }
  }
}

window.tab08 = new Tab08Controller();
