/**
 * Tab 4 Controller: Comparative POS & Morphosyntactic Profiler.
 */
class Tab04Controller {
  constructor() {
    this.grid = null;
    this.currentPair = 'IR-IA_BR-SM';
    this.currentCompKey = 'ALL';
    this.authorSummary = [];
  }

  async init() {
    this.attachEvents();
    if (typeof window.initTab04Viz === 'function') window.initTab04Viz();
    await Promise.all([
      this.loadPosProfiles(),
      this.loadAuthorSummary(),
      this.loadPairDelta(),
      this.loadGroupComparison(),
    ]);
  }

  getContentOnly() {
    const chk = document.getElementById('t4-check-content-only');
    return Boolean((chk && chk.checked) || (window.appState && window.appState.state.view_params && window.appState.state.view_params.filter_function_words));
  }

  async loadPosProfiles() {
    try {
      const payload = window.appState && window.appState.buildRequestPayload
        ? window.appState.buildRequestPayload({ content_only: this.getContentOnly() })
        : { scope: 'all', content_only: this.getContentOnly() };
      const resp = await fetch('/api/v1/syntax/pos/profiles', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (resp.ok) {
        const data = await resp.json();
        this.renderProfilesTable(data.items || []);
      }
    } catch (err) { console.error('Failed to load POS profiles:', err); }
  }

  renderProfilesTable(items) {
    const fmt = (v, d = 1, suf = '%') => (v !== null && v !== undefined ? `${v.toFixed(d)}${suf}` : '-');
    this.grid = new TableGrid('t4-pos-profiles-grid', {
      columns: [
        { key: 'code', label: 'Code' },
        { key: 'language', label: 'Lang' },
        { key: 'NOUN', label: 'NOUN %', render: (v) => fmt(v) },
        { key: 'VERB', label: 'VERB %', render: (v) => fmt(v) },
        { key: 'ADJ', label: 'ADJ %', render: (v) => fmt(v) },
        { key: 'ADV', label: 'ADV %', render: (v) => fmt(v) },
        { key: 'lexical_density', label: 'Lex. Density', render: (v) => fmt(v) },
        { key: 'noun_verb_ratio', label: 'N/V Ratio', render: (v) => fmt(v, 2, '') },
      ],
      data: items,
      pageSize: 15,
    });
    this.grid.render();
  }

  async loadAuthorSummary() {
    try {
      const qs = window.appState && window.appState.buildQueryParams
        ? `?${window.appState.buildQueryParams({ content_only: this.getContentOnly() }).toString()}`
        : `?content_only=${this.getContentOnly()}`;
      const resp = await fetch(`/api/v1/syntax/pos/author-summary${qs}`);
      if (resp.ok) {
        const data = await resp.json();
        this.authorSummary = data.items || [];
        this.renderAuthorSummary();
      }
    } catch (err) { console.error('Failed to load author POS summary:', err); }
  }

  renderAuthorSummary() {
    const el = document.getElementById('t4-author-summary-table');
    if (!el) return;
    el.innerHTML = `<table class="datagrid-table" style="font-size:11.5px;"><thead><tr>
      <th>Key</th><th>Author</th><th>Trans TR ⇄ Indig TR</th><th>Chunks (A/B)</th>
      <th>χ²</th><th>Cramér's V</th><th>Perm. p-value</th>
      <th>Δ Lex. Density</th><th>Δ N/V Ratio</th><th>Top Divergent UPOS</th>
    </tr></thead><tbody>${this.authorSummary.map((r) => `<tr class="t4-summary-row ${r.key === this.currentCompKey ? 't2-row-pos' : ''}" data-comp-key="${r.key}" style="cursor:pointer;">
      <td><b>${r.key}</b></td><td><span class="chip">${r.author}</span></td><td>${r.trans_codes} ⇄ ${r.indig_codes}</td>
      <td class="cell-num">${r.n_chunks_a} / ${r.n_chunks_b}</td><td class="cell-num">${r.chi2.toFixed(2)}</td>
      <td class="cell-num">${r.cramers_v.toFixed(4)}</td><td class="cell-num"><b>${r.p_value.toFixed(4)}</b></td>
      <td class="cell-num">${r.delta_lex_density > 0 ? '+' : ''}${r.delta_lex_density.toFixed(2)} pp</td>
      <td class="cell-num">${r.delta_nv_ratio > 0 ? '+' : ''}${r.delta_nv_ratio.toFixed(2)}</td><td>${r.top_divergent_upos}</td>
    </tr>`).join('')}</tbody></table>`;
    el.querySelectorAll('.t4-summary-row').forEach((tr) => {
      tr.onclick = () => {
        this.currentCompKey = tr.getAttribute('data-comp-key');
        const sel = document.getElementById('t4-select-comp-2c');
        if (sel) sel.value = this.currentCompKey;
        this.renderAuthorSummary(); this.loadGroupComparison();
      };
    });
  }

  async loadPairDelta() {
    try {
      const qs = window.appState && window.appState.buildQueryParams
        ? `?${window.appState.buildQueryParams({ content_only: this.getContentOnly() }).toString()}`
        : `?content_only=${this.getContentOnly()}`;
      const resp = await fetch(`/api/v1/syntax/pos/pair-delta/${this.currentPair}${qs}`);
      if (resp.ok) {
        const data = await resp.json();
        const container = document.getElementById('t4-pair-delta-container');
        if (!container) return;
        container.innerHTML = `
          <div style="font-size:12px; margin-bottom:8px; color:var(--text-secondary);">
            Pair: <b>${data.pair_code}</b> (Turkish % − English % divergence in percentage points):
          </div>
          <div style="display:flex; flex-wrap:wrap; gap:8px;">
            ${(data.items || []).map((item) => `
              <div class="kpi-card" style="padding:6px 10px; font-size:11.5px; min-width:110px;">
                <div style="font-weight:600; color:var(--accent-blue);">${item.upos}</div>
                <div style="font-size:13px; font-weight:700; color:${item.delta_pp >= 0 ? 'var(--accent-teal)' : 'var(--accent-rose)'};">
                  ${item.delta_pp > 0 ? '+' : ''}${item.delta_pp} pp
                </div>
                <div style="font-size:10px; color:var(--text-muted);">EN ${item.eng_pct}% | TR ${item.tur_pct}%</div>
              </div>
            `).join('')}
          </div>`;
      }
    } catch (err) { console.error('Failed to load pair delta:', err); }
  }

  async loadGroupComparison() {
    try {
      const payload = window.appState && window.appState.buildRequestPayload
        ? window.appState.buildRequestPayload({ group_a: 'trans_tr', group_b: 'indig_tr', comparison_key: this.currentCompKey, content_only: this.getContentOnly(), n_bootstrap: 800 })
        : { group_a: 'trans_tr', group_b: 'indig_tr', comparison_key: this.currentCompKey, content_only: this.getContentOnly(), n_bootstrap: 800 };
      const resp = await fetch('/api/v1/syntax/pos/group-comparison', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
      });
      if (resp.ok) {
        const data = await resp.json();
        const statEl = document.getElementById('t4-group-comp-stats');
        if (statEl) {
          statEl.innerHTML = `
            <span id="t4-comp-2c-stats" style="display:inline-flex; flex-wrap:wrap; gap:6px;">
              <span class="chip chip-active">${data.author || this.currentCompKey}</span>
              <span class="stat-badge-math">&chi;<sup>2</sup> = <b>${data.chi2}</b></span>
              <span class="stat-badge-math" id="t4-comp-pval">p = <b>${Number(data.p_value).toFixed(4)}</b></span>
              <span class="stat-badge-math">Cramér's V = <b>${data.cramers_v}</b></span>
              <span class="stat-badge-math">Chunks: <b>${data.n_chunks_a || '-'} vs ${data.n_chunks_b || '-'}</b></span>
            </span>
          `;
        }
        const listEl = document.getElementById('t4-group-comp-list');
        if (listEl) {
          listEl.innerHTML = (data.items || []).slice(0, 10).map((it) => `
            <div style="display:flex; justify-content:space-between; align-items:center; padding:5px 0; border-bottom:1px solid #334155; font-size:11.5px;">
              <span><b>${it.upos}</b> (${it.mean_diff_pp > 0 ? '+' : ''}${it.mean_diff_pp} pp)</span>
              <span style="color:var(--text-secondary);">p=${Number(it.p_val ?? 1).toFixed(4)} | q=${Number(it.q_val ?? 1).toFixed(4)}</span>
              <span style="color:var(--text-muted);">95% CI: [${it.ci_low}, ${it.ci_high}]</span>
            </div>
          `).join('');
        }
      }
    } catch (err) { console.error('Failed to load group comparison:', err); }
  }

