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
import { expect, type Locator, type Page } from "@playwright/test";

const E2E_EMAIL = process.env.ETHAN_E2E_EMAIL;
const E2E_PASSWORD = process.env.ETHAN_E2E_PASSWORD;

export const CREDENTIALS_MISSING =
  "Spec authentifiée : définir ETHAN_E2E_EMAIL + ETHAN_E2E_PASSWORD (cf. tests/e2e/README.md).";

export function hasCredentials(): boolean {
  return Boolean(E2E_EMAIL && E2E_PASSWORD);
}

/**
 * Remplit un champ CONTRÔLÉ par React de façon fiable, même en mode dev :
 * React peut s'hydrater après le premier `fill` et réinitialiser la valeur.
 * On réessaie tant que la valeur ne tient pas (course d'hydratation).
 */
export async function fillStable(locator: Locator, value: string): Promise<void> {
  await expect(async () => {
    await locator.fill(value);
    await expect(locator).toHaveValue(value, { timeout: 1_000 });
  }).toPass({ timeout: 30_000 });
}

/**
 * Connexion réelle via le formulaire /login.
 * Champs réels : #operator-id (texte) et #password (login-form.tsx).
 * Après authentification, le shell charge la navigation : on attend un
 * marqueur de sidebar (et non un simple changement d'URL) pour éviter les
 * assertions sur une page encore vide.
 *
 * Fiabilité (vérifié en exécution réelle, 2026-09-30) :
 * - en mode dev, React peut s'hydrater APRÈS le premier `fill` : les champs
 *   contrôlés sont alors réinitialisés à "" et le submit ne produit AUCUN
 *   POST /api/auth/login (course d'hydratation) — d'où `fillStable`.
 * - l'overlay d'auth anime ~6 s (AUTH_STEPS) + compilation Next à froid :
 *   le budget de navigation est généreux (45 s).
 */
export async function login(page: Page): Promise<void> {
  await page.goto("/login");
  await page.waitForLoadState("load");

  await fillStable(page.locator("#operator-id"), E2E_EMAIL ?? "");
  await fillStable(page.locator("#password"), E2E_PASSWORD ?? "");

  await page.click('button[type="submit"]');
  // Redirection pleine : window.location.replace("/") après l'overlay d'auth.
  await page.waitForURL((url) => !url.pathname.startsWith("/login"), { timeout: 45_000 });
  await expect(page.locator(".sidebar-nav-section-header").first()).toBeVisible();
}
