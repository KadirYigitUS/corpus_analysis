/**
 * Suite 6: Granular Subtab E2E Tests for Tabs 07 to 10 (Dispersion, Diversity, Collocation, TF-IDF)
 * and Global Mode ('drop' vs 'mask') Live Reactivity.
 */
const { assert, pollUntil, waitApi, gotoTab, gridRows } = require('./helpers');

module.exports = async function suiteVizSubtabs07To10(ctx) {
  const { page } = ctx;

  return [
    {
      name: 'tab07_labeled_groups_tables_heatmaps_and_dispersion_curves',
      fn: async () => {
        await Promise.all([
          page.waitForResponse((r) => r.url().includes('/api/v1/corpus/source-tables'), { timeout: 90000 }),
          page.goto('/', { waitUntil: 'domcontentloaded' }),
        ]);

        await gotoTab(page, 7);
        await page.fill('#t7-input-terms', 'makine alanı: robot, makine | insan alanı: insan, adam');
        const { json: batchJson } = await waitApi(page, '/api/v1/concordance/batch-dispersion', async () => {
          await page.click('#t7-btn-run-batch');
        });
        assert.strictEqual(batchJson.summary.length, 4);
        assert.strictEqual((await gridRows(page, 't7-summary-grid')).length, 4);

        // Subtab 2: Sayımlar & Oranlar
        const { json: matJson } = await waitApi(page, '/api/v1/concordance/batch-matrices', async () => {
          await page.click('#t7-subtabs .viz-subtab-btn[data-pane="t7-pane-tables"]');
        });
        const countRows = await gridRows(page, 't7-counts-table');
        const rateRows = await gridRows(page, 't7-rates-table');
        assert.strictEqual(countRows.length, matJson.counts.rows.length);
        assert.strictEqual(rateRows.length, matJson.rates.rows.length);

        // Subtab 3: Şekil 3A Per10k Isı Haritası
        await waitApi(page, '/api/v1/concordance/batch-matrices', async () => {
          await page.click('#t7-subtabs .viz-subtab-btn[data-pane="t7-pane-rates-heatmap"]');
        });
        assert.strictEqual(
          await page.$eval('#t7-rates-heatmap-container', (el) => Boolean(el.querySelector('canvas#t7-rates-canvas'))),
          true
        );

        // Subtab 4: Şekil 3B Bağıntı Matrisi
        await waitApi(page, '/api/v1/concordance/batch-matrices', async () => {
          await page.click('#t7-subtabs .viz-subtab-btn[data-pane="t7-pane-corr-matrix"]');
        });
        assert.strictEqual(
          await page.$eval('#t7-corr-heatmap-container', (el) => Boolean(el.querySelector('canvas#t7-corr-canvas'))),
          true
        );

        // Subtab 5: Şekil 3C Anlatı Dağılımı
        await waitApi(page, '/api/v1/concordance/batch-matrices', async () => {
          await page.click('#t7-subtabs .viz-subtab-btn[data-pane="t7-pane-dispersion-curves"]');
        });
        assert.strictEqual(
          await page.$eval('#t7-chunk-curves-container', (el) => Boolean(el.querySelector('canvas#t7-chunk-canvas'))),
          true
        );
        await page.click('#t7-subtabs .viz-subtab-btn[data-pane="t7-pane-summary-grid"]');
      },
    },
    {
      name: 'tab08_all_diversity_subtabs_and_drop_vs_mask_reactivity',
      fn: async () => {
        await page.selectOption('#global-scope-select', 'indig_tr');
        const divWait = page.waitForResponse((r) => r.url().includes('/api/v1/lexicon/diversity/table'), { timeout: 90000 });
        await gotoTab(page, 8);
        await divWait;

        // Verify mode='drop' vs mode='mask' updates MATTR_500 column in #t8-diversity-grid
        await waitApi(page, '/api/v1/lexicon/diversity/table', async () => {
          await page.selectOption('#matrix-filter', 'true');
        });
        const rowsDrop = await gridRows(page, 't8-diversity-grid');
        await waitApi(page, '/api/v1/lexicon/diversity/table', async () => {
          await page.selectOption('#matrix-mode', 'mask');
        });
        const rowsMask = await gridRows(page, 't8-diversity-grid');
        assert.notStrictEqual(rowsDrop[0][7], rowsMask[0][7], 'Expected MATTR_500 to differ between mode=drop and mode=mask');

        // Restore defaults cleanly
        await waitApi(page, '/api/v1/lexicon/diversity/table', async () => {
          await page.selectOption('#matrix-mode', 'drop');
        });
        await waitApi(page, '/api/v1/lexicon/diversity/table', async () => {
          await page.selectOption('#matrix-filter', 'false');
        });

        // Select compact text A-ZB for fast length sensitivity curve
        await page.selectOption('#t8-select-text', 'A-ZB');

        // Subtab 2: Bölüm 9.3 Metin Boyu Duyarlılığı
        await waitApi(page, '/api/v1/lexicon/diversity/sensitivity', async () => {
          await page.click('#t8-subtabs .viz-subtab-btn[data-pane="t8-pane-sensitivity"]');
        });
        assert.strictEqual(await page.$eval('#t8-sens-chart-container', (el) => Boolean(el.querySelector('canvas#t8-sens-canvas'))), true);
        assert.ok((await gridRows(page, 't8-sens-table-container')).length >= 3);

        // Subtab 3: Token ↔ Lemma & Noktalama
        await waitApi(page, '/api/v1/lexicon/diversity/compare', async () => {
          await page.click('#t8-subtabs .viz-subtab-btn[data-pane="t8-pane-comparisons"]');
        });
        assert.strictEqual((await gridRows(page, 't8-tok-lem-table')).length, 3);
        assert.ok((await gridRows(page, 't8-punct-table')).length >= 2);

        // Subtab 4: Şekil 4A Radar Grafiği
        await waitApi(page, '/api/v1/lexicon/diversity/radar', async () => {
          await page.click('#t8-subtabs .viz-subtab-btn[data-pane="t8-pane-radar"]');
        });
        assert.strictEqual(await page.$eval('#t8-radar-chart-container', (el) => Boolean(el.querySelector('canvas#t8-radar-canvas'))), true);

        // Subtab 5: Şekil 4B MATTR Yörüngeleri
        await waitApi(page, '/api/v1/lexicon/diversity/mattr-trajectories', async () => {
          await page.click('#t8-subtabs .viz-subtab-btn[data-pane="t8-pane-mattr"]');
        });
        assert.strictEqual(await page.$eval('#t8-mattr-curves-container', (el) => Boolean(el.querySelector('canvas#t8-mattr-canvas'))), true);

        // Subtab 6: Şekil 4C Zipf Eğrileri
        await waitApi(page, '/api/v1/lexicon/diversity/zipf-curves', async () => {
          await page.click('#t8-subtabs .viz-subtab-btn[data-pane="t8-pane-zipf"]');
        });
        assert.strictEqual(await page.$eval('#t8-zipf-curves-container', (el) => Boolean(el.querySelector('canvas#t8-zipf-canvas'))), true);

        await page.click('#t8-subtabs .viz-subtab-btn[data-pane="t8-pane-diversity-grid"]');
        await waitApi(page, '/api/v1/lexicon/diversity/table', async () => {
          await page.selectOption('#global-scope-select', 'all');
        });
      },
    },
    {
      name: 'tab09_collocation_and_tab10_tfidf_all_subtabs',
      fn: async () => {
        await gotoTab(page, 9);

        // Tab 9 Subtab 2: Şekil 5 GraphColl Dağılım Grafiği
        await waitApi(page, '/api/v1/lexicon/collocation/scatter', async () => {
          await page.click('#t9-subtabs .viz-subtab-btn[data-pane="t9-pane-scatter"]');
        });
        assert.strictEqual(await page.$eval('#t9-scatter-chart-container', (el) => Boolean(el.querySelector('canvas#t9-scatter-canvas'))), true);

        // Tab 9 Subtab 3: Ölçüt & Pencere Duyarlılığı
        await waitApi(page, '/api/v1/lexicon/collocation/sensitivity', async () => {
          await page.click('#t9-subtabs .viz-subtab-btn[data-pane="t9-pane-sensitivity"]');
        });
        assert.ok((await gridRows(page, 't9-measures-table')).length >= 3);
        assert.ok((await gridRows(page, 't9-window-table')).length >= 3);

        // Tab 9 Subtab 4: NLTK Bigram Doğrulama
        await waitApi(page, '/api/v1/lexicon/collocation/nltk', async () => {
          await page.click('#t9-subtabs .viz-subtab-btn[data-pane="t9-pane-nltk"]');
        });
        assert.ok((await gridRows(page, 't9-nltk-collocs-table')).length >= 1);
        assert.ok((await gridRows(page, 't9-nltk-ngrams-table')).length >= 1);
        await page.click('#t9-subtabs .viz-subtab-btn[data-pane="t9-pane-colloc-grid"]');

        // Tab 10 Subtab 2: Şekil 6 TF-IDF Isı Haritası & Subtab 3: Canlı Rapor Önizleme
        await gotoTab(page, 10);
        await waitApi(page, '/api/v1/lexicon/tfidf/dense', async () => {
          await page.click('#t10-subtabs .viz-subtab-btn[data-pane="t10-pane-heatmap"]');
        });
        assert.strictEqual(await page.$eval('#t10-heatmap-chart-container', (el) => Boolean(el.querySelector('canvas#t10-heatmap-canvas'))), true);

        await waitApi(page, '/api/v1/lexicon/report/preview', async () => {
          await page.click('#t10-subtabs .viz-subtab-btn[data-pane="t10-pane-report-preview"]');
        });
        await pollUntil(async () => (await gridRows(page, 't10-report-summary-table')).length >= 3);
        await page.click('#t10-subtabs .viz-subtab-btn[data-pane="t10-pane-keywords"]');
      },
    },
  ];
};
