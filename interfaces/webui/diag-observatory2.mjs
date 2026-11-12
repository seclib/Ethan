#!/usr/bin/env node
/**
 * diag-observatory2.mjs — capture ALL 404 URLs + console errors per Observatory
 * route (browser-level, authoritative). Usage: node diag-observatory2.mjs
 */
import { chromium } from "playwright";

const BASE = "http://localhost:3001";
const PROBE_USER = "obs_probe_mwajy1ov";
const PROBE_PASS = "Probe-Only-Passw0rd!";
const ROUTES = [
  "/workspaces/observatory",
  "/workspaces/observatory/vault",
  "/workspaces/observatory/graph",
  "/workspaces/observatory/canvas",
  "/workspaces/observatory/timeline",
  "/workspaces/observatory/search",
  "/workspaces/observatory/engineering",
  "/workspaces/observatory/ai-insights",
];

async function login(page) {
  await page.goto(`${BASE}/login`, { waitUntil: "networkidle", timeout: 30000 });
  await page.fill("#operator-id", PROBE_USER, { timeout: 15000 });
  await page.fill("#password", PROBE_PASS, { timeout: 15000 });
  await page.click("button[type=submit]");
  try { await page.waitForURL((u) => !u.pathname.includes("/login"), { timeout: 30000 }); } catch (e) {}
}

const browser = await chromium.launch({ headless: true });
for (const route of ROUTES) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  const failures = [];
  const consoleAll = [];
  const all404 = [];
  page.on("requestfailed", (r) => failures.push(`FAIL ${r.method()} ${r.url()} ${r.failure()?.errorText ?? ""}`));
  page.on("console", (m) => consoleAll.push(`${m.type()}: ${m.text().slice(0, 150)}`));
  page.on("response", (res) => { if (res.status() === 404) all404.push(`404 ${res.url()}`); });
  try {
    await login(page);
    await page.goto(`${BASE}${route}`, { waitUntil: "domcontentloaded", timeout: 30000 });
  } catch (e) {
    console.log(`### ${route}  NAV ERROR: ${e.message.split("\n")[0]}`);
    await context.close();
    continue;
  }
  await page.waitForLoadState("networkidle", { timeout: 20000 }).catch(() => {});
  await page.waitForTimeout(3500);
  console.log(`### ${route}  console_all=${consoleAll.length}  404s=${all404.length}  failreq=${failures.length}`);
  for (const n of all404.slice(0, 20)) console.log("  404:", n);
  for (const f of failures.slice(0, 8)) console.log("  fail:", f);
  for (const c of consoleAll.slice(0, 25)) console.log("  CON:", c);
  await context.close();
}
await browser.close();
