#!/usr/bin/env node
/**
 * diag-observatory.mjs — Diagnostic cible pour probe-observatory.mjs.
 * - collecte toutes les erreurs 404 reseau par route
 * - collecte les console errors par route
 * - inspecte le DOM de la page Vault (inputs, editeurs, liens)
 */
import { chromium } from "playwright";

const BASE = process.argv[2] || "http://localhost:3001";
const ROUTE = process.argv[3] || "/workspaces/observatory/vault";

const results = [];
const ok = (n, d) => { results.push({ n, p: true }); console.log(`  [OK] ${n}${d ? " — " + d : ""}`); };
const fail = (n, d) => { results.push({ n, p: false }); console.log(`  [FAIL] ${n}${d ? " — " + d : ""}`); };

async function snapshot(page, label) {
  const failures = [];
  page.on("requestfailed", (r) => failures.push(`FAIL ${r.method()} ${r.url()} ${r.failure()?.errorText ?? ""}`));
  const consoleAll = [];
  page.on("console", (m) => consoleAll.push(`${m.type()}: ${m.text().slice(0, 140)}`));
  const all404 = [];
  page.on("request", (r) => { if (r.status() === 404) all404.push(`404 ${r.url()}`); });
  await page.waitForTimeout(3000);
  console.log(`\n### ${label}  (console_all=${consoleAll.length}, 404s=${all404.length})`);
  for (const c of consoleAll.slice(0, 25)) console.log("  CON:", c);
  for (const n of all404.slice(0, 15)) console.log("  404:", n);
}

async function dumpVaultDOM(page) {
  console.log("\n### VAULT DOM");
  const info = await page.evaluate(() => {
    const out = { inputs: [], textareas: 0, contenteditable: 0, buttons: 0, links: 0, editorLike: [] };
    document.querySelectorAll("input").forEach((el) => {
      out.inputs.push({ id: el.id, ph: el.placeholder, type: el.type });
    });
    out.textareas = document.querySelectorAll("textarea").length;
    out.contenteditable = document.querySelectorAll("[contenteditable]").length;
    out.buttons = document.querySelectorAll("button").length;
    out.links = document.querySelectorAll("a").length;
    document.querySelectorAll("div, section, article").forEach((el) => {
      const cls = (el.className || "").toString().slice(0, 80);
      if (/editor|markdown|content|prose|file|doc/i.test(cls)) out.editorLike.push(cls);
    });
    return out;
  });
  console.log("inputs:", JSON.stringify(info.inputs.slice(0, 15)));
  console.log("textareas:", info.textareas, "contenteditable:", info.contenteditable, "buttons:", info.buttons, "links:", info.links);
  for (const c of info.editorLike.slice(0, 12)) console.log("  editor-like:", c);
}

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
await page.goto(`${BASE}/login`, { waitUntil: "networkidle", timeout: 30000 });
await page.fill("#operator-id", "obs_probe_mwajy1ov", { timeout: 15000 }).catch(() => {});
await page.fill("#password", "Probe-Only-Passw0rd!", { timeout: 15000 }).catch(() => {});
await page.click("button[type=submit]");
try { await page.waitForURL((u) => !u.pathname.includes("/login"), { timeout: 30000 }).catch(() => {}); } catch (e) {}
await snapshot(page, ROUTE);
await dumpVaultDOM(page);
await browser.close();
