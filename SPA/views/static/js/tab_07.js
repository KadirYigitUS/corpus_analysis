/**
 * Tab 7 Controller: Batch KWIC, Dispersion & Correlation Matrix.
 */
class Tab07Controller {
  constructor() {
    this.summaryGrid = null;
    this.corrGrid = null;
    this.hasRun = false;
  }

  init() {
    this.attachEvents();
    if (typeof window.initTab07Viz === 'function') window.initTab07Viz();
  }

  static parseGroupQuery(raw) {
    const text = (raw || '').trim();
    const groups = {};
    const flatTerms = [];
    if (text.includes(':') || text.includes('|')) {
      text.split('|').forEach((chunk) => {
        const part = chunk.trim();
        if (!part) return;
        if (part.includes(':')) {
          const [gName, wordsStr] = part.split(':', 2);
          const words = wordsStr.split(',').map((w) => w.trim()).filter(Boolean);
          if (gName.trim() && words.length > 0) groups[gName.trim()] = words;
          words.forEach((w) => { if (!flatTerms.includes(w)) flatTerms.push(w); });
        } else {
          part.split(',').map((w) => w.trim()).filter(Boolean).forEach((w) => {
            if (!flatTerms.includes(w)) flatTerms.push(w);
          });
        }
      });
    } else {
      text.split(',').map((w) => w.trim()).filter(Boolean).forEach((w) => {
        if (!flatTerms.includes(w)) flatTerms.push(w);
      });
    }
    return { terms: flatTerms, groups: Object.keys(groups).length > 0 ? groups : null, raw_input: text };
  }

  attachEvents() {
    const runBtn = document.getElementById('t7-btn-run-batch');
    if (runBtn) {
      runBtn.addEventListener('click', () => {
        if (window.SubtabController) window.SubtabController.invalidateAll('t7-subtabs');
        this.runBatchAnalysis();
      });
    }
    const chk = document.getElementById('t7-check-content');
    if (chk) {
      chk.addEventListener('change', () => {
        if (window.SubtabController) window.SubtabController.invalidateAll('t7-subtabs');
        if (this.hasRun) this.runBatchAnalysis();
      });
    }
    if (window.appState) {
      const onRefresh = () => {
        if (this.hasRun) this.runBatchAnalysis();
      };
      window.appState.on('scopeChanged', onRefresh);
      window.appState.on('viewParamsChanged', onRefresh);
    }
  }

  async runBatchAnalysis() {
    this.hasRun = true;
    const termsRaw = document.getElementById('t7-input-terms')?.value || 'robot, insan, dünya, uzay';
    const parsed = Tab07Controller.parseGroupQuery(termsRaw);
    const isContent = document.getElementById('t7-check-content')?.checked || false;
    const vp = Object.assign({}, window.appState ? window.appState.state.view_params : {});
    if (isContent) vp.filter_function_words = true;

    const payload = {
      terms: parsed.terms,
      groups: parsed.groups,
      raw_input: parsed.raw_input,
      view_params: vp,
      scope: window.appState ? window.appState.state.scope : { scope: 'all' },
      n_chunks: 10
    };

    try {
      const resp = await fetch('/api/v1/concordance/batch-dispersion', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (resp.ok) {
        const data = await resp.json();
        this.renderSummary(data.summary || []);
        this.renderCorrelations(data.pairwise || []);
      }
    } catch (err) {
      console.error('Failed to run batch dispersion analysis:', err);
    }
  }

  renderSummary(items) {
    this.summaryGrid = new TableGrid('t7-summary-grid', {
      columns: [
        { key: 'label', label: 'Term' },
        { key: 'hits', label: 'Total Hits' },
        { key: 'per10k_pooled', label: 'Per 10k', render: v => v ? v.toFixed(2) : '0' },
        { key: 'texts_present', label: 'Texts Present' },
        { key: 'D_across_texts', label: "Juilland's D (Across)", render: v => v ? v.toFixed(3) : '-' },
        { key: 'D_within_text(mean)', label: "Juilland's D (Within)", render: v => v ? v.toFixed(3) : '-' }
      ],
      data: items,
      pageSize: 10
    });
    this.summaryGrid.render();
  }

  renderCorrelations(pairs) {
    this.corrGrid = new TableGrid('t7-correlation-grid', {
      columns: [
        { key: 'term_a', label: 'Term A' },
        { key: 'term_b', label: 'Term B' },
        { key: 'pearson_r', label: 'Pearson r', render: v => v !== null ? v.toFixed(3) : '-' },
        { key: 'q_pearson', label: 'q (BH-FDR)', render: v => v !== null ? v.toFixed(4) : '-' },
        { key: 'spearman_rho', label: 'Spearman ρ', render: v => v !== null ? v.toFixed(3) : '-' },
        { key: 'cosine', label: 'Cosine Sim.', render: v => v !== null ? v.toFixed(3) : '-' }
      ],
      data: pairs,
      pageSize: 10
    });
    this.corrGrid.render();
  }
}

window.tab07 = new Tab07Controller();
