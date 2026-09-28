/**
 * E2E — Shell (sidebar + palette), aligné sur nav-config v5.
 *
 * Contrats vérifiés :
 *  - « assistant-first » : Assistants et Pilotage sont déployés ;
 *  - Administration est REPLIÉE au premier rendu (NavSection.defaultCollapsed),
 *    se déplie au clic et s'ouvre automatiquement si on navigue dans le groupe ;
 *  - Ctrl+K ouvre la palette de commandes (input global réel).
 *
 * Specs authentifiées : skippées sans ETHAN_E2E_EMAIL/ETHAN_E2E_PASSWORD.
 */
import { test, expect, type Page } from "@playwright/test";
import { CREDENTIALS_MISSING, hasCredentials, login } from "./support/auth";

function adminHeader(page: Page) {
  return page.locator(".sidebar-nav-section-header", { hasText: "Administration" });
}

test.describe("Shell — sidebar (authentifié)", () => {
  test.beforeEach(async ({ page }) => {
    test.skip(!hasCredentials(), CREDENTIALS_MISSING);
    await login(page);
  });

  test("Assistants et Pilotage sont déployés, Administration est repliée", async ({ page }) => {
    await expect(page.locator('a[href="/agents"]')).toBeVisible();
    await expect(page.locator('a[href="/missions"]')).toBeVisible();
    await expect(adminHeader(page)).toHaveAttribute("aria-expanded", "false");
    await expect(page.locator('a[href="/diagnostics"]')).toBeHidden();
  });

  test("un clic déplie l'Administration, un second la replie", async ({ page }) => {
    await adminHeader(page).click();
    await expect(adminHeader(page)).toHaveAttribute("aria-expanded", "true");
    await expect(page.locator('a[href="/diagnostics"]')).toBeVisible();

    await adminHeader(page).click();
    await expect(adminHeader(page)).toHaveAttribute("aria-expanded", "false");
    await expect(page.locator('a[href="/diagnostics"]')).toBeHidden();
  });

  test("naviguer dans le groupe Administration le déplie automatiquement", async ({ page }) => {
    await page.goto("/diagnostics");
    await expect(adminHeader(page)).toHaveAttribute("aria-expanded", "true");
  });

  test("Ctrl+K ouvre la palette de commandes", async ({ page }) => {
    await page.keyboard.press("Control+k");
    await expect(page.getByPlaceholder("Type a command or search...")).toBeVisible();
  });
});
