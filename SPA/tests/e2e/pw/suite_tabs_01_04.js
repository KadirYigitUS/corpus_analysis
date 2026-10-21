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

        // Verify KPI cards are numeric
        for (const id of ['t1-total-texts', 't1-total-tokens', 't1-total-sentences', 't1-author-count']) {
          const valText = await page.$eval(`#${id}`, (el) => el.innerText.replace(/,/g, '').trim());
          const num = Number(valText);
          assert.ok(!Number.isNaN(num) && num > 0, `KPI #${id} is not positive numeric: "${valText}"`);
        }

        // Search "SCS" filters to >=1 row and preserves focus
        const searchRes = await gridSearch(page, 't1-inventory-grid', 'SCS');
        assert.strictEqual(searchRes.hasFocus, true);
        assert.ok(searchRes.rows.length >= 1, 'Expected at least 1 row for search "SCS"');
        await gridSearch(page, 't1-inventory-grid', '');
        const restoredTotal = await gridTotalCount(page, 't1-inventory-grid');
        assert.strictEqual(restoredTotal, 13);

        // Sort toggles ascending then descending
        const sortAsc = await gridSort(page, 't1-inventory-grid', 'code');
        assert.strictEqual(sortAsc.icon, '▲');
        const firstCodeAsc = sortAsc.rows[0][0];
        const sortDesc = await gridSort(page, 't1-inventory-grid', 'code');
        assert.strictEqual(sortDesc.icon, '▼');
        const firstCodeDesc = sortDesc.rows[0][0];
        assert.notStrictEqual(firstCodeAsc, firstCodeDesc, 'Sort toggle did not reverse row order');

        // Inspect Schema button fills #t1-schema-pane
        const { status: schemaStatus, json: schemaJson } = await waitApi(
          page,
          '/api/v1/corpus/schema/',
          async () => {
            await page.click('#t1-inventory-grid .btn-inspect-schema');
          }
        );
        assert.strictEqual(schemaStatus, 200);
        const paneVisible = await page.$eval('#t1-schema-pane', (el) => el.style.display !== 'none');
        assert.strictEqual(paneVisible, true, '#t1-schema-pane did not become visible');
        const schemaCode = await page.$eval('#t1-schema-text-code', (el) => el.innerText.trim());
        assert.strictEqual(schemaCode, schemaJson.text_code);
        const schemaRows = await gridRows(page, 't1-schema-columns-grid');
        assert.ok(schemaRows.length > 0, 'Expected schema columns grid to have rows');
      },
    },
    {
      name: 'tab02_alignment_kpis_chapters_ner_and_pair_switch',
      fn: async () => {
        const kpiWait = page.waitForResponse((r) => r.url().includes('/api/v1/alignment/kpis/'), { timeout: 90000 });
        const rowsWait = page.waitForResponse((r) => r.url().includes('/api/v1/alignment/rows'), { timeout: 90000 });
        await gotoTab(page, 2);
        const [kpiResp] = await Promise.all([kpiWait, rowsWait]);
        const kpiJson = await kpiResp.json();

        // Assert 4 KPI cards equal API JSON
        const domTotal = await page.$eval('#t2-kpi-total', (el) => Number(el.innerText.trim()));
        const domRatio = await page.$eval('#t2-kpi-ratio', (el) => Number(el.innerText.trim()));
        const domOneToOne = await page.$eval('#t2-kpi-one-to-one', (el) => el.innerText.trim());
        const domExp = await page.$eval('#t2-kpi-expansion', (el) => Number(el.innerText.trim()));

        assert.strictEqual(domTotal, kpiJson.total_alignments);
        assert.strictEqual(domRatio, Number(kpiJson.sentence_ratio));
        assert.strictEqual(domOneToOne, `${kpiJson.one_to_one_pct}%`);
        assert.strictEqual(domExp, Number(kpiJson.expansion_ratio));

        const alignRows = await gridRows(page, 't2-alignment-grid');
        assert.ok(alignRows.length > 0, 'Expected alignment grid to have rows');

        const chBtns = await page.$$eval('#t2-chapter-sidebar .ch-btn', (els) => els.length);
        assert.ok(chBtns > 1, 'Expected chapter sidebar buttons');
        const nerBtns = await page.$$eval('#t2-ner-filter-bar .ner-pill-btn', (els) => els.length);
        assert.strictEqual(nerBtns, 9, 'Expected 9 NER filter pills');

        // Pair select drives /alignment/kpis/{pair}
        const { json: pairKpi } = await waitApi(page, '/api/v1/alignment/kpis/TL-PA_A-ZB', async () => {
          await page.selectOption('#t2-select-pair', 'TL-PA_A-ZB');
        });
        await pollUntil(async () => {
          const cur = await page.$eval('#t2-kpi-total', (el) => Number(el.innerText.trim()));
          return cur === pairKpi.total_alignments;
        });
      },
    },
    {
      name: 'tab03_nda_parallel_tokens_svg_links_and_dictionary_drawer',
      fn: async () => {
        const htmlWait = page.waitForResponse((r) => r.url().includes('/api/v1/alignment/nda/html/'), {
          timeout: 90000,
        });
        const dictWait = page.waitForResponse((r) => r.url().includes('/api/v1/alignment/nda/dictionary/'), {
          timeout: 90000,
        });
        await gotoTab(page, 3);
        const [htmlResp, dictResp] = await Promise.all([htmlWait, dictWait]);
        const htmlJson = await htmlResp.json();
        const dictJson = await dictResp.json();

        // Count tokens inside API HTML response and compare with live DOM
        const domTokens = await page.$$eval('#t3-nda-stage .t, #t3-nda-stage .t-pill', (els) => els.length);
        const apiTokenMatches = (htmlJson.html.match(/class="t(?:\s|")/g) || []).length;
        assert.ok(domTokens > 0, 'Expected >0 parallel tokens rendered on Tab 3');
        assert.strictEqual(domTokens, apiTokenMatches, 'DOM token count must match API HTML response');
        facts.nda_token_counts = facts.nda_token_counts || {};
        facts.nda_token_counts[htmlJson.pair_code] = domTokens;

        // SVG connector count > 0 and Redraw keeps it non-zero
        await pollUntil(async () => (await svgLinkCount(page)) > 0, {
          message: 'Expected >0 SVG connector paths on Tab 3',
        });
        const initialLinks = await svgLinkCount(page);
        await page.click('#btn-redraw-svg-links');
        const afterRedraw = await svgLinkCount(page);
        assert.ok(afterRedraw > 0 && afterRedraw === initialLinks, 'Redraw must keep SVG links non-zero');

        // Candidate / Linked / Realia / Irrealia pill classes present
        const hasLinkedOrCand = await page.$$eval(
          '#t3-nda-stage .t.lk, #t3-nda-stage .t.cand, #t3-nda-stage .t.single-en, #t3-nda-stage .t.single-tr',
          (els) => els.length
        );
        assert.ok(hasLinkedOrCand > 0, 'Expected NDA highlight pill classes on stage');
        const hasBadges = await page.$$eval(
          '#t3-nda-stage sup.lk-b, #t3-nda-stage sup.irr-b, #t3-nda-stage .ner-b',
          (els) => els.length
        );
        assert.ok(hasBadges > 0, 'Expected Realia/Irrealia/Link badges on Tab 3 stage');

        // Dictionary drawer toggles and lists linked, EN, and TR entries
        await page.click('#btn-toggle-nda-dict');
        const isOpen = await page.$eval('#t3-dict-drawer', (el) => el.classList.contains('open'));
        assert.strictEqual(isOpen, true);
        if (dictJson.linked_count > 0) {
          const linkedCards = await page.$$eval('#t3-dict-linked-list .kpi-card', (els) => els.length);
          assert.ok(linkedCards > 0, 'Expected linked dictionary cards');
        }
        await page.click('#t3-dict-drawer .drawer-close');
        const isClosed = await page.$eval('#t3-dict-drawer', (el) => !el.classList.contains('open'));
        assert.strictEqual(isClosed, true);

        // Pair dropdown loads another pair
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
        const profWait = page.waitForResponse((r) => r.url().includes('/api/v1/syntax/pos/profiles'), {
          timeout: 90000,
        });
        const deltaWait = page.waitForResponse((r) => r.url().includes('/api/v1/syntax/pos/pair-delta/'), {
          timeout: 90000,
        });
        const groupWait = page.waitForResponse((r) => r.url().includes('/api/v1/syntax/pos/group-comparison'), {
          timeout: 90000,
        });
        await gotoTab(page, 4);
        await Promise.all([profWait, deltaWait, groupWait]);

        const posRows = await gridRows(page, 't4-pos-profiles-grid');
        assert.strictEqual(posRows.length, 13, `Expected 13 POS profile rows, got ${posRows.length}`);
        const headers = await page.$$eval('#t4-pos-profiles-grid th', (ths) => ths.map((t) => t.innerText.trim()));
        assert.ok(headers.some((h) => h.includes('NOUN')) && headers.some((h) => h.includes('VERB')));

        const deltaCards = await page.$$eval('#t4-pair-delta-container .kpi-card', (els) => els.length);
        assert.ok(deltaCards > 0, 'Expected pair-delta UPOS cards');
        const groupItems = await page.$$eval('#t4-group-comp-list > div', (els) => els.length);
        assert.ok(groupItems > 0, 'Expected group-comparison list items');
      },
    },
  ];
};