  attachEvents() {
    const sel2b = document.getElementById('t4-select-pair-2b');
    if (sel2b) sel2b.addEventListener('change', (e) => { this.currentPair = e.target.value; this.loadPairDelta(); if (window.SubtabController) window.SubtabController.invalidateAll('t4-subtabs'); });
    const sel2c = document.getElementById('t4-select-comp-2c');
    if (sel2c) sel2c.addEventListener('change', (e) => { this.currentCompKey = e.target.value; this.renderAuthorSummary(); this.loadGroupComparison(); if (window.SubtabController) window.SubtabController.invalidateAll('t4-subtabs'); });
    const chk = document.getElementById('t4-check-content-only');
    if (chk) chk.addEventListener('change', () => { this.loadPosProfiles(); this.loadAuthorSummary(); this.loadPairDelta(); this.loadGroupComparison(); if (window.SubtabController) window.SubtabController.invalidateAll('t4-subtabs'); });
    if (window.appState) {
      const onRefresh = () => { this.loadPosProfiles(); this.loadAuthorSummary(); this.loadPairDelta(); this.loadGroupComparison(); };
      window.appState.on('scopeChanged', onRefresh);
      window.appState.on('viewParamsChanged', onRefresh);
    }
  }
}

window.tab04 = new Tab04Controller();
