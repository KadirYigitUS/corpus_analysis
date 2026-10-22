/**
 * Tab 11 Controller: Unified Corpus Explorer & Scriptable Console.
 */
class Tab11Controller {
  init() {
    this.attachEvents();
  }

  attachEvents() {
    const runBtn = document.getElementById('t11-btn-run-console');
    if (runBtn) {
      runBtn.addEventListener('click', () => this.runConsoleQuery());
    }

    const copyBtn = document.getElementById('t11-btn-copy-script');
    if (copyBtn) {
      copyBtn.addEventListener('click', () => this.copyPythonSnippet());
    }

    const evictBtn = document.getElementById('t11-btn-evict-all');
    if (evictBtn) {
      evictBtn.addEventListener('click', () => this.evictAllRam());
    }

    if (window.appState) {
      window.appState.on('scopeChanged', () => this.updateSnippetPreview());
      window.appState.on('viewParamsChanged', () => this.updateSnippetPreview());
    }
  }

  updateSnippetPreview() {
    const scriptBox = document.getElementById('t11-python-snippet');
    if (!scriptBox || !window.appState) return;
    const term = document.getElementById('t11-input-term')?.value || 'bilim-kurgu';
    const sc = window.appState.state.scope || { scope: 'all' };
    const vp = window.appState.state.view_params || { field: 'tok', filter_function_words: false, mode: 'drop', punct: 'drop' };
    const catMap = {
      all: 'All texts',
      all_en: 'All English texts',
      trans_en: 'All English texts',
      all_tr: 'All Turkish texts',
      indig_tr: 'Indigenous Turkish novels',
      author_related: 'Author-translator related texts',
      author_turkish: 'Author-translator Turkish texts'
    };
    const catLabel = catMap[sc.scope] || 'All texts';
    const authArg = sc.author_filter ? `, author='${sc.author_filter}'` : '';
    scriptBox.value =
      `from corpus_toolkit.loader import CorpusLoader\n` +
      `from corpus_toolkit.explorer import quick_search\n\n` +
      `loader = CorpusLoader()\n` +
      `res = quick_search(\n` +
      `    loader, '${term}', category='${catLabel}'${authArg},\n` +
      `    field='${vp.field}', filter_function_words=${vp.filter_function_words ? 'True' : 'False'},\n` +
      `    mode='${vp.mode}', punct='${vp.punct}'\n` +
      `)\n` +
      `print(res)\n`;
  }

  async evictAllRam() {
    try {
      const resp = await fetch('/api/v1/corpus/evict-all', { method: 'POST' });
      if (resp.ok) {
        const data = await resp.json();
        const badge = document.getElementById('t11-ram-badge');
        if (badge) badge.innerText = `RAM: ${Math.round(data.rss_mb)} MB (Evicted ${data.evicted_count})`;
      }
    } catch (e) {
      console.error('Evict failed:', e);
    }
  }

  async runConsoleQuery() {
    const term = document.getElementById('t11-input-term')?.value || 'bilim-kurgu';
    const payload = {
      term: term,
      scope: window.appState ? window.appState.state.scope : { scope: 'all' },
      view_params: window.appState ? window.appState.state.view_params : {},
      max_concordance: 5
    };

    try {
      const resp = await fetch('/api/v1/export/quick-search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (resp.ok) {
        const data = await resp.json();
        document.getElementById('t11-hits-badge').innerText = `${data.total_hits} hits`;
        document.getElementById('t11-presence-text').innerText = (data.presence || []).join(', ') || 'None';

        const samplesContainer = document.getElementById('t11-samples-container');
        if (samplesContainer) {
          samplesContainer.innerHTML = (data.samples || []).map(s => `
            <div style="font-size:11.5px; padding:4px 0; border-bottom:1px solid #334155;">
              <span class="chip" style="margin-right:6px;">${s.text}</span>
              <span style="color:var(--text-muted); font-size:10.5px;">${s.coords}</span>
              <div style="color:var(--text-primary); margin-top:2px;">${s.line}</div>
            </div>
          `).join('');
        }

        const scriptBox = document.getElementById('t11-python-snippet');
        if (scriptBox) {
          scriptBox.value = data.python_snippet || '';
        }
      }
    } catch (err) {
      console.error('Failed to execute console quick search:', err);
    }
  }

  copyPythonSnippet() {
    const scriptBox = document.getElementById('t11-python-snippet');
    if (!scriptBox) return;
    scriptBox.select();
    navigator.clipboard.writeText(scriptBox.value);
    alert('Python script snippet copied to clipboard!');
  }
}

window.tab11 = new Tab11Controller();
