# E2E — ETHAN WebUI (Playwright)

Suite Playwright alignée sur l'application réelle (nav-config v5, Settings
groupés, chat assistant-first). Elle remplace l'ancienne génération de specs
qui ciblait des routes supprimées (`/flux`, `/memory`, `/config`, `/goals`,
`/skills/lab`).

## Fichiers

| Spec | Portée | Identifiants requis |
|------|--------|---------------------|
| `login.spec.ts` | Formulaire de connexion + redirection middleware (`redirect`), soumission vide | Non (public) |
| `app.spec.ts` | Shell : Assistants/Pilotage déployés, Administration repliée par défaut + dépliage (clic et navigation), palette Ctrl+K | Oui |
| `chat.spec.ts` | Composer « Message ETHAN... », retour au chat depuis un workspace | Oui |
| `dashboard.spec.ts` | Settings : recherche de section (filtre, état vide, restauration), accès `#rag`, lien Skills réel | Oui |
| `scenarios.spec.ts` | Scénario 1–2 : créer un projet puis le retrouver dans le chat ; Knowledge : recherche workspace | Oui |
| `support/auth.ts` | Helper `login()` + skip propre sans identifiants | — |

Les specs authentifiées sont **skippées** (pas échouées) quand les
identifiants ne sont pas fournis.

## Exécution

```bash
cd interfaces/webui

# Parcours publics uniquement (aucun compte nécessaire) :
npx playwright test tests/e2e/login.spec.ts

# Suite complète, avec un compte réel du Core de développement :
ETHAN_E2E_EMAIL=operator ETHAN_E2E_PASSWORD='…' npx playwright test
```

- Aucune valeur par défaut, aucun secret commité (règle « secret » du repo) :
  les identifiants viennent uniquement de l'environnement.
- Le compte E2E se crée via l'API réelle : `POST /auth/register` (le mot de passe
  ne vit que dans l'environnement de la session de test).
- `playwright.config.ts` démarre `npm run dev` sur le port 3001 et **réutilise
  un serveur déjà lancé** (`reuseExistingServer` hors CI). Pour cibler une
  autre instance : `ETHAN_WEBUI_URL=https://… npx playwright test`.
- `scenarios.spec.ts` crée un projet réel horodaté (« E2E Smoke … ») pour
  valider le parcours complet jusqu'au Core, puis le **supprime lui-même**
  (`DELETE /v1/projects/{id}` ; repli par nom si l'échec survient avant la
  navigation) — aucun résidu laissé dans le Core de dev.

## Conventions

- Sélecteurs ancrés sur le code réel : ids (`#operator-id`, `#password`,
  `#new-project-name`), rôles ARIA (`getByRole`), placeholders exacts et
  `aria-expanded` des en-têtes de sidebar (`.sidebar-nav-section-header`).
- Aucun sélecteur de mise en page fragile (classes utilitaires Tailwind) :
  l'E2E valide des comportements, les tests unitaires (jest/jsdom) valident le
  rendu détaillé.
- **Hydratation (mode dev)** : React peut s'hydrater après le premier
  `fill`/raccourci clavier — un champ contrôlé serait réinitialisé et le submit
  ne partirait jamais. Utiliser `fillStable()` (`support/auth.ts`) pour tout
  champ contrôlé, et réessayer les raccourcis clavier (cf. Ctrl+K dans
  `app.spec.ts`).
- **Listes Core asynchrones** : attendre les options (`expect.poll` sur
  `[role="option"]`) avant de compter, sinon un skip « aucun modèle/agent »
  peut être prononcé à tort pendant le chargement.
- **Budgets** : `expect` global à 10 s (`playwright.config.ts`) et 15 s pour la
  navigation post-création de projet — la compilation Next à froid en dev peut
  dépasser les 5 s par défaut.
