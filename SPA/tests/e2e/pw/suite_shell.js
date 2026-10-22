/**
 * Suite 1: Global Shell, Theme, Language, Scope, Matrix Bar, RSS Telemetry, Modals & Help Drawer.
 */
const { assert, pollUntil, waitApi, gridTotalCount } = require('./helpers');

module.exports = async function suiteShell(ctx) {
  const { page } = ctx;

  return [
    {
      name: 'shell_brand_and_initial_load',
      fn: async () => {
        await Promise.all([
          page.waitForResponse((r) => r.url().includes('/api/v1/corpus/source-tables'), { timeout: 90000 }),
          page.waitForResponse((r) => r.url().includes('/api/v1/corpus/telemetry'), { timeout: 90000 }),
          page.goto('/', { waitUntil: 'domcontentloaded' }),
        ]);
        const brand = await page.$eval('#txt-brand-title', (el) => el.innerText.trim());
        assert.ok(brand.includes('Turkish SF Corpus Analysis'), `Unexpected brand title: ${brand}`);
        const total = await gridTotalCount(page, 't1-inventory-grid');
        assert.strictEqual(total, 13, `Expected 13 rows on initial 'all' scope, got ${total}`);
      },
    },
    {
      name: 'shell_theme_toggle_persists_across_reload',
      fn: async () => {
        const initialTheme = await page.$eval('html', (el) => el.getAttribute('data-theme'));
        assert.ok(['dark', 'light'].includes(initialTheme), `Invalid initial theme: ${initialTheme}`);
        await page.click('#btn-toggle-theme');
        const flippedTheme = await page.$eval('html', (el) => el.getAttribute('data-theme'));
        assert.notStrictEqual(flippedTheme, initialTheme, 'Theme did not flip on first click');

        if (flippedTheme === 'light') {
          const thBg = await page.$eval('.datagrid-table th', (el) => getComputedStyle(el).backgroundColor);
          assert.strictEqual(thBg, 'rgb(226, 232, 240)', `Expected light header bg rgb(226, 232, 240), got ${thBg}`);
        }

        await Promise.all([
          page.waitForResponse((r) => r.url().includes('/api/v1/corpus/source-tables'), { timeout: 90000 }),
          page.reload({ waitUntil: 'domcontentloaded' }),
        ]);
        const afterReload = await page.$eval('html', (el) => el.getAttribute('data-theme'));
        assert.strictEqual(afterReload, flippedTheme, 'Theme did not persist across reload');

        await page.click('#btn-toggle-theme');
        const restored = await page.$eval('html', (el) => el.getAttribute('data-theme'));
        assert.strictEqual(restored, initialTheme, 'Theme did not flip back on second click');
      },
    },
    {
      name: 'shell_language_toggle_loads_i18n_and_updates_labels',
      fn: async () => {
        const { status: enStatus, json: enJson } = await waitApi(page, '/static/i18n/en.json', async () => {
          await page.click('#btn-lang-toggle');
        });
        assert.strictEqual(enStatus, 200);
        assert.ok(enJson && enJson.brand, 'en.json missing brand key');
        const brandEn = await page.$eval('#txt-brand-title', (el) => el.innerText.trim());
        assert.strictEqual(brandEn, enJson.brand);

        const { status: trStatus, json: trJson } = await waitApi(page, '/static/i18n/tr.json', async () => {
          await page.click('#btn-lang-toggle');
        });
        assert.strictEqual(trStatus, 200);
        const brandTr = await page.$eval('#txt-brand-title', (el) => el.innerText.trim());
        assert.strictEqual(brandTr, trJson.brand);
      },
    },
    {
      name: 'shell_scope_and_matrix_selectors_update_state',
      fn: async () => {
        await waitApi(page, '/api/v1/corpus/source-tables?category=indig_tr', async () => {
          await page.selectOption('#global-scope-select', 'indig_tr');
        });
        await pollUntil(async () => (await gridTotalCount(page, 't1-inventory-grid')) === 3, {
          message: 'Expected 3 rows for indig_tr scope',
        });

        await waitApi(page, '/api/v1/corpus/source-tables', async () => {
          await page.selectOption('#global-scope-select', 'all');
        });
        await pollUntil(async () => (await gridTotalCount(page, 't1-inventory-grid')) === 13, {
          message: 'Expected 13 rows when restored to all scope',
        });

        await page.selectOption('#matrix-field', 'lem');
        await page.selectOption('#matrix-filter', 'true');
        await page.selectOption('#matrix-mode', 'mask');
        await page.selectOption('#matrix-punct', 'strip');

        const vp = await page.evaluate(() => window.appState.state.view_params);
        assert.strictEqual(vp.field, 'lem');
        assert.strictEqual(vp.filter_function_words, true);
        assert.strictEqual(vp.mode, 'mask');
        assert.strictEqual(vp.punct, 'strip');

        // Restore defaults for subsequent suites
        await page.selectOption('#matrix-field', 'tok');
        await page.selectOption('#matrix-filter', 'false');
        await page.selectOption('#matrix-mode', 'drop');
        await page.selectOption('#matrix-punct', 'drop');
      },
    },
    {
      name: 'shell_rss_gauge_within_bounds',
      fn: async () => {
        await pollUntil(async () => {
          const txt = await page.$eval('#hdr-rss-gauge', (el) => el.innerText.trim());
          return txt && !txt.includes('- MB');
        });
        const rssText = await page.$eval('#hdr-rss-gauge', (el) => el.innerText.trim());
        const m = rssText.match(/([\d.]+)\s*MB/);
        assert.ok(m, `RSS gauge not numeric: ${rssText}`);
        const rssMb = parseFloat(m[1]);
        assert.ok(rssMb > 0 && rssMb < 1500, `RSS ${rssMb} MB outside (0, 1500) bounds`);
      },
    },
    {
      name: 'shell_modals_and_help_drawer',
      fn: async () => {
        // 1. Corpus Info Modal
        await Promise.all([
          page.waitForResponse((r) => r.url().includes('/api/v1/config/books')),
          page.waitForResponse((r) => r.url().includes('/api/v1/config/authors')),
          page.click('#btn-open-corpus-info'),
        ]);
        const infoActive = await page.$eval('#corpus-info-modal', (el) => el.classList.contains('active'));
        assert.strictEqual(infoActive, true);
        const bookCount = await page.$$eval('#modal-books-list .kpi-card', (els) => els.length);
        const authorCount = await page.$$eval('#modal-authors-list .kpi-card', (els) => els.length);
        assert.ok(bookCount > 0, 'Expected books in Corpus Info modal');
        assert.ok(authorCount > 0, 'Expected authors in Corpus Info modal');
        await page.click('#btn-close-corpus-info');
        const infoClosed = await page.$eval('#corpus-info-modal', (el) => !el.classList.contains('active'));
        assert.strictEqual(infoClosed, true);

        // 2. Config Editor Modal (stubbed save so nothing is persisted to disk)
        await waitApi(page, '/api/v1/config/paths', async () => {
          await page.click('#btn-open-settings');
        });
        const cfgActive = await page.$eval('#config-editor-modal', (el) => el.classList.contains('active'));
        assert.strictEqual(cfgActive, true);
        const pathInputs = await page.$$eval('#paths-editor-fields .path-input', (els) => els.length);
        assert.ok(pathInputs > 0, 'Expected path input fields in Config Editor');

        let interceptedSave = false;
        await page.route('**/api/v1/config/paths', async (route) => {
          if (['POST', 'PUT'].includes(route.request().method())) {
            interceptedSave = true;
            await route.fulfill({
              status: 200,
              contentType: 'application/json',
              body: JSON.stringify({ saved: true, stubbed: true }),
            });
          } else {
            await route.continue();
          }
        });
        await page.click('#btn-save-settings');
        await pollUntil(async () => interceptedSave);
        await pollUntil(async () => page.$eval('#config-editor-modal', (el) => !el.classList.contains('active')));
        await page.unroute('**/api/v1/config/paths');

        // 3. Help Drawer + Overlay Close + Typographic MathML/HTML verification
        const { status: helpStatus } = await waitApi(page, '/api/v1/help/formulas', async () => {
          await page.click('#btn-open-help');
        });
        assert.strictEqual(helpStatus, 200);
        const drawerOpen = await page.$eval('#help-docs-drawer', (el) => el.classList.contains('open'));
        assert.strictEqual(drawerOpen, true);
        const formulaCards = await page.$$eval('#help-drawer-content .formula-card', (els) => els.length);
        assert.ok(formulaCards >= 12, `Expected >=12 formula cards in Help Drawer, got ${formulaCards}`);
        const helpHtml = await page.$eval('#help-drawer-content', (el) => el.innerHTML);
        assert.ok(helpHtml.includes('math-frac') && helpHtml.includes('math-sqrt'), 'Expected typographic math spans in Help Drawer');
        assert.ok(!helpHtml.includes('\\frac') && !helpHtml.includes('\\text') && !helpHtml.includes('\\sqrt'), 'Found raw LaTeX backslashes in Help Drawer');
        await page.click('#drawer-overlay', { position: { x: 20, y: 20 } });
        const drawerClosed = await page.$eval('#help-docs-drawer', (el) => !el.classList.contains('open'));
        assert.strictEqual(drawerClosed, true);

        // 4. Contextual '?' pane popover button opens Help Drawer filtered to target tab
        await page.click('#t1-subtabs .btn-pane-help');
        assert.strictEqual(await page.$eval('#help-docs-drawer', (el) => el.classList.contains('open')), true);
        const filteredTab = await page.$eval('#help-drawer-content .formula-card', (el) => el.getAttribute('data-help-tab'));
        assert.strictEqual(filteredTab, 'Tab 1');
        await page.click('#btn-close-help');
      },
    },
  ];
};
