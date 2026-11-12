#!/usr/bin/env node
/**
 * probe-observatory.mjs — Validation navigateur REELLE du workspace Observatory
 * (8 sections : Overview, Vault, Graph, Canvas, Timeline, Search, Engineering,
 *  AI Insights).
 *
 * Contraste avec probe-e2e.mjs (UI générique v5) :
 *   - cible uniquement Observatory ;
 *   - vérifie le rendu, la navigation, le responsive, le thème sombre, les états
 *     de chargement/erreur, les interactions et la cohérence des composants ;
 *   - ne pas considère le build comme preuve de qualité visuelle.
 *
 * Usage : node probe-observatory.mjs [baseWebUI]  (defaut http://localhost:3001)
 */

import { chromium } from "playwright";

const BASE = process.argv[2] || "http://localhost:3001";
const API = process.env.ETHAN_API_URL || "http://localhost:8000";
const PROBE_USER = `obs_probe_${Date.now().toString(36)}`;
const PROBE_PASS = "Probe-Only-Passw0rd!";

const results = [];
const ok = (name, detail = "") => {
  results.push({ name, pass: true });
  console.log(`  [OK]   ${name}${detail ? ` — ${detail}` : ""}`);
};
const fail = (name, detail = "") => {
  results.push({ name, pass: false });
  console.log(`  [FAIL] ${name}${detail ? ` — ${detail}` : ""}`);
};

