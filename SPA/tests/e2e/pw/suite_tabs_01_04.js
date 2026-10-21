/**
 * Suite 2: Tabs 01 to 04 (Corpus Inventory, Translation Alignment, NDA Parallel, POS Profiles).
 */
const {
  assert, pollUntil, waitApi, gotoTab, gridRows, gridTotalCount, gridSort, gridSearch, svgLinkCount,
} = require('./helpers');

module.exports = async function suiteTabs01To04(ctx) {
  const { page, facts } = ctx;

  return [
    {
      name: 'tab01_inventory_grid_search_sort_and_schema',
      fn: async () => {
        await Promise.all([
          page.waitForResponse((r) => r.url().includes('/api/v1/corpus/source-tables'), { timeout: 90000 }),
          page.goto('/', { waitUntil: 'domcontentloaded' }),
        ]);

        const rows = await gridRows(page, 't1-inventory-grid');
        const total = await gridTotalCount(page, 't1-inventory-grid');
        assert.ok(rows.length >= 10, `Expected >=10 rows in Tab 1 grid, got ${rows.length}`);
        assert.strictEqual(total, 13, `Expected 13 total texts in 'all' scope, got ${total}`);
        facts.tab01_row_count = total;

        for (const id of ['t1-total-texts', 't1-total-tokens', 't1-total-sentences', 't1-author-count']) {
          const valText = await page.$eval(`#${id}`, (el) => el.innerText.replace(/,/g, '').trim());
          const num = Number(valText);
          assert.ok(!Number.isNaN(num) && num > 0, `KPI #${id} is not positive numeric: "${valText}"`);
        }

        const searchRes = await gridSearch(page, 't1-inventory-grid', 'SCS');
        assert.strictEqual(searchRes.hasFocus, true);
        assert.ok(searchRes.rows.length >= 1, 'Expected at least 1 row for search "SCS"');
        await gridSearch(page, 't1-inventory-grid', '');
        assert.strictEqual(await gridTotalCount(page, 't1-inventory-grid'), 13);

        const sortAsc = await gridSort(page, 't1-inventory-grid', 'code');
        assert.strictEqual(sortAsc.icon, '▲');
        const sortDesc = await gridSort(page, 't1-inventory-grid', 'code');
        assert.strictEqual(sortDesc.icon, '▼');
        assert.notStrictEqual(sortAsc.rows[0][0], sortDesc.rows[0][0], 'Sort toggle did not reverse row order');

        const { status: schemaStatus, json: schemaJson } = await waitApi(page, '/api/v1/corpus/schema/', async () => {
          await page.click('#t1-inventory-grid .btn-inspect-schema');
        });
        assert.strictEqual(schemaStatus, 200);
        assert.strictEqual(await page.$eval('#t1-schema-pane', (el) => el.style.display !== 'none'), true);
        assert.strictEqual(await page.$eval('#t1-schema-text-code', (el) => el.innerText.trim()), schemaJson.text_code);
        assert.ok((await gridRows(page, 't1-schema-columns-grid')).length > 0);
      },
    },
    {
      name: 'tab02_alignment_kpis_chapters_ner_and_pair_switch',
      fn: async () => {
        const kpiWait = page.waitForResponse((r) => r.url().includes('/api/v1/alignment/kpis/'), { timeout: 90000 });
        const statsWait = page.waitForResponse((r) => r.url().includes('/api/v1/alignment/stats/'), { timeout: 90000 });
        const rowsWait = page.waitForResponse((r) => r.url().includes('/api/v1/alignment/rows'), { timeout: 90000 });
        await gotoTab(page, 2);
        const [kpiResp, statsResp, rowsResp] = await Promise.all([kpiWait, statsWait, rowsWait]);
        const [kpiJson, statsJson, rowsJson] = await Promise.all([kpiResp.json(), statsResp.json(), rowsResp.json()]);

        assert.strictEqual(await page.$eval('#t2-kpi-total', (el) => Number(el.innerText.trim())), kpiJson.total_alignments);
        assert.strictEqual(await page.$eval('#t2-kpi-tur-more', (el) => Number(el.innerText.trim())), kpiJson.count_tur_more);
        assert.strictEqual(await page.$eval('#t2-kpi-eng-more', (el) => Number(el.innerText.trim())), kpiJson.count_eng_more);
        assert.strictEqual(await page.$eval('#t2-kpi-equal-sent', (el) => Number(el.innerText.trim())), kpiJson.count_one_one);
        assert.strictEqual(await page.$eval('#t2-kpi-ratio', (el) => Number(el.innerText.trim())), Number(kpiJson.sentence_ratio));
        assert.strictEqual(await page.$eval('#t2-kpi-one-to-one', (el) => el.innerText.trim()), `${kpiJson.one_to_one_pct}%`);
        assert.strictEqual(await page.$eval('#t2-kpi-expansion', (el) => Number(el.innerText.trim())), Number(kpiJson.expansion_ratio));
        assert.ok(statsJson.series.length > 1000, 'Expected full-book sent_diff series > 1000 points');

        assert.ok(rowsJson.total_pages > 2, `Expected >2 pages, got ${rowsJson.total_pages}`);
        await waitApi(page, '/api/v1/alignment/rows', async () => { await page.click('#t2-alignment-grid .grid-next-btn'); });
        const { json: page3Json } = await waitApi(page, '/api/v1/alignment/rows', async () => {
          await page.click('#t2-alignment-grid .grid-next-btn');
        });
        assert.strictEqual(page3Json.page, 3, 'Expected server-side navigation to reach page 3');
        assert.ok(page3Json.rows.length > 0 && page3Json.rows[0].ai >= 50, 'Page 3 should have AI >= 50');

        const { json: nerJson } = await waitApi(page, '/api/v1/alignment/rows', async () => {
          await page.click('#t2-ner-filter-bar .ner-pill-btn[data-ner="PER"]');
        });
        assert.ok(nerJson.total > 0 && nerJson.total < kpiJson.total_alignments);
        assert.ok((await page.$$eval('#t2-alignment-grid .tok.ner-PER', (els) => els.length)) > 0);

        await waitApi(page, '/api/v1/alignment/rows', async () => {
          await page.click('#t2-ner-filter-bar .ner-pill-btn[data-ner="ALL"]');
        });

        const { json: pairKpi } = await waitApi(page, '/api/v1/alignment/kpis/TL-PA_A-ZB', async () => {
          await page.selectOption('#t2-select-pair', 'TL-PA_A-ZB');
        });
        await pollUntil(async () => (await page.$eval('#t2-kpi-total', (el) => Number(el.innerText.trim()))) === pairKpi.total_alignments);

        const { json: tspRows } = await waitApi(page, '/api/v1/alignment/rows', async () => {
          await page.selectOption('#t2-select-pair', 'TSP-JL_KS-ZB');
        });
        assert.strictEqual(tspRows.total, 1407, 'Expected 1407 alignments for TSP-JL_KS-ZB');
        await pollUntil(async () => (await page.$$eval('#t2-chapter-sidebar .ch-btn', (els) => els.length)) === 7);
      },
    },
    {
      name: 'tab03_nda_parallel_tokens_svg_links_and_dictionary_drawer',
      fn: async () => {
        const htmlWait = page.waitForResponse((r) => r.url().includes('/api/v1/alignment/nda/html/'), { timeout: 90000 });
        const dictWait = page.waitForResponse((r) => r.url().includes('/api/v1/alignment/nda/dictionary/'), { timeout: 90000 });
        await gotoTab(page, 3);
        const [htmlResp, dictResp] = await Promise.all([htmlWait, dictWait]);
        const [htmlJson, dictJson] = await Promise.all([htmlResp.json(), dictResp.json()]);

        assert.ok(htmlJson.html.includes('.pv table.pv-grid'), 'Expected PV_CSS in Tab 3 HTML payload');
        const domTokens = await page.$$eval('#t3-nda-stage .t, #t3-nda-stage .t-pill', (els) => els.length);
        const apiTokenMatches = (htmlJson.html.match(/class="t(?:\s|")/g) || []).length;
        assert.ok(domTokens > 0 && domTokens === apiTokenMatches);
        facts.nda_token_counts = facts.nda_token_counts || {};
        facts.nda_token_counts[htmlJson.pair_code] = domTokens;

        await pollUntil(async () => (await svgLinkCount(page)) > 0, { message: 'Expected >0 SVG connector paths on Tab 3' });
        const initialLinks = await svgLinkCount(page);
        await page.click('#btn-redraw-svg-links');
        assert.strictEqual(await svgLinkCount(page), initialLinks);

        await page.click('#t3-nda-stage .pv-toggles button:nth-child(2)');
        assert.strictEqual(await page.$eval('#t3-nda-stage .pv', (el) => el.classList.contains('hide-lemma')), true);
        await page.click('#t3-nda-stage .pv-toggles button:nth-child(2)');

        await page.click('#btn-toggle-nda-dict');
        assert.strictEqual(await page.$eval('#t3-dict-drawer', (el) => el.classList.contains('open')), true);
        if (dictJson.linked_count > 0) {
          assert.ok((await page.$$eval('#t3-dict-linked-list .kpi-card', (els) => els.length)) > 0);
        }
        await page.click('#t3-dict-drawer .drawer-close');

        const { json: nextHtml } = await waitApi(page, '/api/v1/alignment/nda/html/TL-PA_A-ZB', async () => {
          await page.selectOption('#t3-select-pair', 'TL-PA_A-ZB');
        });
        const nextTokens = await page.$$eval('#t3-nda-stage .t, #t3-nda-stage .t-pill', (els) => els.length);
        assert.ok(nextTokens > 0);
        facts.nda_token_counts[nextHtml.pair_code] = nextTokens;
      },
    },
    {
      name: 'tab04_pos_profiles_pair_delta_and_group_comparison',
      fn: async () => {
        const profWait = page.waitForResponse((r) => r.url().includes('/api/v1/syntax/pos/profiles'), { timeout: 90000 });
        const sumWait = page.waitForResponse((r) => r.url().includes('/api/v1/syntax/pos/author-summary'), { timeout: 90000 });
        const deltaWait = page.waitForResponse((r) => r.url().includes('/api/v1/syntax/pos/pair-delta/'), { timeout: 90000 });
        const groupWait = page.waitForResponse((r) => r.url().includes('/api/v1/syntax/pos/group-comparison'), { timeout: 90000 });
        await gotoTab(page, 4);
        const [, sumResp, , groupResp] = await Promise.all([profWait, sumWait, deltaWait, groupWait]);
        const [sumJson, groupAllJson] = await Promise.all([sumResp.json(), groupResp.json()]);

        assert.strictEqual((await gridRows(page, 't4-pos-profiles-grid')).length, 13);
        assert.strictEqual(sumJson.items.length, 7);
        assert.strictEqual(await page.$$eval('#t4-author-summary-table tbody tr', (trs) => trs.length), 7);

        const { json: smJson } = await waitApi(page, '/api/v1/syntax/pos/group-comparison', async () => {
          await page.selectOption('#t4-select-comp-2c', 'SM');
        });
        const { json: zbaJson } = await waitApi(page, '/api/v1/syntax/pos/group-comparison', async () => {
          await page.selectOption('#t4-select-comp-2c', 'ZB_A');
        });
        const { json: okJson } = await waitApi(page, '/api/v1/syntax/pos/group-comparison', async () => {
          await page.selectOption('#t4-select-comp-2c', 'OK');
        });
        assert.strictEqual(smJson.author, 'SM');
        assert.strictEqual(zbaJson.author, 'ZB');
        assert.strictEqual(okJson.author, 'OK');
        assert.notStrictEqual(smJson.chi2, okJson.chi2);
        assert.notStrictEqual(zbaJson.p_value, smJson.p_value);
        assert.notStrictEqual(groupAllJson.cramers_v, zbaJson.cramers_v);
      },
    },
  ];
};
