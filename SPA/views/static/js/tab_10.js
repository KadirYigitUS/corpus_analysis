/**
 * Tab 10 Controller: Sublinear TF-IDF Keyness & Research Reporter.
 */
class Tab10Controller {
  constructor() {
    this.currentDoc = 'BR-SM';
  }

  async init() {
    this.attachEvents();
    if (typeof window.initTab10Viz === 'function') window.initTab10Viz();
    await this.loadTfidfKeywords();
  }

  attachEvents() {
    const runBtn = document.getElementById('t10-btn-run-tfidf');
    if (runBtn) {
      runBtn.addEventListener('click', () => {
        if (window.SubtabController) window.SubtabController.invalidateAll('t10-subtabs');
        this.loadTfidfKeywords();
      });
    }

    const bundleBtn = document.getElementById('t10-btn-download-bundle');
    if (bundleBtn) {
      bundleBtn.addEventListener('click', () => this.downloadResearchBundle());
    }

    if (window.appState) {
      const onRefresh = () => {
        this.loadTfidfKeywords();
      };
      window.appState.on('scopeChanged', onRefresh);
      window.appState.on('viewParamsChanged', onRefresh);
    }
  }

  async loadTfidfKeywords() {
    const topK = parseInt(document.getElementById('t10-input-topk')?.value || '15');
    const excludePropn = document.getElementById('t10-check-exclude-propn')?.checked ?? true;

    const payload = {
      top_k: topK,
      exclude_pos: excludePropn ? ['PROPN'] : [],
      sublinear_tf: true,
      smooth_idf: true,
      view_params: window.appState ? window.appState.state.view_params : {},
      scope: window.appState ? window.appState.state.scope : { scope: 'all_tr' }
    };

    try {
      const resp = await fetch('/api/v1/lexicon/tfidf/keywords', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (resp.ok) {
        const data = await resp.json();
        this.renderKeywordsGrid(data.texts_keywords || {});
      }
    } catch (err) {
      console.error('Failed to load TF-IDF keywords:', err);
    }
  }

  renderKeywordsGrid(textsKeywords) {
    const container = document.getElementById('t10-keywords-container');
    if (!container) return;

    let html = '<div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(240px, 1fr)); gap:12px;">';
    for (const [textCode, keywords] of Object.entries(textsKeywords)) {
      html += `
        <div class="kpi-card" style="padding:10px 12px;">
          <div style="font-weight:700; color:var(--accent-blue); margin-bottom:6px; font-size:12.5px;">${textCode}</div>
          <div style="display:flex; flex-direction:column; gap:3px;">
            ${keywords.slice(0, 10).map((k, i) => `
              <div style="display:flex; justify-content:space-between; font-size:11.5px; border-bottom:1px solid #334155; padding:2px 0;">
                <span>${i + 1}. <b>${k.term}</b></span>
                <span style="color:var(--accent-teal); font-family:var(--font-mono);">${k.tfidf.toFixed(3)}</span>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    }
    html += '</div>';
    container.innerHTML = html;
  }

  async downloadResearchBundle() {
    const bundlePayload = {
      bundle: {
        bundle_name: 'turkish_sf_research_bundle',
        export_formats: ['md', 'tsv', 'xlsx'],
        include_figures: true,
        include_tables: true
      },
      tables: {}
    };

    try {
      const resp = await fetch('/api/v1/export/bundle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(bundlePayload)
      });
      if (resp.ok) {
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'turkish_sf_research_bundle.zip';
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (err) {
      console.error('Failed to download research bundle:', err);
    }
  }
}

window.tab10 = new Tab10Controller();
