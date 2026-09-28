/**
 * E2E — Chat (authentifié).
 *
 * Composer réel : textarea « Message ETHAN... » (assistant-input.tsx).
 * Scénario 10 : revenir au chat depuis un workspace via le logo du header
 * (app-header.tsx — lien accessible « Retour au chat »).
 */
import { test, expect } from "@playwright/test";
import { CREDENTIALS_MISSING, hasCredentials, login } from "./support/auth";

test.describe("Chat — composer et retour au chat", () => {
  test.beforeEach(async ({ page }) => {
    test.skip(!hasCredentials(), CREDENTIALS_MISSING);
    await login(page);
  });

  test("le chat expose le composer ETHAN", async ({ page }) => {
    await expect(page.getByPlaceholder("Message ETHAN...")).toBeVisible();
  });

  test("scénario 10 : revenir au chat depuis un workspace", async ({ page }) => {
    await page.goto("/projects");
    await page.getByRole("link", { name: "Retour au chat" }).click();
    await expect(page).toHaveURL(/\/$/);
    await expect(page.getByPlaceholder("Message ETHAN...")).toBeVisible();
  });
});
