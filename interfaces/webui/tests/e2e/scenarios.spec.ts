/**
 * E2E — Scénarios réels de bout en bout (authentifié).
 *
 * Remplace l'ancienne spec « Dashboard V2 » qui ciblait des routes disparues
 * (/goals, /memory/facts, /skills/lab). Chaque test suit un scénario
 * utilisateur réel contre le Core :
 *
 *  1–2. Créer un projet (Core /v1/projects) puis revenir au chat — le projet
 *       est activé par le Core et visible dans le contexte de conversation ;
 *  3–6. Knowledge expose la recherche du workspace (état vide concret).
 *
 * ⚠️ Le test de création écrit une donnée réelle (projet horodaté « E2E Smoke … »)
 * dans le Core de développement : c'est volontaire pour valider le parcours
 * complet, et réversible via le workspace Projects.
 */
import { test, expect } from "@playwright/test";
import { CREDENTIALS_MISSING, hasCredentials, login } from "./support/auth";

test.describe("Scénarios réels (authentifié)", () => {
  test.beforeEach(async ({ page }) => {
    test.skip(!hasCredentials(), CREDENTIALS_MISSING);
    await login(page);
  });

  test("scénarios 1–2 : créer un projet puis le retrouver dans le chat", async ({ page }) => {
    const name = `E2E Smoke ${Date.now()}`;

    await page.goto("/projects");
    await page.getByRole("button", { name: "New project" }).click();
    await page.fill("#new-project-name", name);
    await page.getByRole("button", { name: "Create", exact: true }).click();

    // Le Core crée le projet puis l'interface navigue vers son workspace.
    await expect(page).toHaveURL(/\/projects\/[^/]+$/);
    await expect(page.getByText(name).first()).toBeVisible();

    // Scénario 2 : le chat s'ouvre avec le projet actif comme contexte.
    await page.goto("/");
    await expect(page.getByPlaceholder("Message ETHAN...")).toBeVisible();
    await expect(page.getByText(name).first()).toBeVisible();
  });

  test("scénario 3–6 : Knowledge expose la recherche du workspace", async ({ page }) => {
    await page.goto("/knowledge");
    await expect(page.getByPlaceholder("Rechercher (tout le workspace)…")).toBeVisible();
  });
});
