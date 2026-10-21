/**
 * Controller for Help, Calculation Formulas & Methodological Sources Drawer.
 */
class HelpDocsDrawerController {
  constructor() {
    this.drawerEl = document.getElementById('help-docs-drawer');
    this.overlayEl = document.getElementById('drawer-overlay');
    this.contentEl = document.getElementById('help-drawer-content');
  }

  init() {
    const openBtn = document.getElementById('btn-open-help');
    const closeBtn = document.getElementById('btn-close-help');

    if (openBtn) openBtn.addEventListener('click', () => this.open());
    if (closeBtn) closeBtn.addEventListener('click', () => this.close());
    if (this.overlayEl) this.overlayEl.addEventListener('click', () => this.close());
  }

  async open() {
    if (!this.drawerEl) return;
    this.drawerEl.classList.add('open');
    if (this.overlayEl) this.overlayEl.classList.add('active');
    await this.loadFormulas();
  }

  close() {
    if (this.drawerEl) this.drawerEl.classList.remove('open');
    if (this.overlayEl) this.overlayEl.classList.remove('active');
  }

  async loadFormulas() {
    if (!this.contentEl) return;
    try {
      const resp = await fetch('/api/v1/help/formulas');
      if (resp.ok) {
        const formulas = await resp.json();
        this.renderHelp(formulas);
      }
    } catch (err) {
      console.error('Failed to load help formulas:', err);
    }
  }

  renderHelp(categories) {
    let html = `
      <div style="margin-bottom:14px; font-size:12px; color:var(--text-secondary); line-height:1.6;">
        <b>Operational Guidance:</b> All metrics are calculated strictly on content/non-punctuation tokens according to the active <code>TokenView</code> settings.
      </div>
    `;

    for (const [catName, items] of Object.entries(categories)) {
      html += `<h4 style="color:var(--accent-blue); text-transform:uppercase; font-size:12px; margin:14px 0 8px 0;">${catName} Formulas</h4>`;
      for (const item of items) {
        html += `
          <div class="formula-card">
            <div class="formula-name">${item.name}</div>
            <div class="formula-math">${item.formula}</div>
            <div style="font-size:11.5px; color:var(--text-secondary); margin-bottom:4px;">${item.description}</div>
            <div class="formula-guard">⚠️ Boundary Guard: ${item.nan_guard}</div>
            <div class="formula-citation">📖 Primary Citation: <b>${item.citation}</b></div>
          </div>
        `;
      }
    }

    this.contentEl.innerHTML = html;
  }
}

window.helpDocsDrawer = new HelpDocsDrawerController();
