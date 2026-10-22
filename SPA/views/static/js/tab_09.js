/**
 * Tab 9 Controller: Union-Slot Collocation & GraphColl Studio.
 */
class Tab09Controller {
  constructor() {
    this.grid = null;
    this.hasRun = false;
  }

  init() {
    this.attachEvents();
    if (typeof window.initTab09Viz === 'function') window.initTab09Viz();
  }

  attachEvents() {
    const runBtn = document.getElementById('t9-btn-run-colloc');
    if (runBtn) {
      runBtn.addEventListener('click', () => {
        if (window.SubtabController) window.SubtabController.invalidateAll('t9-subtabs');
        this.runCollocations();
      });
    }
    const textSel = document.getElementById('t9-select-text');
    if (textSel) {
      textSel.addEventListener('change', () => {
        if (window.SubtabController) window.SubtabController.invalidateAll('t9-subtabs');
        if (this.hasRun) this.runCollocations();
      });
    }
    if (window.appState) {
      window.appState.on('scopeChanged', (sc) => {
        if (sc && sc.text_code && textSel && textSel.value !== sc.text_code) {
          textSel.value = sc.text_code;
        }
        if (this.hasRun) this.runCollocations();
      });
      window.appState.on('viewParamsChanged', () => {
        if (this.hasRun) this.runCollocations();
      });
    }
  }

  async runCollocations() {
    this.hasRun = true;
    const node = document.getElementById('t9-input-node')?.value || 'robot';
    const textCode = document.getElementById('t9-select-text')?.value || 'BR-SM';
    const metric = document.getElementById('t9-select-metric')?.value || 'LogDice';
    const minFreq = parseInt(document.getElementById('t9-input-min-freq')?.value || '3');

    const payload = {
      node_query: node,
      text_code: textCode,
      left_span: 5,
      right_span: 5,
      min_freq: minFreq,
      stat_metric: metric,
      sentence_clamped: true,
      view_params: window.appState ? window.appState.state.view_params : {}
    };

    try {
      const resp = await fetch('/api/v1/lexicon/collocation/table', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (resp.ok) {
        const data = await resp.json();
        document.getElementById('t9-stats-header').innerHTML = `
          <span class="stat-badge-math">Node: <b>${data.node}</b> (f = ${data.f_node} hits)</span>
          <span class="stat-badge-math">Union Slots (R<sub>1</sub>): <b>${data.R1}</b></span>
          <span class="stat-badge-math">Corpus Tokens (N): <b>${data.N}</b></span>
          <span class="stat-badge-math">Metric: <b>${data.metric}</b></span>
        `;
        this.renderTable(data.items || []);
        this.renderGraphColl(data.graphcoll_nodes || []);
      }
    } catch (err) {
      console.error('Failed to run collocations:', err);
    }
  }

  renderTable(items) {
    this.grid = new TableGrid('t9-collocation-grid', {
      columns: [
        { key: 'collocate', label: 'Collocate' },
        { key: 'O11', label: 'O11 (In Window)' },
        { key: 'C1', label: 'C1 (Corpus Freq)' },
        { key: 'E11', label: 'E11 (Expected)', render: v => v ? v.toFixed(2) : '-' },
        { key: 'LogDice', label: 'LogDice', render: v => v ? v.toFixed(2) : '-' },
        { key: 'MI', label: 'MI', render: v => v ? v.toFixed(2) : '-' },
        { key: 'G2', label: 'Signed G2', render: v => v ? v.toFixed(2) : '-' },
        { key: 'T', label: 'T-Score', render: v => v ? v.toFixed(2) : '-' }
      ],
      data: items,
      pageSize: 15
    });
    this.grid.render();
  }

  renderGraphColl(nodes) {
    const stage = document.getElementById('t9-graphcoll-stage');
    if (!stage) return;
    const center = 180;

    let svgHtml = `
      <svg width="360" height="360" viewBox="0 0 360 360" style="background:#0f172a; border-radius:8px; border:1px solid #334155;">
        <circle cx="${center}" cy="${center}" r="70" fill="none" stroke="#334155" stroke-dasharray="3,3"/>
        <circle cx="${center}" cy="${center}" r="130" fill="none" stroke="#334155" stroke-dasharray="3,3"/>
    `;

    nodes.forEach(n => {
      const cx = center + (n.x || 0) * 0.55;
      const cy = center + (n.y || 0) * 0.55;
      if (n.is_center) {
        svgHtml += `
          <circle cx="${cx}" cy="${cy}" r="14" fill="#38bdf8" />
          <text x="${cx}" y="${cy + 4}" text-anchor="middle" fill="#0f172a" font-size="10" font-weight="bold">${n.label}</text>
        `;
      } else {
        svgHtml += `
          <line x1="${center}" y1="${center}" x2="${cx}" y2="${cy}" stroke="#334155" stroke-width="1" />
          <circle cx="${cx}" cy="${cy}" r="${Math.max(4, n.size * 0.7)}" fill="#2dd4bf" opacity="0.85" />
          <text x="${cx + 6}" y="${cy + 3}" fill="#f8fafc" font-size="9">${n.label}</text>
        `;
      }
    });

    svgHtml += '</svg>';
    stage.innerHTML = svgHtml;
  }
}

window.tab09 = new Tab09Controller();
