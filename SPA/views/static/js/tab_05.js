/**
 * Tab 5 Controller: Syntactic Dependency (displaCy UD) Studio.
 */
class Tab05Controller {
  constructor() {
    this.conllGrid = null;
  }

  async init() {
    this.attachEvents();
    if (typeof window.initTab05Aligned === 'function') window.initTab05Aligned();
    await this.renderTree();
  }

  attachEvents() {
    const renderBtn = document.getElementById('t5-btn-render-tree');
    if (renderBtn) {
      renderBtn.addEventListener('click', () => this.renderTree());
    }

    const downloadBtn = document.getElementById('t5-btn-download-svg');
    if (downloadBtn) {
      downloadBtn.addEventListener('click', () => this.downloadSvg());
    }

    if (window.appState) {
      window.appState.on('scopeChanged', (sc) => {
        if (sc && sc.text_code) {
          const inp = document.getElementById('t5-input-text');
          if (inp && inp.value !== sc.text_code) {
            inp.value = sc.text_code;
            this.renderTree();
          }
        }
      });
    }
  }

  async renderTree() {
    const textCode = document.getElementById('t5-input-text')?.value || 'BR-SM';
    const ch = parseInt(document.getElementById('t5-input-ch')?.value || '1');
    const p = parseInt(document.getElementById('t5-input-p')?.value || '1');
    const s = parseInt(document.getElementById('t5-input-s')?.value || '1');

    try {
      // 1. Fetch SVG tree
      const svgResp = await fetch('/api/v1/syntax/dep/tree-svg', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text_code: textCode,
          chapter_no: ch,
          paragraph_no: p,
          sentence_no: s,
          dim_function_words: true
        })
      });
      if (svgResp.ok) {
        const data = await svgResp.json();
        const stage = document.getElementById('t5-tree-stage');
        if (stage) stage.innerHTML = data.svg || '<div>No tree available</div>';
      }

      // 2. Fetch CoNLL Table
      const conllResp = await fetch('/api/v1/syntax/dep/conll', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text_code: textCode,
          chapter_no: ch,
          paragraph_no: p,
          sentence_no: s
        })
      });
      if (conllResp.ok) {
        const conllData = await conllResp.json();
        this.renderConllTable(conllData.tokens || []);
      }
    } catch (err) {
      console.error('Failed to render dependency tree:', err);
    }
  }

  renderConllTable(tokens) {
    this.conllGrid = new TableGrid('t5-conll-grid', {
      columns: [
        { key: 'idx', label: 'ID' },
        { key: 'word', label: 'Word' },
        { key: 'lemma', label: 'Lemma' },
        { key: 'upos', label: 'UPOS' },
        { key: 'head', label: 'Head ID' },
        { key: 'head_word', label: 'Head Word' },
        { key: 'deprel', label: 'DepRel' }
      ],
      data: tokens,
      pageSize: 15
    });
    this.conllGrid.render();
  }

  downloadSvg() {
    const stage = document.getElementById('t5-tree-stage');
    const svgEl = stage?.querySelector('svg');
    if (!svgEl) return;
    const svgData = new XMLSerializer().serializeToString(svgEl);
    const blob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `dep_tree_${Date.now()}.svg`;
    link.click();
    URL.revokeObjectURL(url);
  }
}

window.tab05 = new Tab05Controller();
