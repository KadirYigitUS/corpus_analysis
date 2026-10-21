/**
 * Controller for Settings & Path Configurator Modal.
 */
class ConfigEditorModalController {
  constructor() {
    this.modalEl = document.getElementById('config-editor-modal');
    this.fieldsContainer = document.getElementById('paths-editor-fields');
  }

  init() {
    const openBtn = document.getElementById('btn-open-settings');
    const closeBtn = document.getElementById('btn-close-settings');
    const saveBtn = document.getElementById('btn-save-settings');

    if (openBtn) openBtn.addEventListener('click', () => this.open());
    if (closeBtn) closeBtn.addEventListener('click', () => this.close());
    if (saveBtn) saveBtn.addEventListener('click', () => this.save());
  }

  async open() {
    if (!this.modalEl) return;
    this.modalEl.classList.add('active');
    await this.loadPaths();
  }

  close() {
    if (this.modalEl) this.modalEl.classList.remove('active');
  }

  async loadPaths() {
    if (!this.fieldsContainer) return;
    try {
      const resp = await fetch('/api/v1/config/paths');
      if (resp.ok) {
        const data = await resp.json();
        this.renderFields(data.paths || {});
      }
    } catch (err) {
      console.error('Failed to load paths:', err);
    }
  }

  renderFields(paths) {
    this.fieldsContainer.innerHTML = Object.entries(paths).map(([key, val]) => `
      <div style="margin-bottom:10px;">
        <label style="display:block; font-size:11.5px; font-weight:600; color:var(--text-secondary); text-transform:uppercase;">${key.replace(/_/g, ' ')}</label>
        <input type="text" class="form-input path-input" data-key="${key}" value="${val}" style="width:100%; margin-top:3px;" />
      </div>
    `).join('');
  }

  async save() {
    const inputs = this.fieldsContainer.querySelectorAll('.path-input');
    const updatedPaths = {};
    inputs.forEach(inp => {
      const k = inp.getAttribute('data-key');
      updatedPaths[k] = inp.value.trim();
    });

    try {
      const resp = await fetch('/api/v1/config/paths', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ paths: updatedPaths })
      });
      if (resp.ok) {
        const res = await resp.json();
        alert('Paths configuration successfully updated and validated!');
        this.close();
      }
    } catch (err) {
      console.error('Failed to save paths:', err);
      alert('Error updating paths');
    }
  }
}

window.configEditorModal = new ConfigEditorModalController();
