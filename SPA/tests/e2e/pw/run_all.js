/**
 * Node Playwright Suite Runner for Corpus Analysis SPA.
 * Executes suites serially, captures traces/screenshots on failure, writes results.json.
 */
const fs = require('fs');
const path = require('path');
const {
  ARTIFACT_ROOT,
  launchBrowser,
  createSuiteContext,
  captureFailureArtifacts,
  finalizeSuiteContext,
} = require('./harness');

const SUITES = [
  ['suite_shell', require('./suite_shell')],
  ['suite_tabs_01_04', require('./suite_tabs_01_04')],
  ['suite_tabs_05_08', require('./suite_tabs_05_08')],
  ['suite_tabs_09_11', require('./suite_tabs_09_11')],
  ['suite_viz_subtabs_01_06', require('./suite_viz_subtabs_01_06')],
  ['suite_viz_subtabs_07_10', require('./suite_viz_subtabs_07_10')],
];

async function runWithTimeout(fn, timeoutMs) {
  let timer = null;
  try {
    return await Promise.race([
      fn(),
      new Promise((_, reject) => {
        timer = setTimeout(() => reject(new Error(`Test timed out after ${timeoutMs}ms`)), timeoutMs);
      }),
    ]);
  } finally {
    if (timer) clearTimeout(timer);
  }
}

async function main() {
  const baseUrl = process.env.BASE_URL || 'http://127.0.0.1:5000';
  const perTestTimeout = parseInt(process.env.PW_TEST_TIMEOUT || '120000', 10);
  const resultsPath = path.join(ARTIFACT_ROOT, 'results.json');

  const results = [];
  const facts = {};
  let totalIndex = 0;
  let failedCount = 0;

  console.log(`TAP version 13\n# BASE_URL=${baseUrl}`);
  const browser = await launchBrowser();

  const suiteFilter = process.env.PW_SUITE || '';
  const activeSuites = suiteFilter
    ? SUITES.filter(([name]) => name.includes(suiteFilter))
    : SUITES;

  try {
    for (const [suiteName, suiteFactory] of activeSuites) {
      const ctx = await createSuiteContext(browser, baseUrl, suiteName);
      ctx.facts = facts;
      let suiteFailed = false;

      try {
        const tests = await suiteFactory(ctx);
        for (const testDef of tests) {
          totalIndex += 1;
          ctx.collector.reset();
          const t0 = Date.now();
          let status = 'passed';
          let errorMsg = null;
          let failureArtifacts = null;

          try {
            await runWithTimeout(testDef.fn, perTestTimeout);
            const issues = ctx.collector.issues();
            if (issues.length > 0) {
              throw new Error(`Console/network errors detected:\n${issues.join('\n')}`);
            }
          } catch (err) {
            status = 'failed';
            suiteFailed = true;
            failedCount += 1;
            errorMsg = err && err.stack ? err.stack : String(err);
            failureArtifacts = await captureFailureArtifacts(ctx, testDef.name);
          }

          const durationMs = Date.now() - t0;
          const prefix = status === 'passed' ? 'ok' : 'not ok';
          console.log(`${prefix} ${totalIndex} - ${suiteName} :: ${testDef.name} (${durationMs}ms)`);
          if (errorMsg) {
            console.error(`  ---\n  ${errorMsg.split('\n').join('\n  ')}\n  ...`);
          }

          results.push({
            id: `${suiteName}::${testDef.name}`,
            suite: suiteName,
            name: testDef.name,
            status,
            duration_ms: durationMs,
            error: errorMsg,
            artifacts: failureArtifacts,
          });
        }
      } finally {
        const tracePath = await finalizeSuiteContext(ctx, suiteFailed);
        if (tracePath) {
          console.error(`# Saved failure trace: ${tracePath}`);
        }
      }
    }
  } finally {
    await browser.close();
  }

  console.log(`1..${totalIndex}`);
  const summary = {
    timestamp: new Date().toISOString(),
    base_url: baseUrl,
    total: totalIndex,
    passed: totalIndex - failedCount,
    failed: failedCount,
    facts,
    tests: results,
  };
  fs.writeFileSync(resultsPath, JSON.stringify(summary, null, 2), 'utf-8');

  if (failedCount > 0) {
    process.exit(1);
  }
}

main().catch((err) => {
  console.error('Fatal runner error:', err);
  process.exit(2);
});
