/**
 * tab_05_aligned.js - Bilingual aligned dependency trees view (dv.alignment_html).
 */
(function(window) {
  'use strict';

  function initTab05Aligned() {
    const subtabs = new window.SubtabController('t5-subtabs');

    async function loadAlignedTrees() {
      const pair = document.getElementById('t5-select-pair')?.value || 'IR-IA_BR-SM';
      const ai = parseInt(document.getElementById('t5-input-ai')?.value || '4', 10);
      const norm = document.getElementById('t5-check-norm')?.checked ?? true;
      const dim = document.getElementById('t5-check-dim')?.checked ?? true;
      const stage = document.getElementById('t5-aligned-tree-stage');

      if (!stage) return;
      stage.innerHTML = '<div style="color:var(--text-muted);">Loading aligned dependency trees...</div>';
      try {
        const data = await window.VizAPI.getJSON(`/api/v1/syntax/dep/aligned/${pair}/${ai}?normalize_labels=${norm}&dim_function_words=${dim}`);
        if (data.eng_svg || data.tur_svg) {
          stage.innerHTML = `
            <div class="aligned-trees-grid" style="display:flex; flex-direction:column; gap:14px;">
              <div class="aligned-tree-pane">
                <div style="font-size:12px; font-weight:700; color:#2563eb; margin-bottom:4px;">EN Source: ${data.eng_title || pair} (ai=${data.ai ?? ai})</div>
                <div style="overflow-x:auto;">${data.eng_svg || '<div style="color:#64748b;">No English sentence</div>'}</div>
              </div>
              <div class="aligned-tree-pane">
                <div style="font-size:12px; font-weight:700; color:#0d9488; margin-bottom:4px;">TR Target: ${data.tur_title || pair} (ai=${data.ai ?? ai})</div>
                <div style="overflow-x:auto;">${data.tur_svg || '<div style="color:#64748b;">No Turkish sentence</div>'}</div>
              </div>
            </div>`;
        } else {
          stage.innerHTML = data.svg || data.html || '<div style="color:#ef4444;">No aligned trees returned for this group.</div>';
        }
      } catch (err) {
        stage.innerHTML = `<div style="color:#ef4444;">Failed to load aligned trees: ${err.message}</div>`;
      }
    }

    subtabs.onFirstShow('t5-pane-aligned', () => loadAlignedTrees());

    const renderAlignedBtn = document.getElementById('t5-btn-render-aligned');
    if (renderAlignedBtn) {
      renderAlignedBtn.onclick = () => loadAlignedTrees();
    }
    ['t5-select-pair', 't5-check-norm', 't5-check-dim'].forEach((id) => {
      const el = document.getElementById(id);
      if (el) el.addEventListener('change', () => loadAlignedTrees());
    });
  }

  window.initTab05Aligned = initTab05Aligned;
})(window);
