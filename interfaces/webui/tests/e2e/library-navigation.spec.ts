/**
 * Validation navigateur — Library Navigation (ETHAN WebUI).
 *
 * Couvre :
 *  - Desktop : ordre Workspaces (Library après DAĒNĀ), absence dans Knowledge,
 *    accès direct /library, libellé du header.
 *  - Sidebar réduite : icône Library, tooltip/libellé, navigation.
 *  - Mobile : ouverture du drawer, présence Library, navigation.
 *  - I18n : FR = Bibliothèque, EN = Library.
 *  - KnowledgeHub : aucun onglet Library, autres fonctionnalités préservées.
 *  - Ctrl+K : ouverture, recherche Library, résultat traduit, navigation /library,
 *    fermeture + reset de la recherche.
 *
 * Les identifiants du compte d'audit temporaire sont lus depuis
 * /tmp/opencode/obs-audit-creds.txt (jamais affichés dans le rapport).
 */
import { test, expect } from "@playwright/test";
import * as fs from "fs";
import * as path from "path";

const SCREEN_DIR = "/tmp/opencode/library-nav";
const CREDS_FILE = "/tmp/opencode/obs-audit-creds.txt";

const creds = fs.readFileSync(CREDS_FILE, "utf-8").trim().split(/\s+/);
const OPERATOR_ID = creds[0];
const PASSWORD = creds[1];

fs.mkdirSync(SCREEN_DIR, { recursive: true });

const collectedErrors: string[] = [];

test.describe.configure({ mode: "serial", timeout: 180_000 });

