/**
 * Suite 4: Tabs 09 to 11 & Cross-Cutting Random-Order Navigation (Collocation, TF-IDF, Explorer).
 */
const fs = require('fs');
const { assert, pollUntil, waitApi, gotoTab, gridRows, gridTotalCount } = require('./helpers');

module.exports = async function suiteTabs09To11(ctx) {
  const { page, facts } = ctx;

  return [
    {
      name: 'tab09_collocation_6_metrics_min_freq_and_graphcoll',
      fn: async () => {
        await Promise.all([
          page.waitForResponse((r) => r.url().includes('/api/v1/corpus/source-tables'), { timeout: 90000 }),
          page.goto('/', { waitUntil: 'domcontentloaded' }),
        ]);

        await gotoTab(page, 9);
        await page.fill('#t9-input-node', 'robot');
        await page.selectOption('#t9-select-text', 'BR-SM');
        await page.fill('#t9-input-min-freq', '2');

        const firstCollocates = {};
        for (const metric of ['LogDice', 'MI', 'G2', 'T', 'MI2', 'MI3']) {
          await page.selectOption('#t9-select-metric', metric);
          const { status, json } = await waitApi(page, '/api/v1/lexicon/collocation/table', async () => {
            await page.click('#t9-btn-run-colloc');
          });
          assert.strictEqual(status, 200);
          assert.strictEqual(json.metric, metric);
          const rows = await gridRows(page, 't9-collocation-grid');
          assert.ok(rows.length > 0, `Expected collocation rows for metric ${metric}`);
          firstCollocates[metric] = rows[0][0];

          const headerText = await page.$eval('#t9-stats-header', (el) => el.innerText);
          assert.ok(headerText.includes(metric) && headerText.includes('Union Slots'));
        }

        // Verify different metrics produce distinct top collocates across the 6 measures
        const uniqueTop = new Set(Object.values(firstCollocates));
        assert.ok(uniqueTop.size >= 2, 'Expected 6 collocation metrics to re-sort top collocates');

        // Min-freq filters rows
        const countAt2 = await gridTotalCount(page, 't9-collocation-grid');
        await page.fill('#t9-input-min-freq', '10');
        await waitApi(page, '/api/v1/lexicon/collocation/table', async () => {
          await page.click('#t9-btn-run-colloc');
        });
        const countAt10 = await gridTotalCount(page, 't9-collocation-grid');
        assert.ok(countAt10 < countAt2, `Expected min_freq=10 (${countAt10}) < min_freq=2 (${countAt2})`);

        // GraphColl radial network SVG rendered
        const hasGraphSvg = await page.$eval('#t9-graphcoll-stage', (el) => Boolean(el.querySelector('svg')));
        assert.strictEqual(hasGraphSvg, true);
      },
    },
    {
      name: 'tab10_tfidf_keywords_propn_toggle_and_bundle_download',
      fn: async () => {
        const tfidfWait = page.waitForResponse((r) => r.url().includes('/api/v1/lexicon/tfidf/keywords'), {
          timeout: 90000,
        });
        await gotoTab(page, 10);
        await tfidfWait;

        const cardsNoPropn = await page.$$eval('#t10-keywords-container .kpi-card', (els) =>
          els.map((el) => el.innerText)
        );
        assert.ok(cardsNoPropn.length > 0, 'Expected TF-IDF keyword cards');

        // Toggle Exclude PROPN off and verify results change
        await page.click('#t10-check-exclude-propn');
        await waitApi(page, '/api/v1/lexicon/tfidf/keywords', async () => {
          await page.click('#t10-btn-run-tfidf');
        });
        const cardsWithPropn = await page.$$eval('#t10-keywords-container .kpi-card', (els) =>
          els.map((el) => el.innerText)
        );
        assert.notDeepStrictEqual(
          cardsNoPropn,
          cardsWithPropn,
          'Exclude-PROPN toggle must change TF-IDF keyword results'
        );

        // Verify Tab 10 Report Summary subtab renders structured .report-section-card HTML with zero <pre> dumps
        await waitApi(page, '/api/v1/lexicon/report/preview', async () => {
          await page.click('#t10-subtabs button[data-pane="t10-pane-report-preview"]');
        });
        const reportCards = await page.$$eval('#t10-report-summary-container .report-section-card', (els) => els.length);
        assert.ok(reportCards >= 2, `Expected >=2 .report-section-card blocks, got ${reportCards}`);
        const preCount = await page.$$eval('#t10-report-summary-container pre', (els) => els.length);
        assert.strictEqual(preCount, 0, 'Expected zero <pre> markdown dumps in #t10-report-summary-container');
        await page.click('#t10-subtabs button[data-pane="t10-pane-keywords"]');

        // Download bundle fires download event with file size > 0
        const downloadPromise = page.waitForEvent('download', { timeout: 90000 });
        await page.click('#t10-btn-download-bundle');
        const download = await downloadPromise;
        assert.ok(download.suggestedFilename().endsWith('.zip'));
        const dlPath = await download.path();
        assert.ok(dlPath && fs.existsSync(dlPath), 'Downloaded bundle path must exist');
        const stat = fs.statSync(dlPath);
        assert.ok(stat.size > 0, `Expected bundle zip size > 0, got ${stat.size}`);
        facts.bundle_zip_bytes = stat.size;
      },
    },
    {
      name: 'tab11_explorer_quick_search_and_clipboard_copy',
      fn: async () => {
        await gotoTab(page, 11);
        await page.fill('#t11-input-term', 'robot');
        const { status, json } = await waitApi(page, '/api/v1/export/quick-search', async () => {
          await page.click('#t11-btn-run-console');
        });
        assert.strictEqual(status, 200);
        assert.ok(json.total_hits > 0, 'Expected >0 hits in Tab 11 quick search');

        const badge = await page.$eval('#t11-hits-badge', (el) => el.innerText.trim());
        assert.strictEqual(badge, `${json.total_hits} hits`);
        const presence = await page.$eval('#t11-presence-text', (el) => el.innerText.trim());
        assert.ok(presence.length > 0 && presence !== '-');
        const samples = await page.$$eval('#t11-samples-container > div', (els) => els.length);
        assert.ok(samples > 0, 'Expected sample lines in Tab 11');

        const snippet = await page.$eval('#t11-python-snippet', (el) => el.value);
        assert.ok(snippet.includes('CorpusLoader') || snippet.includes('quick_search') || snippet.length > 10);

        await page.click('#t11-btn-copy-script');
        await pollUntil(async () => {
          const clip = await page.evaluate(() => navigator.clipboard.readText());
          return clip === snippet;
        });
      },
    },
    {
      name: 'crosscutting_random_order_tab_navigation',
      fn: async () => {
        const order = [7, 2, 11, 4, 9, 1, 6, 10, 3, 8, 5];
        for (const tabNum of order) {
          await gotoTab(page, tabNum);
        }
      },
    },
  ];
};
