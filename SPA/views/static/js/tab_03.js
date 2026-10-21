/**
 * Tab 3 Controller: NDA Parallel Corpora & Tripartite Dictionary.
 */
class Tab03Controller {
  constructor() {
    this.currentPair = 'IR-IA_BR-SM';
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
      const resp = await fetch(`/api/v1/alignment/nda/html/${this.currentPair}?max_rows=15`);
      if (resp.ok) {
        const data = await resp.json();
        stage.innerHTML = data.html;
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
      linkedList.innerHTML = (entries.linked || []).slice(0, 50).map(e => `
        <div class="kpi-card" style="padding:6px 10px; margin-bottom:6px; font-size:11.5px;">
          <b style="color:var(--accent-blue);">${e.eng}</b> ⇄ <b style="color:var(--accent-teal);">${e.tur}</b>
          ${e.tags.map(t => `<span class="chip" style="margin-left:4px;">${t}</span>`).join('')}
        </div>
      `).join('');
    }

    if (enList) {
      enList.innerHTML = (entries.single_eng || []).slice(0, 50).map(e => `
        <div class="kpi-card" style="padding:6px 10px; margin-bottom:6px; font-size:11.5px;">
          <b style="color:var(--accent-teal);">${e.eng}</b>
          ${e.tags.map(t => `<span class="chip" style="margin-left:4px;">${t}</span>`).join('')}
        </div>
      `).join('');
    }

    if (trList) {
      trList.innerHTML = (entries.single_tur || []).slice(0, 50).map(e => `
        <div class="kpi-card" style="padding:6px 10px; margin-bottom:6px; font-size:11.5px;">
          <b style="color:var(--accent-rose);">${e.tur}</b>
          ${e.tags.map(t => `<span class="chip" style="margin-left:4px;">${t}</span>`).join('')}
        </div>
      `).join('');
    }
  }

  attachEvents() {
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
  }
}

window.tab03 = new Tab03Controller();
