/**
 * Tab 2 Controller: Translation Alignment & Length-Delta Explorer.
 */
class Tab02Controller {
  constructor() {
    this.currentPair = 'IR-IA_BR-SM';
    this.activeChapter = null;
    this.activeNer = null;
    this.activeSort = 'ai';
    this.grid = null;
  }

  async init() {
    await this.loadKpis();
    await this.loadChapters();
    await this.loadRows();
    this.attachEvents();
  }

  async loadKpis() {
    try {
      const resp = await fetch(`/api/v1/alignment/kpis/${this.currentPair}`);
      if (resp.ok) {
        const kpi = await resp.json();
        document.getElementById('t2-kpi-total').innerText = kpi.total_alignments || 0;
        document.getElementById('t2-kpi-ratio').innerText = kpi.sentence_ratio || '1.0';
        document.getElementById('t2-kpi-one-to-one').innerText = `${kpi.one_to_one_pct || 0}%`;
        document.getElementById('t2-kpi-expansion').innerText = kpi.expansion_ratio || '1.0';
      }
    } catch (err) {
      console.error('Failed to load alignment KPIs:', err);
    }
  }

  async loadChapters() {
    try {
      const resp = await fetch(`/api/v1/alignment/chapters/${this.currentPair}`);
      if (resp.ok) {
        const data = await resp.json();
        const sidebar = document.getElementById('t2-chapter-sidebar');
        if (!sidebar) return;
        sidebar.innerHTML = `
          <button class="btn btn-sm ch-btn active" data-ch="all">All Chapters</button>
          ${data.chapters.map(c => `
            <button class="btn btn-sm ch-btn" data-ch="${c.chapter}">
              Ch. ${c.chapter} <span class="chip">${c.alignment_count}</span>
            </button>
          `).join('')}
        `;
      }
    } catch (err) {
      console.error('Failed to load alignment chapters:', err);
    }
  }

  async loadRows() {
    try {
      const payload = {
        pair_code: this.currentPair,
        chapter_no: this.activeChapter,
        ner_category: this.activeNer,
        sort_by: this.activeSort,
        page: 1,
        page_size: 25
      };
      const resp = await fetch('/api/v1/alignment/rows', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (resp.ok) {
        const result = await resp.json();
        this.renderTable(result.rows || []);
      }
    } catch (err) {
      console.error('Failed to load alignment rows:', err);
    }
  }

  renderTable(rows) {
    this.grid = new TableGrid('t2-alignment-grid', {
      columns: [
        { key: 'ai', label: 'AI' },
        { key: 'ch', label: 'Ch' },
        {
          key: 'eng',
          label: 'English Source',
          render: (val) => `<div style="max-width:320px; white-space:normal;">${val}</div>`
        },
        {
          key: 'tur',
          label: 'Turkish Target',
          render: (val) => `<div style="max-width:320px; white-space:normal;">${val}</div>`
        },
        { key: 'delta_w', label: 'Δ Words' },
        { key: 'delta_c', label: 'Δ Chars' },
        { key: 'type', label: 'Type' }
      ],
      data: rows,
      pageSize: 15
    });
    this.grid.render();
  }

  attachEvents() {
    const sidebar = document.getElementById('t2-chapter-sidebar');
    if (sidebar) {
      sidebar.addEventListener('click', (e) => {
        const btn = e.target.closest('.ch-btn');
        if (btn) {
          sidebar.querySelectorAll('.ch-btn').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          const ch = btn.getAttribute('data-ch');
          this.activeChapter = ch === 'all' ? null : parseInt(ch);
          this.loadRows();
        }
      });
    }

    const nerBar = document.getElementById('t2-ner-filter-bar');
    if (nerBar) {
      nerBar.addEventListener('click', (e) => {
        const pill = e.target.closest('.ner-pill-btn');
        if (pill) {
          nerBar.querySelectorAll('.ner-pill-btn').forEach(p => p.classList.remove('chip-active'));
          pill.classList.add('chip-active');
          const cat = pill.getAttribute('data-ner');
          this.activeNer = cat === 'ALL' ? null : cat;
          this.loadRows();
        }
      });
    }
  }
}

window.tab02 = new Tab02Controller();
