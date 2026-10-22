/**
 * Tab 2 Controller: Translation Alignment & Length-Delta Explorer.
 */
class Tab02Controller {
  constructor() {
    this.currentPair = 'IR-IA_BR-SM';
    this.activeChapter = null; this.activeNer = null;
    this.activeSort = 'ai'; this.ascending = true; this.searchQuery = '';
    this.currentPage = 1; this.pageSize = 25;
    this.totalRows = 0; this.totalPages = 1; this.rows = [];
    this.chartHelper = new Tab02ChartAndTokens('t2-sent-diff-canvas', 't2-chart-title', 't2-tok-tip');
  }

  async init() {
    if (typeof window.initTab02Structure === 'function') window.initTab02Structure();
    await Promise.all([this.loadKpis(), this.loadStatsAndChart(), this.loadChapters(), this.loadRows()]);
    this.attachEvents();
    this.chartHelper.attachTooltip('t2-alignment-grid');
  }

  async loadKpis() {
    try {
      const chParam = this.activeChapter !== null ? `?chapter_no=${this.activeChapter}` : '';
      const resp = await fetch(`/api/v1/alignment/kpis/${this.currentPair}${chParam}`);
      if (resp.ok) {
        const kpi = await resp.json();
        const setTxt = (id, val) => { const el = document.getElementById(id); if (el) el.innerText = val; };
        setTxt('t2-kpi-total', kpi.total_alignments ?? 0); setTxt('t2-kpi-ratio', kpi.sentence_ratio ?? '1.0');
        setTxt('t2-kpi-one-to-one', `${kpi.one_to_one_pct ?? 0}%`); setTxt('t2-kpi-expansion', kpi.expansion_ratio ?? '1.0');
        setTxt('t2-kpi-tur-more', kpi.count_tur_more ?? 0); setTxt('t2-kpi-eng-more', kpi.count_eng_more ?? 0);
        setTxt('t2-kpi-equal-sent', kpi.count_one_one ?? 0); setTxt('t2-kpi-max-min-diff', `${kpi.max_sent_diff ?? 0} / ${kpi.min_sent_diff ?? 0}`);
        setTxt('t2-kpi-avg-len-eng', kpi.avg_len_eng ?? 0); setTxt('t2-kpi-avg-len-tur', kpi.avg_len_tur ?? 0);
        setTxt('t2-kpi-avg-len-diff', kpi.avg_len_diff ?? 0);
      }
    } catch (err) { console.error('Failed to load alignment KPIs:', err); }
  }

  async loadStatsAndChart() {
    try {
      const chParam = this.activeChapter !== null ? `?chapter_no=${this.activeChapter}` : '';
      const resp = await fetch(`/api/v1/alignment/stats/${this.currentPair}${chParam}`);
      if (resp.ok) {
        const data = await resp.json();
        this.chartHelper.drawChart(data.series || [], data.chapter_summary || [], data.scope || 'Whole Book');
      }
    } catch (err) { console.error('Failed to load alignment stats chart:', err); }
  }

  async loadChapters() {
    try {
      const resp = await fetch(`/api/v1/alignment/chapters/${this.currentPair}`);
      if (resp.ok) {
        const data = await resp.json();
        const sidebar = document.getElementById('t2-chapter-sidebar');
        if (!sidebar) return;
        sidebar.innerHTML = [
          `<button class="btn btn-sm ch-btn ${this.activeChapter === null ? 'active' : ''}" data-ch="all">All Chapters</button>`,
          ...(data.chapters || []).map((c) => `<button class="btn btn-sm ch-btn ${this.activeChapter === c.chapter ? 'active' : ''}" data-ch="${c.chapter}">Ch. ${c.chapter} <span class="chip">${c.alignment_count}</span></button>`),
        ].join('');
      }
    } catch (err) { console.error('Failed to load alignment chapters:', err); }
  }

