const { chromium } = require('playwright');

const previewUrl = 'http://localhost:8000/api/v1/metadata/interfaces/26608863-59e7-41eb-bc17-5221c6d2ea38/candidates/0/preview/';
const liveUrl = 'http://prototype.ai4mde.localhost/autologin?as=seller_jansen&next=' + encodeURIComponent('/Seller/render_Seller_Seller_Dashboard');

async function stats(page) {
  const target = page.frames().find((frame) => frame !== page.mainFrame() && frame.url().startsWith('about:srcdoc')) || page.mainFrame();
  return await target.evaluate(() => {
    const all = Array.from(document.querySelectorAll('[data-section-id]'));
    const byPos = (pos) => all.filter((el) => el.getAttribute('data-position') === pos).length;
    const byLayout = (layout) => all.filter((el) => el.getAttribute('data-layout') === layout).length;
    const text = document.body.innerText || '';
    return {
      header: byPos('header'),
      footer: byPos('footer'),
      sidebar: byPos('sidebar'),
      main: byPos('main'),
      siteNav: byLayout('site-nav') + byLayout('nav-links') + byLayout('nav-bar'),
      actionPanel: byLayout('activity_action') + byLayout('action_panel'),
      unsupported: text.includes('Unsupported section layout'),
      headerText: Array.from(document.querySelectorAll('[data-position="header"]')).map((el) => el.innerText.trim()).join(' | ').slice(0, 220),
      footerText: Array.from(document.querySelectorAll('[data-position="footer"]')).map((el) => el.innerText.trim()).join(' | ').slice(0, 220),
      title: document.title,
    };
  });
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const previewContext = await browser.newContext({
    viewport: { width: 1536, height: 760 },
    extraHTTPHeaders: { Authorization: 'Bearer studio-internal-service-key' },
  });
  const page = await previewContext.newPage();
  await page.goto(previewUrl, { waitUntil: 'networkidle', timeout: 60000 });
  await page.screenshot({ path: 'tmp/preview-live-check/preview-c0.png', fullPage: true });
  const previewStats = await stats(page);

  await previewContext.close();

  const liveContext = await browser.newContext({ viewport: { width: 1536, height: 760 } });
  const livePage = await liveContext.newPage();
  await livePage.goto(liveUrl, { waitUntil: 'networkidle', timeout: 60000 });
  await livePage.screenshot({ path: 'tmp/preview-live-check/live-c0.png', fullPage: true });
  const liveStats = await stats(livePage);

  console.log(JSON.stringify({ previewStats, liveStats }, null, 2));
  await liveContext.close();
  await browser.close();
})();
