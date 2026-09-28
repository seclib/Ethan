/**
 * E2E — Settings workspace (authentifié).
 *
 * Réaligne la spec sur la refonte Settings : navigation groupée (8 groupes),
 * recherche de section (état mort câblé en Phase 5), accès direct par hash,
 * et absence de lien fantôme sur le workspace Skills.
 */
import { test, expect } from "@playwright/test";
import { CREDENTIALS_MISSING, hasCredentials, login } from "./support/auth";

test.describe("Settings — navigation guidée (authentifié)", () => {
  test.beforeEach(async ({ page }) => {
    test.skip(!hasCredentials(), CREDENTIALS_MISSING);
    await login(page);
  });

  test("recherche de section : filtre, état vide, restauration", async ({ page }) => {
    await page.goto("/settings");
    const search = page.getByRole("textbox", { name: "Rechercher une section Settings" });
    await expect(search).toBeVisible();
    await expect(page.getByRole("button", { name: "Appearance" })).toBeVisible();

    await search.fill("rag");
    await expect(page.getByRole("button", { name: "RAG" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Appearance" })).toHaveCount(0);

    await search.fill("zzzz");
    await expect(page.getByText("Aucune section ne correspond")).toBeVisible();

    await search.fill("");
    await expect(page.getByRole("button", { name: "Appearance" })).toBeVisible();
    await expect(page.getByRole("button", { name: "RAG" })).toBeVisible();
  });

  test("accès direct par hash : /settings#rag ouvre la configuration du moteur", async ({ page }) => {
    await page.goto("/settings#rag");
    await expect(
      page.getByText("Configuration du moteur d'ingestion et de récupération"),
    ).toBeVisible();
  });

  test("Settings → Skills pointe un workspace réel (aucun lien fantôme)", async ({ page }) => {
    await page.goto("/settings#skills");
    const link = page.getByRole("link", { name: "Ouvrir le workspace Skills" });
    await expect(link).toBeVisible();
    await expect(link).toHaveAttribute("href", "/skills");
  });
});