test("library navigation — full validation", async ({ page }) => {
  /* ── Collecte erreurs console + requêtes échouées ── */
  page.on("console", (msg) => {
    if (msg.type() === "error" || msg.type() === "warning") {
      collectedErrors.push(`CONSOLE ${msg.type().toUpperCase()}: ${msg.text()}`);
    }
  });
  page.on("requestfailed", (req) => {
    const f = req.failure();
    collectedErrors.push(
      `REQUEST FAILED: ${req.url()} — ${f ? f.errorText : "unknown"}`,
    );
  });
  page.on("response", (res) => {
    if (res.status() >= 400) {
      collectedErrors.push(`HTTP ${res.status()}: ${res.url()}`);
    }
  });

  async function snap(name: string) {
    await page.screenshot({
      path: path.join(SCREEN_DIR, `${name}.png`),
      fullPage: true,
    });
  }

  async function setLocale(locale: "fr" | "en") {
    await page.evaluate((loc) => {
      localStorage.setItem("ethan_locale_explicit", "1");
      localStorage.setItem("ethan_locale", loc);
      location.reload();
    }, locale);
    await page.waitForLoadState("domcontentloaded");
    await page.waitForTimeout(800);
  }

  async function login() {
    await page.goto("/login");
    await page.fill('input#operator-id', OPERATOR_ID);
    await page.fill('input#password', PASSWORD);
    await page.click('button[type="submit"]');
    await expect(page.locator("#sidebar")).toBeVisible({ timeout: 20000 });
  }

  /* ── Connexion compte d'audit ── */
  await login();
  const cookiesAfterLogin = await page.context().cookies();
  collectedErrors.push(
    "COOKIES après login: " +
      cookiesAfterLogin.map((c) => `${c.name}=${c.domain}:${c.path}`).join(" | "),
  );
  await snap("01-home-desktop-en");

  /* ── Desktop EN : ordre Workspaces (Library après DAĒNĀ) ── */
  const observatory = page.locator('a[href="/workspaces/observatory"]').first();
  const libraryLink = page.locator('a[href="/library"]').first();
  await expect(observatory).toBeVisible();
  await expect(libraryLink).toBeVisible();
  const obsBox = await observatory.boundingBox();
  const libBox = await libraryLink.boundingBox();
  expect(obsBox).toBeTruthy();
  expect(libBox).toBeTruthy();
  expect(libBox!.y).toBeGreaterThan(obsBox!.y); // Library sous DAĒNĀ

  /* Un seul lien /library dans la sidebar (pas de doublon, hors Knowledge) */
  await expect(page.locator('a[href="/library"]')).toHaveCount(1);
  await snap("02-desktop-en-workspaces-order");

  /* ── Accès direct /library + header libellé ── */
  await page.goto("/library");
  await expect(page).toHaveURL("/library", { timeout: 20000 });
  await expect(page.locator("text=Library").first()).toBeVisible({
    timeout: 10000,
  });
  await snap("03-library-page-en");

  /* ── Sidebar réduite : icône, tooltip, navigation ── */
  await page.goto("/");
  await page.locator(".sidebar-hamburger").first().click(); // replier
  const rail = page.locator('[data-testid="sidebar-collapsed-library"]').first();
  await expect(rail).toBeVisible();
  await expect(rail.locator("svg")).toBeVisible(); // icône Library
  await expect(rail).toHaveAttribute("title", "Library");
  await expect(rail).toHaveAttribute("aria-label", "Library");
  await rail.click();
  await expect(page).toHaveURL("/library", { timeout: 20000 });
  await snap("04-sidebar-reduite-library-en");

  /* ── Mobile : drawer, présence Library, navigation ── */
  await page.setViewportSize({ width: 375, height: 812 });
  await page.waitForTimeout(700);
  // En mobile replié (rail), le bouton d'ouverture du drawer est le logo.
  const openDrawer = page.locator('[aria-label="Ouvrir la sidebar"]').first();
  await expect(openDrawer).toBeVisible();
  await openDrawer.click();
  await expect(page.locator('a[href="/library"]')).toBeVisible();
  await page.locator('a[href="/library"]').first().click();
  await expect(page).toHaveURL("/library", { timeout: 20000 });
  await snap("05-mobile-library-en");

  /* Revenir en desktop (recharger pour état initial sidebar déployée) */
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.waitForTimeout(400);
  await page.goto("/");
  await expect(page.locator("#sidebar")).toBeVisible();

  /* ── I18n FR : Bibliothèque ── */
  await setLocale("fr");
  await page.goto("/");
  const frLib = page.locator('a[href="/library"]').first();
  await expect(frLib).toContainText("Bibliothèque");
  await snap("06-desktop-fr-bibliotheque");
  await frLib.click();
  await expect(page).toHaveURL("/library", { timeout: 20000 });
  await expect(page.locator("text=Bibliothèque").first()).toBeVisible({
    timeout: 10000,
  });
  await snap("07-library-page-fr");

  /* ── I18n EN : Library ── */
  await setLocale("en");
  await page.goto("/");
  await expect(page.locator('a[href="/library"]').first()).toContainText(
    "Library",
  );
  await snap("08-desktop-en-library");

  /* ── KnowledgeHub : aucun onglet Library dans le contenu, Knowledge préservé ── */
  await page.goto("/knowledge");
  await expect(page.locator('a[href="/knowledge"]')).toBeVisible();
  const totalLib = await page.locator('a[href="/library"]').count();
  const inSidebar = await page.locator('#sidebar a[href="/library"]').count();
  expect(totalLib).toBe(inSidebar); // Library confiné à la sidebar, pas d'onglet dans le hub
  await snap("09-knowledgehub-no-library");

  /* ── Ctrl+K : ouverture, recherche, résultat traduit, navigation, fermeture ── */
  await page.goto("/");
  await page.locator('[aria-label="Rechercher"]').first().click();
  const search = page.locator('input[placeholder*="command or search"]');
  await expect(search).toBeVisible();
  await snap("10-ctrlk-opened");

  await search.fill("library");
  await page.waitForTimeout(400);
  const result = page.locator('a[href="/library"]').first();
  await expect(result).toBeVisible();
  await expect(result).toContainText("Library"); // résultat traduit (EN)
  await snap("11-ctrlk-search-library");

  await result.click();
  await expect(page).toHaveURL("/library", { timeout: 20000 });
  // palette fermée après sélection
  await expect(search).not.toBeVisible();
  await snap("12-ctrlk-navigated-closed");

  /* Reset de la recherche à la fermeture : rouvrir, l'input doit être vide */
  await page.locator('[aria-label="Rechercher"]').first().click();
  await expect(search).toBeVisible();
  await expect(search).toHaveValue("");
  await page.keyboard.press("Escape"); // refermer proprement
  await expect(search).not.toBeVisible();
  await snap("13-ctrlk-reset-closed");

  /* ── Rapport erreurs console / réseau ── */
  fs.writeFileSync(
    path.join(SCREEN_DIR, "console-and-network-errors.txt"),
    collectedErrors.length > 0
      ? collectedErrors.join("\n")
      : "(aucune erreur console / requête échouée)",
  );
});
