/**
 * Suite 3: Tabs 05 to 08 (Syntactic Dependency, Search & KWIC, Dispersion, Lexical Diversity).
 */
const { assert, pollUntil, waitApi, gotoTab, gridRows, gridTotalCount } = require('./helpers');

module.exports = async function suiteTabs05To08(ctx) {
  const { page, facts } = ctx;

  return [
    {
      name: 'tab05_dependency_tree_svg_conll_and_download',
      fn: async () => {
        await Promise.all([
          page.waitForResponse((r) => r.url().includes('/api/v1/corpus/source-tables'), { timeout: 90000 }),
          page.goto('/', { waitUntil: 'domcontentloaded' }),
        ]);

        const svgWait = page.waitForResponse((r) => r.url().includes('/api/v1/syntax/dep/tree-svg'), {
          timeout: 90000,
        });
        const conllWait = page.waitForResponse((r) => r.url().includes('/api/v1/syntax/dep/conll'), {
          timeout: 90000,
        });
        await gotoTab(page, 5);
        await Promise.all([svgWait, conllWait]);

        const hasSvg = await page.$eval('#t5-tree-stage', (el) => Boolean(el.querySelector('svg')));
        assert.strictEqual(hasSvg, true, 'Expected <svg> inside #t5-tree-stage');
        const textNodes = await page.$$eval('#t5-tree-stage svg text', (els) => els.length);
        assert.ok(textNodes > 0, 'Expected <text> nodes inside dependency SVG');

        const conllRows = await gridRows(page, 't5-conll-grid');
        assert.ok(conllRows.length > 0, 'Expected CoNLL grid rows');
        const conllCols = await page.$$eval('#t5-conll-grid th[data-col]', (ths) =>
          ths.map((th) => th.getAttribute('data-col'))
        );
        assert.deepStrictEqual(conllCols, ['idx', 'word', 'lemma', 'upos', 'head', 'head_word', 'deprel']);

        // Download SVG fires download event
        const downloadPromise = page.waitForEvent('download', { timeout: 15000 });
        await page.click('#t5-btn-download-svg');
        const download = await downloadPromise;
        assert.ok(download.suggestedFilename().endsWith('.svg'));
      },
    },
    {
      name: 'tab06_kwic_modes_spans_sort_punct_compare_and_invalid_regex',
      fn: async () => {
        await gotoTab(page, 6);

        // 1. Exact, Glob, and Regex search modes
        for (const [mode, query] of [
          ['exact', 'robot'],
          ['glob', 'robot*'],
          ['regex', '^robot.*'],
        ]) {
          await page.fill('#t6-input-query', query);
          await page.selectOption('#t6-select-match', mode);
          const { status, json } = await waitApi(page, '/api/v1/concordance/search', async () => {
            await page.click('#t6-btn-search');
          });
          assert.strictEqual(status, 200);
          assert.ok(json.total_hits > 0, `Expected >0 hits for mode=${mode}, query=${query}`);
          const badgeText = await page.$eval('#t6-hit-count', (el) => el.innerText.trim());
          assert.strictEqual(badgeText, `${json.total_hits} hits`);
          const gridTotal = await gridTotalCount(page, 't6-kwic-grid');
          assert.strictEqual(gridTotal, json.returned_hits, 'Grid total must equal returned_hits');
        }

        // 2. Span L/R and sort change the order
        await page.fill('#t6-input-query', 'robot');
        await page.selectOption('#t6-select-match', 'exact');
        await page.fill('#t6-input-span-l', '3');
        await page.fill('#t6-input-span-r', '3');
        await page.selectOption('#t6-select-sort', 'position');
        await waitApi(page, '/api/v1/concordance/search', async () => {
          await page.click('#t6-btn-search');
        });
        const posRows = await gridRows(page, 't6-kwic-grid');

        await page.selectOption('#t6-select-sort', 'R1');
        await waitApi(page, '/api/v1/concordance/search', async () => {
          await page.click('#t6-btn-search');
        });
        const r1Rows = await gridRows(page, 't6-kwic-grid');
        assert.notDeepStrictEqual(posRows[0], r1Rows[0], 'Sorting by R1 should reorder KWIC lines');

        // 3. Punct-compare fills the pane
        const { status: pStatus } = await waitApi(page, '/api/v1/concordance/punct-compare', async () => {
          await page.click('#t6-btn-punct-compare');
        });
        assert.strictEqual(pStatus, 200);
        const punctVisible = await page.$eval('#t6-punct-pane', (el) => el.style.display !== 'none');
        assert.strictEqual(punctVisible, true);
        const punctCards = await page.$$eval('#t6-punct-pane .kpi-card', (els) => els.length);
        assert.strictEqual(punctCards, 4, 'Expected 4 punctuation regime cards');

        // 4. Invalid regex shows an error, not a crash
        ctx.collector.allowExpected400 = true;
        await page.fill('#t6-input-query', '[unclosed_regex');
        await page.selectOption('#t6-select-match', 'regex');
        const { status: errStatus, json: errJson } = await waitApi(page, '/api/v1/concordance/search', async () => {
          await page.click('#t6-btn-search');
        });
        ctx.collector.allowExpected400 = false;
        assert.strictEqual(errStatus, 400);
        assert.ok(errJson.error, 'Expected error field for invalid regex');
        const hasErrCard = await page.$eval('#t6-kwic-grid', (el) => el.innerText.includes('Invalid'));
        assert.strictEqual(hasErrCard, true);
      },
    },
    {
      name: 'tab07_batch_dispersion_and_correlation_grids',
      fn: async () => {
        await gotoTab(page, 7);
        await page.fill('#t7-input-terms', 'robot, insan, dünya, uzay');
        const { status, json } = await waitApi(page, '/api/v1/concordance/batch-dispersion', async () => {
          await page.click('#t7-btn-run-batch');
        });
        assert.strictEqual(status, 200);

        const sumRows = await gridRows(page, 't7-summary-grid');
        const corrRows = await gridRows(page, 't7-correlation-grid');
        assert.strictEqual(sumRows.length, json.summary.length);
        assert.strictEqual(corrRows.length, json.pairwise.length);
        assert.ok(sumRows.length === 4 && corrRows.length === 6, 'Expected 4 summary rows and 6 pairwise rows');
      },
    },
    {
      name: 'tab08_lexical_diversity_table_and_mattr_trajectory',
      fn: async () => {
        const divWait = page.waitForResponse((r) => r.url().includes('/api/v1/lexicon/diversity/table'), {
          timeout: 90000,
        });
        await gotoTab(page, 8);
        const divResp = await divWait;
        const divJson = await divResp.json();

        const rows = await gridRows(page, 't8-diversity-grid');
        assert.strictEqual(rows.length, divJson.items.length);
        assert.strictEqual(rows.length, 13, 'Expected 13 rows in diversity table');
        facts.tab08_row_count = rows.length;

        const colKeys = await page.$$eval('#t8-diversity-grid th[data-col]', (ths) =>
          ths.map((th) => th.getAttribute('data-col'))
        );
        assert.deepStrictEqual(colKeys, [
          'text_code',
          'N',
          'V',
          'TTR',
          'Guiraud_R',
          'Yule_K',
          'Simpson_D',
          'MATTR_500',
          'MTLD',
          'HD_D',
        ]);

        // Refresh button reloads table
        await waitApi(page, '/api/v1/lexicon/diversity/table', async () => {
          await page.click('#t8-btn-refresh-diversity');
        });

        // View MATTR Curve fills #t8-mattr-pane
        const { status: mStatus } = await waitApi(page, '/api/v1/lexicon/diversity/mattr', async () => {
          await page.click('#t8-btn-view-mattr');
        });
        assert.strictEqual(mStatus, 200);
        await pollUntil(async () => page.$eval('#t8-mattr-pane', (el) => el.style.display !== 'none'));
        const mattrText = await page.$eval('#t8-mattr-pane', (el) => el.innerText);
        assert.ok(mattrText.includes('MATTR Curve'), 'Expected MATTR Curve summary text');
      },
    },
  ];
};
