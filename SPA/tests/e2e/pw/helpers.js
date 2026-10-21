/**
 * Shared Playwright Helpers for Tab Navigation, API Synchronization & TableGrid Assertions.
 */
const assert = require('assert');

async function pollUntil(fn, { timeout = 15000, interval = 100, message = 'Condition timed out' } = {}) {
  const deadline = Date.now() + timeout;
  let lastErr = null;
  while (Date.now() < deadline) {
    try {
      const res = await fn();
      if (res) return res;
    } catch (err) {
      lastErr = err;
    }
    await new Promise((r) => setTimeout(r, interval));
  }
  if (lastErr) throw lastErr;
  throw new Error(message);
}

async function waitApi(page, urlPattern, actionFn, timeout = 90000) {
  const matchFn = (resp) => {
    const url = resp.url();
    if (typeof urlPattern === 'string') return url.includes(urlPattern);
    if (urlPattern instanceof RegExp) return urlPattern.test(url);
    if (typeof urlPattern === 'function') return urlPattern(resp);
    return false;
  };
  const respPromise = page.waitForResponse(matchFn, { timeout });
  await actionFn();
  const resp = await respPromise;
  let json = null;
  try {
    const ct = resp.headers()['content-type'] || '';
    if (ct.includes('application/json')) {
      json = await resp.json();
    }
  } catch (_) {}
  return { resp, status: resp.status(), json };
}

async function gotoTab(page, tabNum, waitUrlPattern = null) {
  const padded = String(tabNum).padStart(2, '0');
  const tabId = `tab_${padded}`;
  const btnSel = `#main-tab-nav .tab-btn[data-tab="${tabId}"]`;
  const paneSel = `#${tabId}`;

  let apiResult = null;
  if (waitUrlPattern) {
    apiResult = await waitApi(page, waitUrlPattern, async () => {
      await page.click(btnSel);
    });
  } else {
    await page.click(btnSel);
  }

  await page.waitForSelector(`${paneSel}.active`, { state: 'visible', timeout: 15000 });
  const isBtnActive = await page.$eval(btnSel, (el) => el.classList.contains('active'));
  assert.strictEqual(isBtnActive, true, `Expected ${btnSel} to have .active class`);
  return apiResult;
}

async function gridRows(page, containerId) {
  const sel = `#${containerId} tbody tr`;
  await page.waitForSelector(`#${containerId} .datagrid-table`, { state: 'attached', timeout: 15000 });
  return page.$$eval(sel, (trs) =>
    trs.map((tr) => Array.from(tr.querySelectorAll('td')).map((td) => td.innerText.trim()))
  );
}

async function gridTotalCount(page, containerId) {
  const statSel = `#${containerId} .grid-stats`;
  await page.waitForSelector(statSel, { state: 'visible', timeout: 15000 });
  const txt = await page.$eval(statSel, (el) => el.innerText.trim());
  const m = txt.match(/(\d+)/);
  return m ? parseInt(m[1], 10) : 0;
}

async function gridSort(page, containerId, colKey) {
  const thSel = `#${containerId} th[data-col="${colKey}"]`;
  await page.click(thSel);
  const icon = await page.$eval(`${thSel} .sort-icon`, (el) => el.textContent.trim());
  const rows = await gridRows(page, containerId);
  return { icon, rows };
}

async function gridSearch(page, containerId, text) {
  const inpSel = `#${containerId} .grid-search`;
  await page.waitForSelector(inpSel, { state: 'visible', timeout: 15000 });
  await page.click(inpSel);
  await page.fill(inpSel, '');
  if (text) {
    await page.type(inpSel, text);
  }
  const hasFocus = await page.$eval(inpSel, (el) => document.activeElement === el);
  assert.strictEqual(hasFocus, true, `Search input in #${containerId} lost focus after typing "${text}"`);
  const rows = await gridRows(page, containerId);
  const total = await gridTotalCount(page, containerId);
  return { hasFocus, rows, total };
}

async function svgLinkCount(page, stageId = 't3-nda-stage') {
  return page.$$eval(`#${stageId} svg.nda-link-svg path`, (paths) => paths.length);
}

module.exports = {
  assert,
  pollUntil,
  waitApi,
  gotoTab,
  gridRows,
  gridTotalCount,
  gridSort,
  gridSearch,
  svgLinkCount,
};
