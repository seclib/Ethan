/**
 * Support E2E — authentification.
 *
 * L'application est protégée par le middleware Next.js (cookie HttpOnly
 * `ethan_token`) : tout parcours hors /login et /register exige une session
 * réelle. Les specs authentifiées utilisent ce helper et sont SKIPPÉES
 * proprement quand les identifiants ne sont pas fournis — aucun secret par
 * défaut, rien de commité (règle « secret » du repo).
 *
 * Exécution :
 *   ETHAN_E2E_EMAIL=operator ETHAN_E2E_PASSWORD=… npx playwright test
 *   (cf. tests/e2e/README.md)
 */
import { expect, type Page } from "@playwright/test";

const E2E_EMAIL = process.env.ETHAN_E2E_EMAIL;
const E2E_PASSWORD = process.env.ETHAN_E2E_PASSWORD;

export const CREDENTIALS_MISSING =
  "Spec authentifiée : définir ETHAN_E2E_EMAIL + ETHAN_E2E_PASSWORD (cf. tests/e2e/README.md).";

export function hasCredentials(): boolean {
  return Boolean(E2E_EMAIL && E2E_PASSWORD);
}

/**
 * Connexion réelle via le formulaire /login.
 * Champs réels : #operator-id (texte) et #password (login-form.tsx).
 * Après authentification, le shell charge la navigation : on attend un
 * marqueur de sidebar (et non un simple changement d'URL) pour éviter les
 * assertions sur une page encore vide.
 */
export async function login(page: Page): Promise<void> {
  await page.goto("/login");
  await page.fill("#operator-id", E2E_EMAIL ?? "");
  await page.fill("#password", E2E_PASSWORD ?? "");
  await page.click('button[type="submit"]');
  // Redirection pleine : window.location.replace("/") après l'overlay d'auth.
  await page.waitForURL((url) => !url.pathname.startsWith("/login"), { timeout: 30_000 });
  await expect(page.locator(".sidebar-nav-section-header").first()).toBeVisible();
}
