/**
 * probe-e2e.mjs — Validation navigateur REELLE de la WebUI ETHAN (v5).
 *
 * Contrairement aux specs tests/e2e/*.spec.ts (juillet 2026, derivees de la
 * v2/v3 — selecteurs et routes disparus), ce probe :
 *   1. cree un compte de probe via /auth/register (public, source de verite DB) ;
 *   2. se connecte via le VRAI formulaire (#operator-id / #password) ;
 *   3. visite chaque route reellement servie par src/app ;
 *   4. capture erreurs console, exceptions page et requetes reseau echouees.
 *
 * Zero logique metier ici : pur outil de validation d'interface.
 * Usage : node probe-e2e.mjs [baseWebUI]  (defaut http://localhost:3001)
 */
import { chromium } from "playwright";

const BASE = process.argv[2] || "http://localhost:3001";
const API = process.env.ETHAN_API_URL || "http://localhost:8000";
const PROBE_USER = `e2e_probe_${Date.now().toString(36)}`;
const PROBE_PASS = "Probe-Only-Passw0rd!";

// Routes reellement servies (find src/app -name page.tsx), hors (auth).
const ROUTES = [
  "/", "/agents", "/missions", "/calendar", "/notes", "/inbox",
  "/research", "/cookbook", "/knowledge", "/skills", "/tools",
  "/providers", "/connections", "/diagnostics", "/settings", "/models",
  "/plugins", "/mcp", "/security", "/logs", "/monitoring",
];

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

export function collectPageDiagnostics(page) {
  const consoleErrors = [];
  const pageErrors = [];
  const failedReqs = [];
  const onConsole = (m) => { if (m.type() === "error") consoleErrors.push(m.text()); };
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

async function visitRoute(page, route) {
  const diag = collectPageDiagnostics(page);
  try {
    const resp = await page.goto(`${BASE}${route}`, {
      waitUntil: "domcontentloaded",
      timeout: 20000,
    });
    // Laisse l'hydratation React + fetch initiaux se terminer.
    await page.waitForLoadState("networkidle", { timeout: 15000 }).catch(() => {});
    const status = resp ? resp.status() : 0;
    const contentLen = (await page.content()).length;
    // Critere de rendu robuste : <main> visible OU items de sidebar rendus.
    // (un union-css attraperait un body>div portal invisible → faux negatif)
    const mainVisible = await page
      .locator("main")
      .first()
      .isVisible()
      .catch(() => false);
    const navItems = await page.locator(".sidebar-nav-item").count().catch(() => 0);
    const rootHasContent = mainVisible || navItems > 0;
    const boundary = await page
      .getByText(/Application error|Something went wrong/i)
      .first()
      .isVisible()
      .catch(() => false);

    const realErrors = diag.consoleErrors.filter(
      (t) => !/favicon|Download the React DevTools|sourcemap/i.test(t),
    );
    const netFails = diag.failedReqs.filter((u) => !/favicon/.test(u));

    if (status >= 400 || !rootHasContent || boundary) {
      fail(route, `HTTP ${status}, content=${contentLen}, boundary=${boundary}`);
    } else {
      ok(
        route,
        `HTTP ${status}, content=${contentLen}o` +
          (realErrors.length ? ` | ${realErrors.length} err console` : "") +
          (netFails.length ? ` | ${netFails.length} req echouees` : ""),
      );
    }
    const authDenied = netFails.filter((u) => u.includes("403"));
    if (authDenied.length) console.log(`         · info RBAC: ${authDenied.length} requete(s) 403 (role standard, attendu)`);
    for (const t of realErrors.slice(0, 3)) console.log(`         · console: ${t.slice(0, 140)}`);
    for (const u of netFails.slice(0, 3)) console.log(`         · reseau:  ${u.slice(0, 140)}`);
    for (const t of diag.pageErrors.slice(0, 3)) console.log(`         · page:    ${t.slice(0, 140)}`);
  } catch (e) {
    fail(route, e.message.split("\n")[0]);
  } finally {
    diag.stop();
  }
}

async function main() {
  console.log(`WebUI=${BASE}  API=${API}\n`);
  await registerProbeUser();

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  // ── [2] Page de login : le formulaire reel ─────────────────────────────
  console.log("\n[2] Page de login (formulaire reel v5)");
  await page.goto(`${BASE}/login`, { waitUntil: "networkidle", timeout: 30000 });
  for (const sel of ["#operator-id", "#password", "button[type=submit]"]) {
    const visible = await page.locator(sel).first().isVisible().catch(() => false);
    visible ? ok(`login: ${sel} visible`) : fail(`login: ${sel} visible`);
  }

  // ── [3] Login reel via le formulaire ───────────────────────────────────
  console.log("\n[3] Login reel (cookie ethan_token via proxy /api)");
  await page.fill("#operator-id", PROBE_USER);
  await page.fill("#password", PROBE_PASS);
  // Diagnostic : trace l' appel reseau du login
  page.on("response", (r) => {
    if (r.url().includes("/api/auth/login")) {
      console.log(`         · POST ${r.url()} → ${r.status()}`);
    }
  });
  await page.click("button[type=submit]");
  try {
    await page.waitForURL((u) => !u.pathname.includes("/login"), { timeout: 30000 });
    const cookies = await context.cookies();
    const token = cookies.find((c) => c.name === "ethan_token");
    if (token) ok(`login effectue → ${page.url()} (cookie ethan_token present)`);
    else fail("cookie ethan_token absent apres login");
  } catch (e) {
    fail(`login par formulaire: ${e.message.split("\n")[0]}`);
    console.log(`         · URL finale: ${page.url()}`);
    const errText = await page
      .locator("[class*=error], [role=alert]")
      .allTextContents()
      .catch(() => []);
    if (errText.length) console.log(`         · erreur affichee: ${errText.join(" | ").slice(0, 200)}`);
    await page.screenshot({ path: "/tmp/login-fail.png", fullPage: true });
    console.log("         · screenshot: /tmp/login-fail.png");
    await browser.close();
    process.exit(1);
  }

  // ── [4] Visite de chaque route servie ──────────────────────────────────
  console.log("\n[4] Routes servies — rendu + erreurs");
  for (const route of ROUTES) {
    await visitRoute(page, route);
  }

  // ── [5] Sidebar reelle (labels de nav-config) ──────────────────────────
  console.log("\n[5] Sidebar v5 (nav-config reel)");
  await page.goto(`${BASE}/agents`, { waitUntil: "networkidle", timeout: 20000 }).catch(() => {});
  for (const label of ["Agents", "Missions", "Calendar", "Notes", "Inbox"]) {
    const found = await page
      .locator(`.sidebar-nav-item:has-text("${label}"), a:has-text("${label}")`)
      .first()
      .isVisible()
      .catch(() => false);
    found ? ok(`sidebar: « ${label} »`) : fail(`sidebar: « ${label} »`);
  }

  await browser.close();

  const passed = results.filter((r) => r.pass).length;
  const total = results.length;
  console.log(`\n${"=".repeat(70)}`);
  console.log(`RESULTAT : ${passed} OK / ${total - passed} ECHEC(S)  (${total} verifications)`);
  console.log("=".repeat(70));
  process.exit(passed === total ? 0 : 1);
}

main().catch((e) => {
  console.error("Probe fatal:", e);
  process.exit(1);
});
