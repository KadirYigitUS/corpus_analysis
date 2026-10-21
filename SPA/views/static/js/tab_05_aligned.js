/**
 * tab_05_aligned.js - Bilingual aligned dependency trees view (dv.alignment_html).
 */
(function(window) {
  'use strict';

  function initTab05Aligned() {
    const subtabs = new window.SubtabController('t5-subtabs');

    const renderAlignedBtn = document.getElementById('t5-btn-render-aligned');
    if (renderAlignedBtn) {
      renderAlignedBtn.onclick = async () => {
        const pair = document.getElementById('t5-select-pair')?.value || 'IR-IA_BR-SM';
        const ai = parseInt(document.getElementById('t5-input-ai')?.value || '4');
        const norm = document.getElementById('t5-check-norm')?.checked ?? true;
        const dim = document.getElementById('t5-check-dim')?.checked ?? true;
        const stage = document.getElementById('t5-aligned-tree-stage');

        if (stage) {
          stage.innerHTML = '<div style="color:var(--text-muted);">Loading aligned dependency trees...</div>';
          try {
            const data = await window.VizAPI.getJSON(`/api/v1/syntax/dep/aligned/${pair}/${ai}?normalize_labels=${norm}&dim_function_words=${dim}`);
            stage.innerHTML = data.svg || data.html || '<div style="color:#ef4444;">No aligned trees returned for this group.</div>';
          } catch (err) {
            stage.innerHTML = `<div style="color:#ef4444;">Failed to load aligned trees: ${err.message}</div>`;
          }
        }
      };
    }
  }

  window.initTab05Aligned = initTab05Aligned;
})(window);
