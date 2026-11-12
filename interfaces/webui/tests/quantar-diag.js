const { chromium } = require('/home/fatsio/AI/Ethan/interfaces/webui/node_modules/playwright');
const fs = require('fs');
(async () => {
  const token = fs.readFileSync('/tmp/quantar-token.txt','utf8').trim();
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  await context.addCookies([{ name:'ethan_token', value:token, domain:'localhost', path:'/', httpOnly:true }]);
  const page = await context.newPage();
  page.on('console', msg => console.error('CONSOLE', msg.type(), msg.text()));
  page.on('requestfailed', req => console.error('REQFAILED', req.url(), req.failure()?.errorText));
  page.on('response', res => { if (res.status()>=400) console.error('HTTP', res.status(), res.url()); });
  const resp = await page.goto('http://localhost:3001/quantar', { waitUntil:'networkidle', timeout:30000 });
  console.log('PAGE STATUS', resp.status());
  await page.waitForTimeout(2000);
  const body = await page.textContent('body');
  console.log('BODY HAS NOT FOUND', body.includes('could not be found'));
  await browser.close();
})();
