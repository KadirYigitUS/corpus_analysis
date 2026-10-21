/**
 * Controller for Corpus Info & Sources Modal (Book Covers & Author Dossiers).
 */
class CorpusInfoModalController {
  constructor() {
    this.modalEl = document.getElementById('corpus-info-modal');
    this.booksListEl = document.getElementById('modal-books-list');
    this.authorsListEl = document.getElementById('modal-authors-list');
  }

  init() {
    const openBtn = document.getElementById('btn-open-corpus-info');
    const closeBtn = document.getElementById('btn-close-corpus-info');
    if (openBtn) openBtn.addEventListener('click', () => this.open());
    if (closeBtn) closeBtn.addEventListener('click', () => this.close());
  }

  async open(selectedCode = null) {
    if (!this.modalEl) return;
    this.modalEl.classList.add('active');
    await Promise.all([this.loadBooks(), this.loadAuthors()]);
    if (selectedCode) {
      const card = this.modalEl.querySelector(`[data-code="${selectedCode}"]`);
      if (card) card.scrollIntoView({ behavior: 'smooth' });
    }
  }

  close() {
    if (this.modalEl) this.modalEl.classList.remove('active');
  }

  async loadBooks() {
    if (!this.booksListEl) return;
    try {
      const resp = await fetch('/api/v1/config/books');
      if (resp.ok) {
        const data = await resp.json();
        this.renderBooks(data.books || []);
      }
    } catch (err) {
      console.error('Failed to load books for modal:', err);
    }
  }

  renderBooks(books) {
    this.booksListEl.innerHTML = books.map(b => `
      <div class="kpi-card" data-code="${b.code}" style="display:flex; gap:12px; align-items:center; margin-bottom:10px;">
        <img src="${b.cover_image || `/static/img/books/${b.code}.svg`}" alt="${b.title}" style="width:65px; height:90px; border-radius:4px; object-fit:cover; border:1px solid #334155;" onerror="this.src='/static/img/books/default.svg';" />
        <div style="flex:1;">
          <div style="font-weight:700; color:var(--text-primary); font-size:13px;">${b.title} <span class="chip">${b.code}</span></div>
          <div style="font-size:11.5px; color:var(--text-secondary); margin-top:2px;">Author: <b>${b.author}</b> ${b.translator ? `· Trans: <b>${b.translator}</b>` : ''} (${b.year})</div>
          <div style="font-size:11px; color:var(--text-muted); margin-top:2px;">Category: <i>${b.category}</i> ${b.pair_code ? `· Pair: <code>${b.pair_code}</code>` : ''}</div>
          <div style="margin-top:6px;">
            <label class="btn btn-sm" style="cursor:pointer;">
              Change Cover
              <input type="file" class="book-cover-upload" data-code="${b.code}" style="display:none;" accept="image/*" />
            </label>
          </div>
        </div>
      </div>
    `).join('');

    this.booksListEl.querySelectorAll('.book-cover-upload').forEach(inp => {
      inp.addEventListener('change', (e) => this.handleImageUpload(e, 'book'));
    });
  }

  async loadAuthors() {
    if (!this.authorsListEl) return;
    try {
      const resp = await fetch('/api/v1/config/authors');
      if (resp.ok) {
        const data = await resp.json();
        this.renderAuthors(data.authors || []);
      }
    } catch (err) {
      console.error('Failed to load authors for modal:', err);
    }
  }

  renderAuthors(authors) {
    this.authorsListEl.innerHTML = authors.map(a => `
      <div class="kpi-card" data-code="${a.code}" style="display:flex; gap:12px; align-items:center; margin-bottom:10px;">
        <img src="${a.portrait_image || `/static/img/authors/${a.code}.svg`}" alt="${a.name}" style="width:60px; height:60px; border-radius:50%; object-fit:cover; border:1px solid #2dd4bf;" onerror="this.src='/static/img/authors/default.svg';" />
        <div style="flex:1;">
          <div style="font-weight:700; color:var(--accent-teal); font-size:13px;">${a.name} <span class="chip">${a.code}</span></div>
          <div style="font-size:11.5px; color:var(--text-secondary);">${a.role} · ${a.era}</div>
          <div style="margin-top:6px;">
            <label class="btn btn-sm" style="cursor:pointer;">
              Change Portrait
              <input type="file" class="author-portrait-upload" data-code="${a.code}" style="display:none;" accept="image/*" />
            </label>
          </div>
        </div>
      </div>
    `).join('');

    this.authorsListEl.querySelectorAll('.author-portrait-upload').forEach(inp => {
      inp.addEventListener('change', (e) => this.handleImageUpload(e, 'author'));
    });
  }

  async handleImageUpload(event, category) {
    const file = event.target.files[0];
    if (!file) return;
    const code = event.target.getAttribute('data-code');
    const fd = new FormData();
    fd.append('file', file);
    fd.append('category', category);

    try {
      const resp = await fetch('/api/v1/config/upload-image', { method: 'POST', body: fd });
      if (resp.ok) {
        const res = await resp.json();
        if (category === 'book') await this.loadBooks();
        else await this.loadAuthors();
        alert(`Successfully uploaded ${category} image!`);
      }
    } catch (err) {
      console.error('Failed to upload image:', err);
    }
  }
}

window.corpusInfoModal = new CorpusInfoModalController();
