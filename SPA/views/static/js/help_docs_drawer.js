/**
 * Controller for Help, Calculation Formulas & Methodological Sources Drawer.
 * Includes semantic HTML/MathML formula formatter and contextual '?' pane popover routing.
 */
function formatFormulaHtml(entry) {
  let raw = typeof entry === 'string' ? entry : (entry?.formula_html || entry?.formula || '');
  if (!raw) return '';
  // Convert any residual LaTeX macros into semantic HTML spans
  let out = String(raw)
    .replace(/\\text\{([^{}]*)\}/g, '<span class="math-var">$1</span>')
    .replace(/\\sqrt\{([^{}]*)\}/g, '<span class="math-sqrt">&radic;<span class="math-radicand">$1</span></span>')
    .replace(/\\frac\{([^{}]*)\}\{([^{}]*)\}/g, '<span class="math-frac"><span class="math-num">$1</span><span class="math-den">$2</span></span>')
    .replace(/_\{([^{}]*)\}/g, '<sub>$1</sub>')
    .replace(/\^\{([^{}]*)\}/g, '<sup>$1</sup>')
    .replace(/\\sum/g, '&sum;')
    .replace(/\\times/g, '&times;')
    .replace(/\\dots/g, '&hellip;')
    .replace(/\\ln/g, 'ln')
    .replace(/\\log_2/g, 'log<sub>2</sub>')
    .replace(/\\log_\{10\}/g, 'log<sub>10</sub>')
    .replace(/\\[a-zA-Z]+/g, '');
  return out;
}

class HelpDocsDrawerController {
  constructor() {
    this.drawerEl = document.getElementById('help-docs-drawer');
    this.overlayEl = document.getElementById('drawer-overlay');
    this.contentEl = document.getElementById('help-drawer-content');
    this.catalog = null;
    this.activeFilter = 'ALL';
  }

  init() {
    const openBtn = document.getElementById('btn-open-help');
    const closeBtn = document.getElementById('btn-close-help');

    if (openBtn) openBtn.addEventListener('click', () => this.open('ALL'));
    if (closeBtn) closeBtn.addEventListener('click', () => this.close());
    if (this.overlayEl) this.overlayEl.addEventListener('click', () => this.close());

    document.addEventListener('click', (e) => {
      const btn = e.target.closest('.btn-pane-help');
      if (btn) {
        e.preventDefault();
        const targetTab = btn.getAttribute('data-help-tab') || 'ALL';
        this.open(targetTab);
      }
    });
  }

  async open(filterTab = 'ALL') {
    if (!this.drawerEl) return;
    this.activeFilter = filterTab || 'ALL';
    this.drawerEl.classList.add('open');
    if (this.overlayEl) this.overlayEl.classList.add('active');
    await this.loadFormulas(this.activeFilter);
  }

  close() {
    if (this.drawerEl) this.drawerEl.classList.remove('open');
    if (this.overlayEl) this.overlayEl.classList.remove('active');
  }

  async loadFormulas(filterTab = 'ALL') {
    if (!this.contentEl) return;
    try {
      if (!this.catalog) {
        const resp = await fetch('/api/v1/help/formulas');
        if (resp.ok) {
          this.catalog = await resp.json();
        }
      }
      if (this.catalog) {
        this.renderHelp(this.catalog, filterTab);
      }
    } catch (err) {
      console.error('Failed to load help formulas:', err);
    }
  }

  renderHelp(categories, filterTab = 'ALL') {
    const normFilter = String(filterTab || 'ALL').trim().toLowerCase();
    const catKeys = Object.keys(categories);
    const matchCat = (catName, items) => {
      if (normFilter === 'all') return true;
      const prefix = catName.split(':')[0].trim().toLowerCase();
      if (catName.toLowerCase() === normFilter || prefix === normFilter) return true;
      return Array.isArray(items) && items.some(it => String(it.tab || '').trim().toLowerCase() === normFilter);
    };

    let html = `
      <div style="margin-bottom:12px; font-size:12px; color:var(--text-secondary); line-height:1.5;">
        <b>Operational Guidance:</b> All metrics are computed on active <code>TokenView</code> streams across the 8 corpus scopes.
      </div>
      <div style="display:flex; gap:8px; align-items:center; margin-bottom:14px;">
        <span style="font-size:11.5px; font-weight:600; color:var(--text-muted);">Filter Section:</span>
        <select id="help-tab-filter" class="form-select" style="flex:1;">
          <option value="ALL">All Tabs &amp; Global Matrix (${catKeys.length} Sections)</option>
          ${catKeys.map(k => `<option value="${k}" ${matchCat(k, categories[k]) && normFilter !== 'all' ? 'selected' : ''}>${k}</option>`).join('')}
        </select>
      </div>
    `;

    for (const [catName, items] of Object.entries(categories)) {
      if (!matchCat(catName, items)) continue;

      const secTab = (Array.isArray(items) && items[0]?.tab) ? items[0].tab : catName;
      html += `<h4 data-help-section="${secTab}" style="color:var(--accent-blue); text-transform:uppercase; font-size:12px; margin:14px 0 8px 0; border-bottom:1px solid var(--border-subtle); padding-bottom:4px;">${catName}</h4>`;
      for (const item of items) {
        const renderedFormula = formatFormulaHtml(item);
        html += `
          <div class="formula-card" data-help-tab="${item.tab || catName}">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
              <div class="formula-name" style="margin-bottom:0;">${item.name}</div>
              <span class="chip" style="font-size:10px;">${item.tab || catName}</span>
            </div>
            <div class="formula-math">${renderedFormula}</div>
            <div style="font-size:11.5px; color:var(--text-secondary); margin-bottom:6px;">${item.description}</div>
            <div class="formula-guard">Boundary Guard: ${item.nan_guard}</div>
            <div class="formula-citation">Primary Source: <b>${item.citation}</b></div>
          </div>
        `;
      }
    }

    this.contentEl.innerHTML = html;
    const sel = document.getElementById('help-tab-filter');
    if (sel) {
      sel.addEventListener('change', (e) => {
        this.activeFilter = e.target.value;
        this.renderHelp(categories, this.activeFilter);
      });
    }
  }
}

window.formatFormulaHtml = formatFormulaHtml;
window.helpDocsDrawer = new HelpDocsDrawerController();
