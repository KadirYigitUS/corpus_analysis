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
  const langBtn = document.getElementById('btn-lang-toggle');
  if (langBtn) {
    langBtn.addEventListener('click', () => {
      const cur = window.appState.state.lang || 'tr';
      const next = cur === 'tr' ? 'en' : 'tr';
      window.appState.state.lang = next;
      langBtn.innerText = next.toUpperCase() + ' / ' + (next === 'tr' ? 'EN' : 'TR');
      window.appState.emit('langChanged', { lang: next });
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

  document.getElementById('global-scope-select').addEventListener('change', (e) => {
    window.appState.setScope({ scope: e.target.value });
  });

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
