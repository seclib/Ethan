/**
 * E2E — Login (parcours PUBLIC, exécutable sans identifiants).
 *
 * Page réelle : src/app/(auth)/login/components/login-form.tsx
 *   - #operator-id (texte) · #password · button[type="submit"]
 * Middleware réel : src/middleware.ts (redirection + paramètre `redirect`).
 *
 * Ces tests tournent contre le serveur de la config Playwright
 * (`webServer: npm run dev`, port 3001) et ne requièrent AUCUN compte.
 */
import { test, expect } from "@playwright/test";

test.describe("Login — accès et formulaire", () => {
  test("la page de connexion expose le formulaire réel", async ({ page }) => {
    await page.goto("/login");
    await expect(page.locator("#operator-id")).toBeVisible();
    await expect(page.locator("#password")).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
    await expect(page.getByText("Operator ID")).toBeVisible();
  });

  test("une route protégée redirige vers /login en conservant la cible", async ({ page }) => {
    await page.goto("/settings");
    await expect(page).toHaveURL(/\/login\?redirect=%2Fsettings/);
  });

  test("soumission vide : l'utilisateur reste sur /login", async ({ page }) => {
    await page.goto("/login");
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/\/login/);
  });
});