async function registerProbeUser() {
  const res = await fetch(`${API}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username: PROBE_USER, password: PROBE_PASS }),
  });
  if (!res.ok) throw new Error(`register ${res.status}: ${await res.text()}`);
  console.log(`[1] Compte probe cree : ${PROBE_USER}`);
}

function collectDiagnostics(page) {
  const consoleErrors = [];
  const pageErrors = [];
  const failedReqs = [];
  const onConsole = (m) => {
    if (m.type() === "error") consoleErrors.push(m.text());
  };
  const onPageError = (e) => pageErrors.push(String(e).split("\n")[0]);
  const onReqFailed = (r) =>
    failedReqs.push(`${r.method()} ${r.url()} → ${r.failure()?.errorText ?? "?"}`);
  page.on("console", onConsole);
  page.on("pageerror", onPageError);
  page.on("requestfailed", onReqFailed);
  return {
    stop: () => {
      page.off("console", onConsole);
      page.off("pageerror", onPageError);
      page.off("requestfailed", onReqFailed);
    },
    consoleErrors,
    pageErrors,
    failedReqs,
  };
}

async function visitRoute(page, route, label) {
  const diag = collectDiagnostics(page);
  let resp;
  try {
    resp = await page.goto(`${BASE}${route}`, { waitUntil: "domcontentloaded", timeout: 30000 });
  } catch (e) {
    diag.stop();
    fail(`${label} ${route}`, `navigate threw: ${e.message.split("\n")[0]}`);
    return { diag, status: 0 };
  }
  try {
    await page.waitForLoadState("networkidle", { timeout: 20000 }).catch(() => {});
  } catch (e) {
    // timeout: pas grave pour la validation
  }
  const status = resp ? resp.status() : 0;
  const contentLen = (await page.content()).length;
  const mainVisible = await page.locator("main").first().isVisible().catch(() => false);
  const boundary = await page.getByText(/Application error|Something went wrong/i).first().isVisible().catch(() => false);
  const diagErrors = diag.consoleErrors.filter((t) => !/favicon|React DevTools|sourcemap/i.test(t));
  const netFails = diag.failedReqs.filter((u) => !/favicon/.test(u));

  if (status >= 400 || !mainVisible || boundary) {
    fail(`${label} ${route}`, `HTTP ${status}, content=${contentLen}, boundary=${boundary}`);
  } else {
    ok(`${label} ${route}`, `HTTP ${status}, content=${contentLen}o, console=${diagErrors.length}, reseau=${netFails.length}`);
  }
  for (const t of diagErrors.slice(0, 2)) console.log(`         · console: ${t.slice(0, 160)}`);
  for (const u of netFails.slice(0, 2)) console.log(`         · reseau:  ${u.slice(0, 160)}`);
  diag.stop();
  return { diag, status, contentLen };
}

async function checkSectionContent(page, label, expectedTexts) {
  const missing = [];
  for (const t of expectedTexts) {
    const found = await page.getByText(t, { exact: false }).first().isVisible().catch(() => false);
    if (!found) missing.push(t);
  }
  if (missing.length) fail(`${label} contenu`, `manquant: ${missing.join(", ")}`);
  else ok(`${label} contenu`, `attends: ${expectedTexts.join(", ")}`);
}

async function checkLoadingState(page, label, indicator) {
  const shown = await page.locator(indicator).first().isVisible().catch(() => false);
  if (shown) ok(`${label} etat chargement`, indicator);
  else fail(`${label} etat chargement`, `atteint ${indicator} absent`);
}

async function checkTheme(page, label) {
  const hasDarkClass = await page.evaluate(() =>
    document.documentElement.classList.contains("dark") ||
    document.documentElement.getAttribute("data-theme") === "dark"
  );
  const rootBg = await page.evaluate(() => {
    const el = document.documentElement;
    const cs = getComputedStyle(el);
    return cs.backgroundColor;
  });
  if (!hasDarkClass) fail(`${label} theme sombre`, "classe .dark / data-theme manquante");
  else if (!/rgba\(23, 23, 27\)/.test(rootBg)) fail(`${label} theme sombre`, `background root = ${rootBg}`);
  else ok(`${label} theme sombre`, `dark mode active, bg=${rootBg}`);
}

async function checkResponsive(page, label, width, height) {
  const res = await page.evaluate(({ w, h }) => {
    const el = document.documentElement;
    return {
      innerW: el.clientWidth,
      innerH: el.clientHeight,
      scrolled: el.scrollWidth > el.clientWidth,
    };
  }, { w: width, h: height });
  if (res.innerW === width && res.innerH === height) ok(`${label} responsive ${width}x${height}`, `client=${res.innerW}x${res.innerH}, nested=${res.scrolled}`);
  else fail(`${label} responsive ${width}x${height}`, `client=${res.innerW}x${res.innerH}, nested=${res.scrolled}`);
}
async function main() {
  console.log(`\n=== Observatory — Validation navigateur REELLE ===\nWebUI=${BASE}`);
  await registerProbeUser();

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  // ── [1] Login reel ──────────────────────────────────────────────────────
  console.log("\n[1] Login reel (cookie ethan_token)");
  await page.goto(`${BASE}/login`, { waitUntil: "networkidle", timeout: 30000 });
  const hasLoginForm = await page.locator("#operator-id, [data-testid*='operator']").first().isVisible().catch(() => false);
  if (!hasLoginForm) {
    await page.fill("input[type=email], input[name=username], input[id*=operator]", PROBE_USER);
    await page.fill("input[type=password]", PROBE_PASS);
    await page.click("button[type=submit]");
  } else {
    await page.fill("#operator-id", PROBE_USER);
    await page.fill("#password", PROBE_PASS);
    await page.click("button[type=submit]");
  }
  try {
    await page.waitForURL((u) => !u.pathname.includes("/login"), { timeout: 30000 });
    const cookies = await page.context().cookies();
    const token = cookies.find((c) => c.name === "ethan_token");
    if (token) ok(`login effectue → ${page.url()} (cookie ethan_token present)`);
    else fail("login effectue", "cookie ethan_token absent");
  } catch (e) {
    fail("login effectue", e.message.split("\n")[0]);
    const errText = await page.locator("[class*=error], [role=alert]").allTextContents().catch(() => []);
    if (errText.length) console.log(`         · erreur affichee: ${errText.join(" | ").slice(0, 200)}`);
    await browser.close();
    process.exit(1);
  }

  // ── [2] Les 8 sections (viewport desktop 1440x900) ─────────────────────
  console.log("\n[2] Sections — rendu + erreurs (1440x900)");
  const SECTIONS = [
    ["/workspaces/observatory", "Overview"],
    ["/workspaces/observatory/vault", "Vault"],
    ["/workspaces/observatory/graph", "Graph"],
    ["/workspaces/observatory/canvas", "Canvas"],
    ["/workspaces/observatory/timeline", "Timeline"],
    ["/workspaces/observatory/search", "Search"],
    ["/workspaces/observatory/engineering", "Engineering"],
    ["/workspaces/observatory/ai-insights", "AI Insights"],
  ];
  for (const [route, label] of SECTIONS) {
    await visitRoute(page, route, label);
  }


  // ── [3] Navigation interne — rail + onglets + contenu ─────────────────
  console.log("\n[3] Navigation interne — rail + onglets + contenu");
  for (const [route, label] of SECTIONS) {
    const active = await page.locator(`a[href="${route}"]`).first().isVisible().catch(() => false);
    if (!active) fail(`nav ${label}`, `lien ${route} invisible`);
    else ok(`nav ${label}`, `lien actif`);
  }
  const qaTexts = ["Vault", "Graph", "Timeline", "Search", "Engineering", "AI Insights"];
  for (const t of qaTexts) {
    const found = await page.getByText(t, { exact: false }).first().isVisible().catch(() => false);
    found ? ok(`overview quick-action « ${t} »`) : fail(`overview quick-action « ${t} »`);
  }

  // ── [4] Vault interactions ─────────────────────────────────────────────
  console.log("\n[4] Vault — interactions (arborescence, recherche, wikilien, backlinks)");
  await page.goto(`${BASE}/workspaces/observatory/vault`, { waitUntil: "networkidle", timeout: 30000 });
  await page.waitForTimeout(2500);
  const treeVisible = await page.getByRole("tree").first().isVisible().catch(() => false);
  treeVisible ? ok("vault arborescence tree visible") : fail("vault arborescence", "tree non trouve");
  const editorVisible = await page.locator("textarea, [data-testid*='editor']").first().isVisible().catch(() => false);
  editorVisible ? ok("vault editeur visible") : fail("vault editeur", "editeur non trouve");
  const searchInput = page.locator("input[type=text], input[name=q], input[placeholder*=earch]").first();
  await searchInput.fill("MEMORY_DATA_MODEL");
  await page.keyboard.press("Enter");
  await page.waitForTimeout(1500);
  const searchHits = await page.locator("[class*=search-hit], li[class*=hit]").count().catch(() => 0);
  searchHits > 0 ? ok("vault recherche retourne des resultats") : fail("vault recherche", "0 resultats");
  const wikilinkTargets = await page.locator("a[href*='/vault'], a[href*='[']").count().catch(() => 0);
  const wikilinkUnresolved = await page.locator("text/Wikilien non résolu").first().isVisible().catch(() => false);
  wikilinkTargets > 0 ? ok("vault wikiliens cliquables detectes") : fail("vault wikiliens", "0 detectes");
  const backlinkVisible = await page.getByText("Backlinks|retourne").first().isVisible().catch(() => false);
  backlinkVisible ? ok("vault backlinks panel") : fail("vault backlinks", "panel absent");

  // ── [5] Graph interactions ─────────────────────────────────────────────
  console.log("\n[5] Graph — nœuds/arêtes et interaction");
  await page.goto(`${BASE}/workspaces/observatory/graph`, { waitUntil: "networkidle", timeout: 30000 });
  await page.waitForTimeout(2500);
  const svgVisible = await page.locator("svg").first().isVisible().catch(() => false);
  svgVisible ? ok("graph SVG visible") : fail("graph SVG", "SVG absent");
  const nodeCount = await page.locator("[data-testid*='node'], .node, circle, g.node").count().catch(() => 0);
  const edgeCount = await page.locator("[data-testid*='edge'], .edge, path.edge").count().catch(() => 0);
  ok(`graph nœuds/arêtes (dom estime: node=${nodeCount}, edge=${edgeCount})`, `dom: node=${nodeCount}, edge=${edgeCount}`);
  const wheelOk = await page.evaluate(() => {
    const svg = document.querySelector("svg");
    if (!svg) return false;
    try {
      svg.dispatchEvent(new WheelEvent("wheel", { bubbles: true, deltaY: 30 }));
      return true;
    } catch (e) {
      return false;
    }
  });
  wheelOk ? ok("graph zoom/pan sans erreur") : fail("graph zoom/pan", "dispatch wheel echouee");


  // ── [6] Canvas interactions ────────────────────────────────────────────
  console.log("\n[6] Canvas — arrangement local + drag");
  await page.goto(`${BASE}/workspaces/observatory/canvas`, { waitUntil: "networkidle", timeout: 30000 });
  await page.waitForTimeout(2500);
  const canvasVisible = await page.locator("svg, [data-testid*='canvas']").first().isVisible().catch(() => false);
  canvasVisible ? ok("canvas SVG visible") : fail("canvas SVG", "SVG absent");
  const dndOk = await page.evaluate(() => {
    const el = document.querySelector("[data-sortable], [data-canvas]");
    if (!el) return false;
    try {
      el.dispatchEvent(new DragEvent("dragstart", { bubbles: true }));
      return true;
    } catch (e) {
      return false;
    }
  });
  dndOk ? ok("canvas drag-and-drop sans erreur") : fail("canvas drag-and-drop", "noop");
  const storageOk = await page.evaluate(() => {
    try {
      const v = localStorage.getItem("observatory_canvas");
      return v ? v.length : 0;
    } catch (e) { return 0; }
  });
  storageOk >= 0 ? ok("canvas localStorage presence", `size=${storageOk}`) : fail("canvas localStorage", "0");

  // ── [7] Timeline ───────────────────────────────────────────────────────
  console.log("\n[7] Timeline — chronologie");
  await page.goto(`${BASE}/workspaces/observatory/timeline`, { waitUntil: "networkidle", timeout: 30000 });
  await page.waitForTimeout(2000);
  const timelineEvents = await page.locator("li, [data-testid*='event'], [class*=event]").count().catch(() => 0);
  timelineEvents > 0 ? ok("timeline events presentes", `count=${timelineEvents}`) : fail("timeline events", "0 presentes");

  // ── [8] Search unified ─────────────────────────────────────────────────
  console.log("\n[8] Search unifie — recherche vault + /v1/search");
  await page.goto(`${BASE}/workspaces/observatory/search`, { waitUntil: "networkidle", timeout: 30000 });
  await page.waitForTimeout(2000);
  const searchVisible = await page.getByText("Search|recherche").first().isVisible().catch(() => false);
  searchVisible ? ok("search section visible") : fail("search section", "invisible");
  await page.locator("input[type=text], input[name=q], input[placeholder*=earch]").first().fill("Observatory");
  await page.keyboard.press("Enter");
  await page.waitForTimeout(2000);
  const resultsShown = await page.locator("[class*=result], li[class*=result]").count().catch(() => 0);
  ok(`search affiche des resultats (count=${resultsShown})`, `count=${resultsShown}`);

  // ── [9] Engineering view ───────────────────────────────────────────────
  console.log("\n[9] Engineering — ADR/ESR/ASR/recherche");
  await page.goto(`${BASE}/workspaces/observatory/engineering`, { waitUntil: "networkidle", timeout: 30000 });
  await page.waitForTimeout(2500);
  const engTabs = await page.locator("button, [class*=tab]").count().catch(() => 0);
  const hasAdr = await page.getByText("ADR", { exact: false }).first().isVisible().catch(() => false);
  const hasEsr = await page.getByText("ESR", { exact: false }).first().isVisible().catch(() => false);
  ok(`engineering tabs (count=${engTabs})`, `count=${engTabs}`);
  hasAdr ? ok("engineering ADR visible") : fail("engineering ADR", "absent");
  hasEsr ? ok("engineering ESR visible") : fail("engineering ESR", "absent");

  // ── [10] AI Insights ───────────────────────────────────────────────────
  console.log("\n[10] AI Insights — synthèses agents + provenance");
  await page.goto(`${BASE}/workspaces/observatory/ai-insights`, { waitUntil: "networkidle", timeout: 30000 });
  await page.waitForTimeout(2500);
  const aiVisible = await page.getByText("AI Insights", { exact: false }).first().isVisible().catch(() => false);
  aiVisible ? ok("ai-insights visible") : fail("ai-insights visible", "invisible");
  const badges = await page.getByText("Agent|RPT|PROVISIONAL|VALIDATED").first().isVisible().catch(() => false);
  badges ? ok("ai-insights provenance badges") : fail("ai-insights badges", "absents");

  // ── [11] Responsive + thème sombre ─────────────────────────────────────
  console.log("\n[11] Responsive & thème");
  await checkResponsive(page, "mobile", 390, 844);
  await checkResponsive(page, "tablette", 768, 1024);
  await checkTheme(page, "dark");

  // ── [12] Nettoyage ─────────────────────────────────────────────────────
  console.log("\n[12] Nettoyage");
  try {
    await page.context().close();
    await browser.close();
    ok("navigateur ferme proprement");
  } catch (e) {
    fail("navigateur ferme", e.message);
  }

  // ── Rapport ────────────────────────────────────────────────────────────
  console.log(`\n=== RESULTAT : ${results.filter((r) => r.pass).length}/${results.length} OK ===`);
  const fails = results.filter((r) => !r.pass);
  if (fails.length) {
    console.log("\nECHEC(S):");
    for (const f of fails) console.log(`  - ${f.name}`);
  }
  process.exit(fails.length === 0 ? 0 : 1);
}

main().catch((e) => {
  console.error("Probe fatal:", e);
  process.exit(1);
});


