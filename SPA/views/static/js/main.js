/**
 * Main application bootstrap for Corpus Analysis SPA.
 */
document.addEventListener('DOMContentLoaded', async () => {
  // 0. Theme initialization
  const savedTheme = localStorage.getItem('spa-theme') ||
    (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');
  document.documentElement.setAttribute('data-theme', savedTheme);

  const themeBtn = document.getElementById('btn-toggle-theme');
  if (themeBtn) {
    themeBtn.addEventListener('click', () => {
      const cur = document.documentElement.getAttribute('data-theme') || 'dark';
      const next = cur === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('spa-theme', next);
    });
  }

  // 0b. Language toggle
  const applyI18n = (cat) => {
    if (!cat) return;
    if (cat.brand) document.getElementById('txt-brand-title').innerText = cat.brand;
    if (cat.tabs) {
      Object.entries(cat.tabs).forEach(([tid, label]) => {
        const b = document.querySelector(`#main-tab-nav .tab-btn[data-tab="${tid}"]`);
        if (b) b.innerText = label;
      });
    }
  };
  const langBtn = document.getElementById('btn-lang-toggle');
  if (langBtn) {
    langBtn.addEventListener('click', async () => {
      const cur = window.appState.state.lang || 'tr';
      const next = cur === 'tr' ? 'en' : 'tr';
      langBtn.innerText = next.toUpperCase() + ' / ' + (next === 'tr' ? 'EN' : 'TR');
      await window.appState.loadI18n(next);
      applyI18n(window.appState.i18nCatalog);
    });
  }

  // 1. Initialize Modals & Drawer
  window.corpusInfoModal.init();
  window.configEditorModal.init();
  window.helpDocsDrawer.init();

  // 2. Tab Switching Logic
  const tabNav = document.getElementById('main-tab-nav');
  tabNav.addEventListener('click', (e) => {
    const btn = e.target.closest('.tab-btn');
    if (!btn) return;
    const targetTab = btn.getAttribute('data-tab');

    tabNav.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

    btn.classList.add('active');
    const pane = document.getElementById(targetTab);
    if (pane) pane.classList.add('active');

    // Lazy initialize tab controller on first activation
    const tabNum = targetTab.replace('tab_', '');
    const controller = window['tab' + tabNum];
    if (controller && controller.init && !controller._initialized) {
      controller.init();
      controller._initialized = true;
    }
  });

  // 3. Matrix Bar & Scope Selectors Wiring
  const updateMatrix = () => {
    window.appState.setViewParams({
      field: document.getElementById('matrix-field').value,
      filter_function_words: document.getElementById('matrix-filter').value === 'true',
      mode: document.getElementById('matrix-mode').value,
      punct: document.getElementById('matrix-punct').value
    });
  };
  ['matrix-field', 'matrix-filter', 'matrix-mode', 'matrix-punct'].forEach(id => {
    document.getElementById(id).addEventListener('change', updateMatrix);
  });

  const scopeSel = document.getElementById('global-scope-select');
  const subSel = document.getElementById('global-scope-subselect');

  const AUTHOR_OPTIONS = [
    { val: 'SM', label: 'Selma MİNE [SM]' },
    { val: 'ZB', label: 'Zühtü BAYAR [ZB]' },
    { val: 'OK', label: 'Özlem KURDOĞLU [OK]' },
    { val: 'NCK', label: 'N. Can KANTARCI [NCK]' },
    { val: 'AS', label: 'Algan SEZGİNTÜREDİ [AS]' },
    { val: 'CE', label: 'Çiğdem ERKAL [CE]' },
    { val: 'SG', label: 'Sabri GÜRSES [SG]' }
  ];
  const TEXT_OPTIONS = [
    { val: 'IR-IA', label: 'IR-IA · I, Robot' },
    { val: 'BR-SM', label: 'BR-SM · Ben, Robot' },
    { val: 'OBI-SM', label: 'OBI-SM · OnaBirİsimVer' },
    { val: 'TL-PA', label: 'TL-PA · The Light' },
    { val: 'A-ZB', label: 'A-ZB · Aydınlık' },
    { val: 'TLP-ML', label: 'TLP-ML · The Lonely Planet' },
    { val: 'YG-ZB', label: 'YG-ZB · Yalnız Gezegen' },
    { val: 'TSP-JL', label: 'TSP-JL · The Scarlet Plague' },
    { val: 'KS-ZB', label: 'KS-ZB · Kızıl Veba' },
    { val: 'SU-ZB', label: 'SU-ZB · Sahte Uygarlık' },
    { val: 'ASD-PKD', label: 'ASD-PKD · A Scanner Darkly' },
    { val: 'KT-OK', label: 'KT-OK · Karanlığı Taramak' },
    { val: 'SCS-OK', label: 'SCS-OK · Son Çıkan Işığı Söndürsün' }
  ];

  const syncSubSelect = (scopeVal) => {
    if (!subSel) return;
    if (scopeVal === 'author_related' || scopeVal === 'author_turkish') {
      subSel.innerHTML = AUTHOR_OPTIONS.map(o => `<option value="${o.val}">${o.label}</option>`).join('');
      subSel.style.display = 'inline-block';
      const curAuth = window.appState.state.scope.author_filter || 'SM';
      subSel.value = AUTHOR_OPTIONS.some(o => o.val === curAuth) ? curAuth : 'SM';
      window.appState.setScope({ scope: scopeVal, author_filter: subSel.value, text_code: null });
    } else if (scopeVal === 'single') {
      subSel.innerHTML = TEXT_OPTIONS.map(o => `<option value="${o.val}">${o.label}</option>`).join('');
      subSel.style.display = 'inline-block';
      const curTxt = window.appState.state.scope.text_code || 'BR-SM';
      subSel.value = TEXT_OPTIONS.some(o => o.val === curTxt) ? curTxt : 'BR-SM';
      window.appState.setScope({ scope: scopeVal, author_filter: null, text_code: subSel.value });
    } else {
      subSel.style.display = 'none';
      subSel.innerHTML = '';
      window.appState.setScope({ scope: scopeVal, author_filter: null, text_code: null });
    }
  };

  if (scopeSel) {
    scopeSel.addEventListener('change', (e) => {
      syncSubSelect(e.target.value);
    });
  }
  if (subSel) {
    subSel.addEventListener('change', (e) => {
      const sc = scopeSel ? scopeSel.value : window.appState.state.scope.scope;
      if (sc === 'author_related' || sc === 'author_turkish') {
        window.appState.setScope({ scope: sc, author_filter: e.target.value });
      } else if (sc === 'single') {
        window.appState.setScope({ scope: sc, text_code: e.target.value });
      }
    });
  }

  // 4. Initial Tab 1 Activation & Telemetry Polling
  if (window.tab01) {
    await window.tab01.init();
    window.tab01._initialized = true;
  }
  await window.appState.refreshTelemetry();
  const gauge = document.getElementById('hdr-rss-gauge');
  if (gauge && window.appState.state.telemetry) {
    gauge.innerText = `RSS: ${window.appState.state.telemetry.rss_mb || 0} MB`;
  }
});