  async loadRows() {
    try {
      const payload = {
        pair_code: this.currentPair, chapter_no: this.activeChapter, ner_category: this.activeNer,
        search_query: this.searchQuery, sort_by: this.activeSort, ascending: this.ascending,
        page: this.currentPage, page_size: this.pageSize,
      };
      const resp = await fetch('/api/v1/alignment/rows', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
      });
      if (resp.ok) {
        const res = await resp.json();
        this.totalRows = res.total || 0;
        this.totalPages = res.total_pages || Math.max(1, Math.ceil(this.totalRows / this.pageSize));
        this.currentPage = res.page || 1; this.rows = res.rows || []; this.renderTable();
      }
    } catch (err) { console.error('Failed to load alignment rows:', err); }
  }

  renderTable() {
    const container = document.getElementById('t2-alignment-grid');
    if (!container) return;
    const cols = [
      { key: 'ai', label: 'AI' }, { key: 'ch', label: 'Ch' },
      { key: 'sent_eng', label: 'EN Sents' }, { key: 'sent_tur', label: 'TR Sents' },
      { key: 'sent_diff', label: 'sent_diff' }, { key: 'len_diff', label: 'len_diff' },
      { key: 'eng', label: 'English Source', sortable: false },
      { key: 'tur', label: 'Turkish Target', sortable: false }, { key: 'type', label: 'Type' },
    ];
    const startIdx = this.totalRows === 0 ? 0 : (this.currentPage - 1) * this.pageSize + 1;
    const endIdx = Math.min(this.currentPage * this.pageSize, this.totalRows);
    container.innerHTML = `
      <div class="datagrid-wrapper">
        <div class="datagrid-toolbar">
          <div style="font-size:12px; color:var(--text-secondary);">
            Showing <b>${startIdx}–${endIdx}</b> of <b>${this.totalRows}</b> records
            ${this.activeNer ? `<span class="chip chip-active" style="margin-left:6px;">NER: ${this.activeNer}</span>` : ''}
          </div>
          <input type="text" class="form-input grid-search-input" id="t2-grid-search" placeholder="Search EN/TR text or AI..." value="${this.searchQuery.replace(/"/g, '&quot;')}" style="width:220px;">
        </div>
        <div class="datagrid-scroll">
          <table class="datagrid-table">
            <thead><tr>${cols.map((c) => `<th data-key="${c.key}" class="${c.sortable === false ? '' : 'sortable-th'}">${c.label} ${this.activeSort === c.key ? (this.ascending ? '▲' : '▼') : ''}</th>`).join('')}</tr></thead>
            <tbody>
              ${this.rows.length === 0 ? `<tr><td colspan="${cols.length}" style="text-align:center; padding:18px; color:var(--text-muted);">No matching alignment rows.</td></tr>` : this.rows.map((r) => {
                const rowCls = r.sent_diff > 0 ? 't2-row-pos' : (r.sent_diff < 0 ? 't2-row-neg' : 't2-row-zero');
                const sdStr = `${r.sent_diff > 0 ? '+' : ''}${r.sent_diff}`;
                const ldStr = `${r.len_diff > 0 ? '+' : ''}${r.len_diff}`;
                return `<tr class="${rowCls}" data-ai="${r.ai}">
                  <td class="cell-num">${r.ai}</td><td class="cell-num">${r.ch}</td>
                  <td class="cell-num">${r.sent_eng}</td><td class="cell-num">${r.sent_tur}</td>
                  <td class="cell-num" style="font-weight:700;">${sdStr}</td><td class="cell-num">${ldStr}</td>
                  <td style="max-width:340px; white-space:normal;">${Tab02ChartAndTokens.renderCellHtml(r.ann_eng, r.eng)}</td>
                  <td style="max-width:340px; white-space:normal;">${Tab02ChartAndTokens.renderCellHtml(r.ann_tur, r.tur)}</td>
                  <td><span class="chip">${r.type}</span></td>
                </tr>`;
              }).join('')}
            </tbody>
          </table>
        </div>
        <div class="datagrid-pagination">
          <span>Page <b>${this.currentPage}</b> of <b>${this.totalPages}</b> (${this.totalRows} rows)</span>
          <div style="display:flex; gap:6px; align-items:center;">
            <button class="btn btn-sm grid-prev-btn" ${this.currentPage <= 1 ? 'disabled' : ''}>Prev</button>
            <button class="btn btn-sm grid-next-btn" ${this.currentPage >= this.totalPages ? 'disabled' : ''}>Next</button>
          </div>
        </div></div>`;
    this.bindGridControls(container);
  }

  bindGridControls(container) {
    const prevBtn = container.querySelector('.grid-prev-btn');
    const nextBtn = container.querySelector('.grid-next-btn');
    if (prevBtn) prevBtn.onclick = () => { if (this.currentPage > 1) { this.currentPage--; this.loadRows(); } };
    if (nextBtn) nextBtn.onclick = () => { if (this.currentPage < this.totalPages) { this.currentPage++; this.loadRows(); } };
    container.querySelectorAll('th.sortable-th').forEach((th) => {
      th.onclick = () => {
        const key = th.getAttribute('data-key');
        this.ascending = this.activeSort === key ? !this.ascending : true;
        this.activeSort = key; this.currentPage = 1; this.loadRows();
      };
    });
    const searchInput = container.querySelector('#t2-grid-search');
    if (searchInput) searchInput.onchange = (e) => { this.searchQuery = e.target.value; this.currentPage = 1; this.loadRows(); };
  }

  attachEvents() {
    const pairSelect = document.getElementById('t2-select-pair');
    if (pairSelect) {
      pairSelect.addEventListener('change', async (e) => {
        this.currentPair = e.target.value; this.activeChapter = null; this.currentPage = 1;
        if (window.SubtabController) window.SubtabController.invalidateAll('t2-subtabs');
        await Promise.all([this.loadStatsAndChart(), this.loadChapters(), this.loadRows()]);
        await this.loadKpis();
      });
    }
    if (window.appState) {
      window.appState.on('scopeChanged', async (sc) => {
        if (sc && sc.pair_code && sc.pair_code !== this.currentPair) {
          this.currentPair = sc.pair_code; if (pairSelect) pairSelect.value = this.currentPair;
          this.activeChapter = null; this.currentPage = 1;
          await Promise.all([this.loadStatsAndChart(), this.loadChapters(), this.loadRows(), this.loadKpis()]);
        }
        if (window.SubtabController) window.SubtabController.invalidateAll('t2-subtabs');
      });
    }
    const pageSizeSel = document.getElementById('t2-page-size');
    if (pageSizeSel) pageSizeSel.addEventListener('change', (e) => { this.pageSize = parseInt(e.target.value, 10) || 25; this.currentPage = 1; this.loadRows(); });
    const sidebar = document.getElementById('t2-chapter-sidebar');
    if (sidebar) {
      sidebar.addEventListener('click', (e) => {
        const btn = e.target.closest('.ch-btn');
        if (!btn) return;
        sidebar.querySelectorAll('.ch-btn').forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        const ch = btn.getAttribute('data-ch');
        this.activeChapter = ch === 'all' ? null : parseInt(ch, 10);
        this.currentPage = 1; this.loadKpis(); this.loadStatsAndChart(); this.loadRows();
      });
    }
    const nerBar = document.getElementById('t2-ner-filter-bar');
    if (nerBar) {
      nerBar.addEventListener('click', (e) => {
        const pill = e.target.closest('.ner-pill-btn');
        if (!pill) return;
        nerBar.querySelectorAll('.ner-pill-btn').forEach((p) => p.classList.remove('chip-active'));
        pill.classList.add('chip-active');
        const cat = pill.getAttribute('data-ner');
        this.activeNer = cat === 'ALL' ? null : cat;
        this.currentPage = 1; this.loadRows();
      });
    }
  }
}

window.tab02 = new Tab02Controller();
