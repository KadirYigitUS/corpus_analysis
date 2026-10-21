/**
 * Tab 4 Controller: Comparative POS & Morphosyntactic Profiler.
 */
class Tab04Controller {
  constructor() {
    this.grid = null;
    this.currentPair = 'IR-IA_BR-SM';
  }

  async init() {
    await this.loadPosProfiles();
    await this.loadPairDelta();
    await this.loadGroupComparison();
  }

  async loadPosProfiles() {
    try {
      const resp = await fetch('/api/v1/syntax/pos/profiles', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scope: 'all', content_only: false })
      });
      if (resp.ok) {
        const data = await resp.json();
        this.renderProfilesTable(data.items || []);
      }
    } catch (err) {
      console.error('Failed to load POS profiles:', err);
    }
  }

  renderProfilesTable(items) {
    this.grid = new TableGrid('t4-pos-profiles-grid', {
      columns: [
        { key: 'code', label: 'Code' },
        { key: 'language', label: 'Lang' },
        { key: 'NOUN', label: 'NOUN %', render: v => v ? `${v.toFixed(1)}%` : '-' },
        { key: 'VERB', label: 'VERB %', render: v => v ? `${v.toFixed(1)}%` : '-' },
        { key: 'ADJ', label: 'ADJ %', render: v => v ? `${v.toFixed(1)}%` : '-' },
        { key: 'ADV', label: 'ADV %', render: v => v ? `${v.toFixed(1)}%` : '-' },
        { key: 'lexical_density', label: 'Lex. Density', render: v => v ? `${v.toFixed(1)}%` : '-' },
        { key: 'noun_verb_ratio', label: 'N/V Ratio', render: v => v ? v.toFixed(2) : '-' }
      ],
      data: items,
      pageSize: 15
    });
    this.grid.render();
  }

  async loadPairDelta() {
    try {
      const resp = await fetch(`/api/v1/syntax/pos/pair-delta/${this.currentPair}`);
      if (resp.ok) {
        const data = await resp.json();
        const container = document.getElementById('t4-pair-delta-container');
        if (!container) return;
        container.innerHTML = `
          <div style="font-size:12px; margin-bottom:8px; color:var(--text-secondary);">
            Pair: <b>${data.pair_code}</b> (Turkish % − English % divergence in percentage points):
          </div>
          <div style="display:flex; flex-wrap:wrap; gap:8px;">
            ${(data.items || []).map(item => `
              <div class="kpi-card" style="padding:6px 10px; font-size:11.5px; min-width:110px;">
                <div style="font-weight:600; color:var(--accent-blue);">${item.upos}</div>
                <div style="font-size:13px; font-weight:700; color:${item.delta_pp >= 0 ? 'var(--accent-teal)' : 'var(--accent-rose)'};">
                  ${item.delta_pp > 0 ? '+' : ''}${item.delta_pp} pp
                </div>
                <div style="font-size:10px; color:var(--text-muted);">EN ${item.eng_pct}% | TR ${item.tur_pct}%</div>
              </div>
            `).join('')}
          </div>
        `;
      }
    } catch (err) {
      console.error('Failed to load pair delta:', err);
    }
  }

  async loadGroupComparison() {
    try {
      const resp = await fetch('/api/v1/syntax/pos/group-comparison', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ group_a: 'trans_tr', group_b: 'indig_tr', n_bootstrap: 1000 })
      });
      if (resp.ok) {
        const data = await resp.json();
        const statEl = document.getElementById('t4-group-comp-stats');
        if (statEl) {
          statEl.innerHTML = `
            <span class="chip">χ² = ${data.chi2}</span>
            <span class="chip">p = ${data.p_value.toFixed(4)}</span>
            <span class="chip">Cramér's V = ${data.cramers_v}</span>
          `;
        }

        const listEl = document.getElementById('t4-group-comp-list');
        if (listEl) {
          listEl.innerHTML = (data.items || []).slice(0, 8).map(it => `
            <div style="display:flex; justify-content:space-between; padding:5px 0; border-bottom:1px solid #334155; font-size:12px;">
              <span><b>${it.upos}</b> (Diff: ${it.mean_diff_pp} pp)</span>
              <span style="color:var(--text-muted);">95% CI: [${it.ci_low}, ${it.ci_high}]</span>
            </div>
          `).join('');
        }
      }
    } catch (err) {
      console.error('Failed to load group comparison:', err);
    }
  }
}

window.tab04 = new Tab04Controller();
