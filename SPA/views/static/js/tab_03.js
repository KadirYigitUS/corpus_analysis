/**
 * Tab 3 Controller: NDA Parallel Corpora & Tripartite Dictionary.
 */
class Tab03Controller {
  constructor() {
    this.currentPair = 'IR-IA_BR-SM';
    this.mode = 'linked';
    this.page = 1;
    this.totalPages = 1;
    this.maxRows = 15;
    this.customAis = '';
    this.hits = '';
    this.connector = new SvgConnectorEngine('t3-nda-stage');
  }

  async init() {
    await this.loadParallelView();
    await this.loadDictionaryDrawer();
    this.attachEvents();
    this.connector.attachResizeWatcher();
  }

  async loadParallelView() {
    const stage = document.getElementById('t3-nda-stage');
    if (!stage) return;
    try {
      const params = new URLSearchParams({
        max_rows: String(this.maxRows),
        mode: this.mode,
        page: String(this.page),
      });
      if (this.customAis.trim()) params.set('ais', this.customAis.trim());
      if (this.hits.trim()) params.set('hits', this.hits.trim());
      const resp = await fetch(`/api/v1/alignment/nda/html/${this.currentPair}?${params.toString()}`);
      if (resp.ok) {
        const data = await resp.json();
        this.page = data.page || 1;
        this.totalPages = data.total_pages || 1;
        stage.innerHTML = data.html;
        const pageInfo = document.getElementById('t3-page-info');
        if (pageInfo) {
          pageInfo.innerText = `Page ${this.page} / ${this.totalPages}`;
        }
        const prevBtn = document.getElementById('t3-prev-page');
        const nextBtn = document.getElementById('t3-next-page');
        if (prevBtn) prevBtn.disabled = this.page <= 1;
        if (nextBtn) nextBtn.disabled = this.page >= this.totalPages;
        setTimeout(() => this.connector.drawLinks(), 50);
      }
    } catch (err) {
      console.error('Failed to load parallel NDA view:', err);
    }
  }

  async loadDictionaryDrawer() {
    try {
      const resp = await fetch(`/api/v1/alignment/nda/dictionary/${this.currentPair}`);
      if (resp.ok) {
        const dict = await resp.json();
        this.renderDictionaryLists(dict.entries || {});
      }
    } catch (err) {
      console.error('Failed to load NDA dictionary:', err);
    }
  }

  renderDictionaryLists(entries) {
    const linkedList = document.getElementById('t3-dict-linked-list');
    const enList = document.getElementById('t3-dict-en-list');
    const trList = document.getElementById('t3-dict-tr-list');

    if (linkedList) {
      linkedList.innerHTML = (entries.linked || []).slice(0, 50).map((e) => `
        <div class="kpi-card" style="padding:6px 10px; margin-bottom:6px; font-size:11.5px;">
          <b style="color:var(--accent-blue);">${e.eng}</b> ⇄ <b style="color:var(--accent-teal);">${e.tur}</b>
          ${(e.tags || []).map((t) => `<span class="chip" style="margin-left:4px;">${t}</span>`).join('')}
        </div>
      `).join('');
    }

    if (enList) {
      enList.innerHTML = (entries.single_eng || []).slice(0, 50).map((e) => `
        <div class="kpi-card" style="padding:6px 10px; margin-bottom:6px; font-size:11.5px;">
          <b style="color:var(--accent-teal);">${e.eng}</b>
          ${(e.tags || []).map((t) => `<span class="chip" style="margin-left:4px;">${t}</span>`).join('')}
        </div>
      `).join('');
    }

    if (trList) {
      trList.innerHTML = (entries.single_tur || []).slice(0, 50).map((e) => `
        <div class="kpi-card" style="padding:6px 10px; margin-bottom:6px; font-size:11.5px;">
          <b style="color:var(--accent-rose);">${e.tur}</b>
          ${(e.tags || []).map((t) => `<span class="chip" style="margin-left:4px;">${t}</span>`).join('')}
        </div>
      `).join('');
    }
  }

  attachEvents() {
    const pairSelect = document.getElementById('t3-select-pair');
    if (pairSelect) {
      pairSelect.addEventListener('change', async (e) => {
        this.currentPair = e.target.value;
        this.page = 1;
        await this.loadParallelView();
        await this.loadDictionaryDrawer();
      });
    }

    const modeSelect = document.getElementById('t3-select-mode');
    if (modeSelect) {
      modeSelect.addEventListener('change', (e) => {
        this.mode = e.target.value;
        this.page = 1;
        this.loadParallelView();
      });
    }

    const applyBtn = document.getElementById('t3-btn-apply');
    if (applyBtn) {
      applyBtn.addEventListener('click', () => {
        const aisInput = document.getElementById('t3-input-ais');
        const hitsInput = document.getElementById('t3-input-hits');
        this.customAis = aisInput ? aisInput.value : '';
        this.hits = hitsInput ? hitsInput.value : '';
        this.page = 1;
        this.loadParallelView();
      });
    }

    const prevBtn = document.getElementById('t3-prev-page');
    const nextBtn = document.getElementById('t3-next-page');
    if (prevBtn) {
      prevBtn.addEventListener('click', () => {
        if (this.page > 1) {
          this.page--;
          this.loadParallelView();
        }
      });
    }
    if (nextBtn) {
      nextBtn.addEventListener('click', () => {
        if (this.page < this.totalPages) {
          this.page++;
          this.loadParallelView();
        }
      });
    }

    const toggleDictBtn = document.getElementById('btn-toggle-nda-dict');
    const dictDrawer = document.getElementById('t3-dict-drawer');
    if (toggleDictBtn && dictDrawer) {
      toggleDictBtn.addEventListener('click', () => {
        dictDrawer.classList.toggle('open');
      });
    }

    const redrawBtn = document.getElementById('btn-redraw-svg-links');
    if (redrawBtn) {
      redrawBtn.addEventListener('click', () => {
        this.connector.drawLinks();
      });
    }

    if (window.appState) {
      window.appState.on('scopeChanged', async (sc) => {
        const pairMap = { SM: 'IR-IA_BR-SM', ZB: 'TL-PA_A-ZB', OK: 'ASD-PKD_KT-OK', 'IR-IA': 'IR-IA_BR-SM', 'BR-SM': 'IR-IA_BR-SM', 'TL-PA': 'TL-PA_A-ZB', 'A-ZB': 'TL-PA_A-ZB', 'TLP-ML': 'TLP-ML_YG-ZB', 'YG-ZB': 'TLP-ML_YG-ZB', 'TSP-JL': 'TSP-JL_KS-ZB', 'KS-ZB': 'TSP-JL_KS-ZB', 'ASD-PKD': 'ASD-PKD_KT-OK', 'KT-OK': 'ASD-PKD_KT-OK' };
        const nextPair = (sc && sc.pair_code) || (sc && sc.text_code && pairMap[sc.text_code]) || (sc && sc.author_filter && pairMap[sc.author_filter]);
        if (nextPair && nextPair !== this.currentPair) {
          this.currentPair = nextPair;
          if (pairSelect) pairSelect.value = nextPair;
          this.page = 1;
          await this.loadParallelView();
          await this.loadDictionaryDrawer();
        }
      });
    }
  }
}

window.tab03 = new Tab03Controller();
