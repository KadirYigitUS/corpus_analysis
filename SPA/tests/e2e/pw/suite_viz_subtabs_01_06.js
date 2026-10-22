/**
 * Suite 5: Granular Subtab E2E Tests for Tabs 01 to 06 (Inventory, Alignment, POS, Dependency, KWIC).
 * Uses real Playwright .click() on every .viz-subtab-btn and verifies DOM tables, charts, and scope/view invalidation.
 */
const { assert, pollUntil, waitApi, gotoTab, gridRows } = require('./helpers');

module.exports = async function suiteVizSubtabs01To06(ctx) {
  const { page } = ctx;

  return [
    {
      name: 'tab01_all_subtabs_charts_tables_and_scope_invalidation',
      fn: async () => {
        await Promise.all([
          page.waitForResponse((r) => r.url().includes('/api/v1/corpus/source-tables'), { timeout: 90000 }),
          page.goto('/', { waitUntil: 'domcontentloaded' }),
        ]);

        // Pill 2: Metin Boyutları (Şekil)
        const { json: sizesAll } = await waitApi(page, '/api/v1/corpus/sizes-chart', async () => {
          await page.click('#t1-subtabs .viz-subtab-btn[data-pane="t1-pane-sizes-chart"]');
        });
        assert.strictEqual(sizesAll.items.length, 13);
        const hasSizesCanvas = await page.$eval('#t1-sizes-chart-container', (el) => Boolean(el.querySelector('canvas#t1-sizes-canvas')));
        assert.strictEqual(hasSizesCanvas, true, 'Expected #t1-sizes-canvas in Tab 1 sizes chart subtab');

        // Pill 3: Doğrulama Tablosu
        const { json: verifyJson } = await waitApi(page, '/api/v1/corpus/verify-files', async () => {
          await page.click('#t1-subtabs .viz-subtab-btn[data-pane="t1-pane-verify"]');
        });
        const verifyRows = await gridRows(page, 't1-verify-grid');
        assert.strictEqual(verifyRows.length, verifyJson.rows.length);
        assert.strictEqual(verifyRows.length, 13);

        // Pill 4: Boyut Özeti
        const { json: sumJson } = await waitApi(page, '/api/v1/corpus/size-summary', async () => {
          await page.click('#t1-subtabs .viz-subtab-btn[data-pane="t1-pane-summary"]');
        });
        const sumRows = await gridRows(page, 't1-summary-grid');
        assert.strictEqual(sumRows.length, sumJson.rows.length);
        assert.strictEqual(sumRows.length, 13);

        // Changing global scope to indig_tr invalidates active Boyut Özeti subtab and reloads 3 rows
        const { json: sumIndig } = await waitApi(page, '/api/v1/corpus/size-summary', async () => {
          await page.selectOption('#global-scope-select', 'indig_tr');
        });
        assert.strictEqual(sumIndig.rows.length, 3);
        await pollUntil(async () => (await gridRows(page, 't1-summary-grid')).length === 3, {
          message: 'Expected Boyut Özeti subtab to reload 3 rows on indig_tr scope',
        });

        // Pill 5: Bellek & İçerik Kökleri
        const [, lemResp] = await Promise.all([
          page.waitForResponse((r) => r.url().includes('/api/v1/corpus/memory-report'), { timeout: 90000 }),
          page.waitForResponse((r) => r.url().includes('/api/v1/corpus/content-lemmas'), { timeout: 90000 }),
          page.click('#t1-subtabs .viz-subtab-btn[data-pane="t1-pane-memory"]'),
        ]);
        const lemJson = await lemResp.json();
        const memRows = await gridRows(page, 't1-memory-grid');
        const lemRows = await gridRows(page, 't1-lemmas-grid');
        assert.ok(memRows.length >= 1, 'Expected >=1 row in memory report table');
        assert.strictEqual(lemRows.length, lemJson.rows.length);
        assert.strictEqual(lemRows.length, 3);

        // Restore scope to all and return to inventory pane
        await waitApi(page, '/api/v1/corpus/content-lemmas', async () => {
          await page.selectOption('#global-scope-select', 'all');
        });
        await page.click('#t1-subtabs .viz-subtab-btn[data-pane="t1-pane-inventory"]');
      },
    },
    {
      name: 'tab02_structure_summary_and_scatter_subtab',
      fn: async () => {
        await gotoTab(page, 2);

        const [structResp, scatterResp] = await Promise.all([
          page.waitForResponse((r) => r.url().includes('/api/v1/alignment/structure-summary'), { timeout: 90000 }),
          page.waitForResponse((r) => r.url().includes('/api/v1/alignment/structure-scatter'), { timeout: 90000 }),
          page.click('#t2-subtabs .viz-subtab-btn[data-pane="t2-pane-structure"]'),
        ]);
        const [structJson, scatterJson] = await Promise.all([structResp.json(), scatterResp.json()]);
        assert.strictEqual(structJson.table.rows.length, 5);
        assert.ok(scatterJson.series.length >= 1);

        const structRows = await gridRows(page, 't2-structure-summary-grid');
        assert.strictEqual(structRows.length, 5);
        const hasStacked = await page.$eval('#t2-stacked-chart-container', (el) => Boolean(el.querySelector('canvas#t2-stacked-canvas')));
        const hasScatter = await page.$eval('#t2-scatter-chart-container', (el) => Boolean(el.querySelector('canvas#t2-scatter-canvas')));
        assert.strictEqual(hasStacked, true);
        assert.strictEqual(hasScatter, true);

        await page.click('#t2-subtabs .viz-subtab-btn[data-pane="t2-pane-pair"]');
      },
    },
    {
      name: 'tab04_pos_heatmap_dumbbell_and_forest_subtabs',
      fn: async () => {
        await gotoTab(page, 4);

        // Şekil 2A: UPOS Isı Haritası
        const { json: matJson } = await waitApi(page, '/api/v1/syntax/pos/matrix', async () => {
          await page.click('#t4-subtabs .viz-subtab-btn[data-pane="t4-pane-heatmap"]');
        });
        assert.strictEqual(matJson.rows.length, 13);
        const hasHeatmap = await page.$eval('#t4-heatmap-chart-container', (el) => Boolean(el.querySelector('canvas#t4-heatmap-canvas')));
        assert.strictEqual(hasHeatmap, true);

        // Şekil 2B: Dumbbell Çift Grafiği
        const { json: pairJson } = await waitApi(page, '/api/v1/syntax/pos/pair-delta/', async () => {
          await page.click('#t4-subtabs .viz-subtab-btn[data-pane="t4-pane-dumbbell"]');
        });
        assert.ok(pairJson.items.length >= 10);
        const hasDumbbell = await page.$eval('#t4-dumbbell-chart-container', (el) => Boolean(el.querySelector('canvas#t4-dumbbell-canvas')));
        assert.strictEqual(hasDumbbell, true);

        // Şekil 2C: Forest Plot
        const { json: forestJson } = await waitApi(page, '/api/v1/syntax/pos/group-comparison', async () => {
          await page.click('#t4-subtabs .viz-subtab-btn[data-pane="t4-pane-forest"]');
        });
        assert.ok(forestJson.items.length >= 10);
        const hasForest = await page.$eval('#t4-forest-chart-container', (el) => Boolean(el.querySelector('canvas#t4-forest-canvas')));
        assert.strictEqual(hasForest, true);

        await page.click('#t4-subtabs .viz-subtab-btn[data-pane="t4-pane-profiles"]');
      },
    },
    {
      name: 'tab05_aligned_bilingual_trees_and_tab06_kwic_subtabs',
      fn: async () => {
        // Tab 5 Aligned Bilingual Dependency Trees
        await gotoTab(page, 5);
        const { json: alJson } = await waitApi(page, '/api/v1/syntax/dep/aligned/', async () => {
          await page.click('#t5-subtabs .viz-subtab-btn[data-pane="t5-pane-aligned"]');
        });
        assert.ok(alJson.eng_svg && alJson.tur_svg);
        const svgCount = await page.$$eval('#t5-aligned-tree-stage svg', (els) => els.length);
        assert.strictEqual(svgCount, 2, `Expected 2 aligned <svg> trees in Tab 5, got ${svgCount}`);

        // Toggle Dim Function Words off and verify re-render
        const { json: noDimJson } = await waitApi(page, '/api/v1/syntax/dep/aligned/', async () => {
          await page.click('#t5-check-dim');
        });
        assert.ok(!noDimJson.eng_svg.includes('opacity:0.4'));
        await page.click('#t5-subtabs .viz-subtab-btn[data-pane="t5-pane-single"]');

        // Tab 6 KWIC Subtabs: Summary, Views Compare, NLTK
        await gotoTab(page, 6);
        await page.fill('#t6-input-query', 'robot');
        await page.selectOption('#t6-select-match', 'exact');

        const { json: sumJson } = await waitApi(page, '/api/v1/concordance/summary', async () => {
          await page.click('#t6-subtabs .viz-subtab-btn[data-pane="t6-pane-summary"]');
        });
        assert.strictEqual(sumJson.table.rows.length, 13);
        const sumRows = await gridRows(page, 't6-summary-table-container');
        assert.strictEqual(sumRows.length, 13);
        const hasSumBars = await page.$eval('#t6-summary-chart-container', (el) => Boolean(el.querySelector('canvas#t6-summary-bars-canvas')));
        assert.strictEqual(hasSumBars, true);

        const { json: viewsJson } = await waitApi(page, '/api/v1/concordance/views-compare', async () => {
          await page.click('#t6-subtabs .viz-subtab-btn[data-pane="t6-pane-views"]');
        });
        const viewRows = await gridRows(page, 't6-views-table-container');
        assert.strictEqual(viewRows.length, viewsJson.rows.length);
        assert.ok(viewRows.length >= 4);

        const { json: nltkJson } = await waitApi(page, '/api/v1/concordance/nltk', async () => {
          await page.click('#t6-subtabs .viz-subtab-btn[data-pane="t6-pane-nltk"]');
        });
        assert.ok(nltkJson.concordance.length > 0);
        const nltkText = await page.$eval('#t6-nltk-lines-container', (el) => el.innerText);
        assert.ok(nltkText.toLowerCase().includes('robot'));

        await page.click('#t6-subtabs .viz-subtab-btn[data-pane="t6-pane-kwic"]');
      },
    },
  ];
};
