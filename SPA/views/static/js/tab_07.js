/**
 * Tab 7 Controller: Batch KWIC, Dispersion & Correlation Matrix.
 */
class Tab07Controller {
  constructor() {
    this.summaryGrid = null;
    this.corrGrid = null;
  }

  init() {
    this.attachEvents();
  }

  attachEvents() {
    const runBtn = document.getElementById('t7-btn-run-batch');
    if (runBtn) {
      runBtn.addEventListener('click', () => this.runBatchAnalysis());
    }
  }

  async runBatchAnalysis() {
    const termsRaw = document.getElementById('t7-input-terms')?.value || 'robot, insan, dünya, uzay';
    const terms = termsRaw.split(',').map(t => t.trim()).filter(Boolean);

    const payload = {
      terms: terms,
      view_params: window.appState ? window.appState.state.view_params : {},
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
