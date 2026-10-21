/**
 * Tab 1 Controller: Corpus Inventory, Source Tables & Schema Inspector.
 */
class Tab01Controller {
  constructor() {
    this.grid = null;
    this.schemaGrid = null;
  }

  async init() {
    await this.loadSummary();
    await this.loadSourceTables();
    this.attachEvents();
  }

  async loadSummary() {
    try {
      const resp = await fetch('/api/v1/corpus/inventory');
      if (resp.ok) {
        const stats = await resp.json();
        document.getElementById('t1-total-texts').innerText = stats.total_texts;
        document.getElementById('t1-total-tokens').innerText = stats.total_tokens.toLocaleString();
        document.getElementById('t1-total-sentences').innerText = stats.total_sentences.toLocaleString();
        document.getElementById('t1-author-count').innerText = stats.author_count;
        document.getElementById('t1-rss-mb').innerText = `${stats.rss_mb} MB`;
      }
    } catch (err) {
      console.error('Failed to load summary stats:', err);
    }
  }

  async loadSourceTables() {
    try {
      const resp = await fetch('/api/v1/corpus/source-tables');
      if (resp.ok) {
        const data = await resp.json();
        const allRows = [
          ...(data.trans_en || []),
          ...(data.trans_tr || []),
          ...(data.indig_tr || [])
        ];

        this.grid = new TableGrid('t1-inventory-grid', {
          columns: [
            { key: 'code', label: 'Code', render: (_, r) => r.code || r.text_code || '' },
            { key: 'title', label: 'Title' },
            { key: 'author_translator', label: 'Author / Trans.', render: (_, r) => r.author_translator || r.author || '' },
            { key: 'language', label: 'Lang', render: (_, r) => r.language || r.lang || '' },
            { key: 'tokens', label: 'Tokens', render: (v) => v ? Number(v).toLocaleString() : '0' },
            { key: 'sentences', label: 'Sentences', render: (v) => v ? Number(v).toLocaleString() : '0' },
            {
              key: 'actions',
              label: 'Details',
              render: (_, row) => `
                <button class="btn btn-sm btn-inspect-schema" data-code="${row.code || row.text_code}">Schema</button>
                <button class="btn btn-sm btn-view-dossier" data-code="${row.code || row.text_code}">Dossier</button>
              `
            }
          ],
          data: allRows,
          pageSize: 15
        });
        this.grid.render();

      }
    } catch (err) {
      console.error('Failed to load source tables:', err);
    }
  }

  attachEvents() {
    const container = document.getElementById('t1-inventory-grid');
    if (!container) return;

    container.addEventListener('click', async (e) => {
      const inspectBtn = e.target.closest('.btn-inspect-schema');
      if (inspectBtn) {
        const code = inspectBtn.getAttribute('data-code');
        await this.inspectSchema(code);
      }
      const dossierBtn = e.target.closest('.btn-view-dossier');
      if (dossierBtn) {
        const code = dossierBtn.getAttribute('data-code');
        if (window.corpusInfoModal) window.corpusInfoModal.open(code);
      }
    });
  }

  async inspectSchema(textCode) {
    try {
      const resp = await fetch(`/api/v1/corpus/schema/${textCode}`);
      if (resp.ok) {
        const schema = await resp.json();
        document.getElementById('t1-schema-pane').style.display = 'block';
        document.getElementById('t1-schema-text-code').innerText = schema.text_code;
        document.getElementById('t1-schema-tok-count').innerText = `${schema.token_rows} tokens`;

        this.schemaGrid = new TableGrid('t1-schema-columns-grid', {
          columns: [
            { key: 'column', label: 'Column' },
            { key: 'dtype', label: 'Data Type' },
            { key: 'non_null', label: 'Non-Null Values' }
          ],
          data: schema.token_schema,
          pageSize: 10
        });
        this.schemaGrid.render();
      }
    } catch (err) {
      console.error('Failed to inspect schema:', err);
    }
  }
}

window.tab01 = new Tab01Controller();
