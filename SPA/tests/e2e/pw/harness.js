/**
 * Playwright Browser/Context/Trace/Artifact Harness for Corpus Analysis SPA.
 */
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ARTIFACT_ROOT = path.resolve(__dirname, '../../results/playwright');
const TRACES_DIR = path.join(ARTIFACT_ROOT, 'traces');
const SCREENSHOTS_DIR = path.join(ARTIFACT_ROOT, 'screenshots');
const VIDEOS_DIR = path.join(ARTIFACT_ROOT, 'videos');

function ensureArtifactDirs() {
  [ARTIFACT_ROOT, TRACES_DIR, SCREENSHOTS_DIR, VIDEOS_DIR].forEach((dir) => {
    fs.mkdirSync(dir, { recursive: true });
  });
}

function slugify(name) {
  return String(name)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 80);
}

async function launchBrowser() {
  ensureArtifactDirs();
  return chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
  });
}

async function createSuiteContext(browser, baseUrl, suiteName) {
  ensureArtifactDirs();
  const recordVideo = process.env.PW_VIDEO === '1' ? { dir: VIDEOS_DIR, size: { width: 1440, height: 900 } } : undefined;
  const context = await browser.newContext({
    baseURL: baseUrl,
    viewport: { width: 1440, height: 900 },
    acceptDownloads: true,
    recordVideo,
  });

  try {
    await context.grantPermissions(['clipboard-read', 'clipboard-write'], { origin: baseUrl });
  } catch (_) {
    // Ignore if permissions are unsupported in specific headless build
  }

  await context.tracing.start({ screenshots: true, snapshots: true, sources: true });
  const page = await context.newPage();

  // Auto-dismiss any native alert/confirm dialogs while recording their messages
  const dialogs = [];
  page.on('dialog', async (dialog) => {
    dialogs.push({ type: dialog.type(), message: dialog.message() });
    await dialog.accept();
  });

  const collector = {
    pageErrors: [],
    consoleErrors: [],
    failedRequests: [],
    serverErrors: [],
    dialogs,
    allowExpected400: false,
    reset() {
      this.pageErrors.length = 0;
      this.consoleErrors.length = 0;
      this.failedRequests.length = 0;
      this.serverErrors.length = 0;
      this.dialogs.length = 0;
      this.allowExpected400 = false;
    },
    issues() {
      return [
        ...this.pageErrors.map((e) => `pageerror: ${e}`),
        ...this.consoleErrors.map((e) => `console.error: ${e}`),
        ...this.failedRequests.map((e) => `requestfailed: ${e}`),
        ...this.serverErrors.map((e) => `5xx: ${e}`),
      ];
    },
  };

  page.on('pageerror', (err) => {
    collector.pageErrors.push(err && err.message ? err.message : String(err));
  });

  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      const txt = msg.text();
      if (txt.includes('favicon.ico')) return;
      if (collector.allowExpected400 && txt.includes('status of 400')) return;
      collector.consoleErrors.push(txt);
    }
  });

  page.on('requestfailed', (req) => {
    const url = req.url();
    const errText = req.failure()?.errorText || 'unknown';
    if (!url.includes('favicon.ico') && !errText.includes('net::ERR_ABORTED')) {
      collector.failedRequests.push(`${req.method()} ${url} (${errText})`);
    }
  });

  page.on('response', (resp) => {
    const status = resp.status();
    const url = resp.url();
    if (status >= 500 && !url.includes('favicon.ico')) {
      collector.serverErrors.push(`${status} ${resp.request().method()} ${url}`);
    }
  });

  return {
    context,
    page,
    collector,
    suiteName,
    artifacts: { ARTIFACT_ROOT, TRACES_DIR, SCREENSHOTS_DIR, VIDEOS_DIR },
  };
}

async function captureFailureArtifacts(ctx, testName) {
  const slug = `${slugify(ctx.suiteName)}__${slugify(testName)}`;
  const screenshotPath = path.join(SCREENSHOTS_DIR, `${slug}.png`);
  const domPath = path.join(SCREENSHOTS_DIR, `${slug}.html`);
  try {
    await ctx.page.screenshot({ path: screenshotPath, fullPage: true });
    const html = await ctx.page.content();
    fs.writeFileSync(domPath, html, 'utf-8');
  } catch (_) {}
  return { screenshotPath, domPath };
}

async function finalizeSuiteContext(ctx, suiteFailed) {
  const slug = slugify(ctx.suiteName);
  const tracePath = path.join(TRACES_DIR, `${slug}_trace.zip`);
  try {
    if (suiteFailed || process.env.PW_SAVE_TRACES === '1') {
      await ctx.context.tracing.stop({ path: tracePath });
    } else {
      await ctx.context.tracing.stop();
    }
  } catch (_) {}
  await ctx.context.close();
  return suiteFailed ? tracePath : null;
}

module.exports = {
  ARTIFACT_ROOT,
  launchBrowser,
  createSuiteContext,
  captureFailureArtifacts,
  finalizeSuiteContext,
};
