/**
 * E2E — Model Hub (parcours authentifié : login → Discover → recherche).
 *
 * Valide le rendu RÉEL de la page /models contre l'API ETHAN :
 *   - le sélecteur source expose l'alias « local » du catalogue (D7) ;
 *   - une recherche catalogue affiche bien ses résultats — régression du bug
 *     « filteredResults non rendu » ;
 *   - aucun mock : les données viennent du Core via l'API (source de vérité).
 *
 * Tourne contre le serveur Playwright (webServer réutilise un serveur déjà
 * présent sur 3001 — ex. le conteneur ethan-ui).
 */
import { test, expect } from "@playwright/test";

const OPERATOR_ID = process.env.ETHAN_SMOKE_USER || "ethan-smoke";
const PASSWORD = process.env.ETHAN_SMOKE_PASSWORD || "smoke-ethan-2026";

test.describe("Model Hub — Discover (live Core API)", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
    await page.fill("#operator-id", OPERATOR_ID);
    await page.fill("#password", PASSWORD);
    await page.click('button[type="submit"]');
    await expect(page).not.toHaveURL(/\/login/);
  });

  test("le sélecteur source expose l'alias local du catalogue", async ({ page }) => {
    await page.goto("/models");
    await page.getByRole("button", { name: /Discover/ }).click();

    const sourceSelect = page.getByLabel("Filtrer par source");
    await expect(sourceSelect).toBeVisible();
    await expect(sourceSelect.locator('option[value="local"]')).toHaveCount(1);
    await expect(sourceSelect.locator('option[value="huggingface"]')).toHaveCount(1);
  });

  test("une recherche catalogue affiche ses résultats rendus par le Core", async ({ page }) => {
    await page.goto("/models");
    await page.getByRole("button", { name: /Discover/ }).click();

    await page.getByPlaceholder(/Rechercher un modèle/).fill("qwen");
    // Scope sur la search bar du Hub : la sidebar possède aussi un bouton
    // « Rechercher » (Ctrl+K) qui viole le strict mode.
    const searchBar = page
      .getByPlaceholder(/Rechercher un modèle/)
      .locator("xpath=ancestor::div[contains(@class,'gap-2')][1]");
    await searchBar.getByRole("button", { name: "Rechercher" }).click();

    // Le modèle du catalogue local « qwen » doit être rendu (filteredResults).
    await expect(page.getByText(/Qwen/i).first()).toBeVisible({ timeout: 15_000 });
  });
});