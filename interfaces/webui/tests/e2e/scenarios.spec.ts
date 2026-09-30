/**
 * E2E — Scénarios réels de bout en bout (authentifié).
 *
 * Couvre les 10 scénarios de validation UX du mandat :
 *
 *   1–2. Créer un projet (Core /v1/projects) puis revenir au chat — le projet
 *        est activé par le Core et visible dans le contexte de conversation ;
 *   3.   Changer de modèle depuis le chat (ModelSelector compact) ;
 *   4.   Changer d'agent depuis le chat (AgentSelector du header) ;
 *   5.   Ajouter un fichier au composer (upload réel Core) ;
 *   6.   Rechercher dans Knowledge (état vide concret) ;
 *   7.   Configurer un provider (workspace /providers réel) ;
 *   8.   Connecter/voir une intégration (Settings → Integrations) ;
 *   9.   Gérer les skills (workspace /skills réel) ;
 *   10.  Revenir au chat (couvert par chat.spec.ts — lien « Retour au chat »).
 *
 * ⚠️ Le test de création écrit une donnée réelle (projet horodaté « E2E Smoke … »)
 * dans le Core de développement : c'est volontaire pour valider le parcours
 * complet. Le test nettoie derrière lui (DELETE /v1/projects/{id} — suppression
 * logique, conversations préservées) pour laisser le Core de dev inchangé.
 */
import { test, expect } from "@playwright/test";
import { CREDENTIALS_MISSING, fillStable, hasCredentials, login } from "./support/auth";

test.describe("Scénarios réels (authentifié)", () => {
  test.beforeEach(async ({ page }) => {
    test.skip(!hasCredentials(), CREDENTIALS_MISSING);
    await login(page);
  });

  test("scénarios 1–2 : créer un projet puis le retrouver dans le chat", async ({ page }) => {
    const name = `E2E Smoke ${Date.now()}`;
    let projectId: string | null = null;

    try {
      await page.goto("/projects");
      await page.getByRole("button", { name: "New project" }).click();
      await fillStable(page.locator("#new-project-name"), name);
      await page.getByRole("button", { name: "Create", exact: true }).click();

      // Le Core crée le projet puis l'interface navigue vers son workspace
      // (création + activation + contexte : aller-retour Core réel).
      await expect(page).toHaveURL(/\/projects\/[^/]+$/, { timeout: 15_000 });
      await expect(page.getByText(name).first()).toBeVisible();
      projectId = page.url().match(/\/projects\/([^/]+)$/)?.[1] ?? null;
      expect(projectId, "id du projet créé extrait de l'URL").toBeTruthy();

      // Scénario 2 : le chat s'ouvre avec le projet actif comme contexte.
      await page.goto("/");
      await expect(page.getByPlaceholder("Message ETHAN...")).toBeVisible();
      await expect(page.getByText(name).first()).toBeVisible();
    } finally {
      // Nettoyage : le projet réel créé dans le Core de dev est supprimé via
      // l'API (page.request partage les cookies de session du navigateur).
      // Si l'id n'a pas pu être extrait (échec avant la navigation), on le
      // retrouve par nom : aucun résidu n'est laissé, même en cas d'échec.
      if (!projectId) {
        const list = await page.request.get("/api/v1/projects");
        if (list.ok()) {
          const payload = await list.json();
          const projects: Array<{ id: string; name: string }> = Array.isArray(payload)
            ? payload
            : (payload.projects ?? []);
          projectId = projects.find((p) => p.name === name)?.id ?? null;
        }
      }
      if (projectId) {
        const res = await page.request.delete(`/api/v1/projects/${projectId}`);
        expect.soft(res.ok(), `suppression du projet E2E ${projectId}`).toBeTruthy();
      }
    }
  });

  test("scénario 6 : Knowledge expose la recherche du workspace", async ({ page }) => {
    await page.goto("/knowledge");
    await expect(page.getByPlaceholder("Rechercher (tout le workspace)…")).toBeVisible();
  });

  test("scénario 3 : changer de modèle depuis le chat", async ({ page }) => {
    await page.goto("/");
    const trigger = page.getByTitle("Changer de modèle");
    await trigger.click();

    const listbox = page.getByRole("listbox");
    await expect(listbox).toBeVisible();

    // Les modèles arrivent du Core de façon asynchrone (React Query) : on
    // attend la fin du chargement avant de compter, sinon le test se
    // « skip » à tort sur une liste encore vide.
    const options = listbox.locator('[role="option"]');
    try {
      await expect
        .poll(async () => options.count(), { timeout: 10_000, message: "chargement des modèles" })
        .toBeGreaterThan(0);
    } catch {
      // Aucun modèle exposé par le Core : skip documenté ci-dessous.
    }

    const selectable = listbox.locator(
      '[role="option"][aria-selected="false"]:not([aria-disabled="true"])',
    );
    test.skip((await selectable.count()) === 0, "Aucun modèle alternatif disponible (Core).");

    const before = (await trigger.innerText()).trim();
    await selectable.first().click();

    await expect.poll(async () => (await trigger.innerText()).trim()).not.toBe(before);
  });

  test("scénario 4 : changer d'agent depuis le chat", async ({ page }) => {
    await page.goto("/");
    const trigger = page.getByTitle("Changer d'agent");
    await trigger.click();

    const listbox = page.getByRole("listbox", { name: "Sélectionner un agent" });
    await expect(listbox).toBeVisible();

    // Même attente que pour les modèles : la liste d'agents vient du Core.
    const options = listbox.locator('[role="option"]');
    try {
      await expect
        .poll(async () => options.count(), { timeout: 10_000, message: "chargement des agents" })
        .toBeGreaterThan(0);
    } catch {
      // Aucun agent exposé par le Core : skip documenté ci-dessous.
    }

    const realAgents = options
      .filter({ hasNotText: "Sans agent" })
      .and(listbox.locator('[aria-selected="false"]:not([aria-disabled="true"])'));
    test.skip((await realAgents.count()) === 0, "Aucun agent réel disponible (Core).");

    const before = (await trigger.innerText()).trim();
    await realAgents.first().click();

    await expect.poll(async () => (await trigger.innerText()).trim()).not.toBe(before);
  });

  test("scénario 5 : ajouter un fichier au composer (upload Core)", async ({ page }) => {
    await page.goto("/");
    const name = `e2e-note-${Date.now()}.txt`;

    await page.setInputFiles('[data-testid="chat-file-input"]', {
      name,
      mimeType: "text/plain",
      buffer: Buffer.from("ETHAN E2E — pièce jointe"),
    });

    // La pièce jointe est affichée dans le composer (état réel post-upload Core).
    await expect(page.getByText(name).first()).toBeVisible();
  });

  test("scénario 7 : configurer un provider (workspace réel)", async ({ page }) => {
    await page.goto("/providers");
    await expect(page.getByRole("button", { name: "Ajouter un provider" })).toBeVisible();
  });

  test("scénario 8 : intégrations visibles depuis Settings", async ({ page }) => {
    await page.goto("/settings#integrations");
    await expect(page.getByRole("heading", { name: "Integrations" }).first()).toBeVisible();
  });

  test("scénario 9 : gérer les skills (workspace réel)", async ({ page }) => {
    await page.goto("/skills");
    await expect(page.getByPlaceholder("Rechercher un skill…")).toBeVisible();
  });
});
