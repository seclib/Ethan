# ETHAN — Qualification WebUI & Docker Runtime (Mission 9)

Date : 2026-11-04
Statut : QUALIFICATION RÉELLE (browser + API), Docker non destructif
Chemin demandé : `Obsidian/Architecture/Applications/ETHAN_WEBUI_DOCKER_QUALIFICATION.md`

## 1. Environnement

- API Docker : `ethan-api`, Up healthy, port `8000`.
- WebUI Docker : `ethan-ui`, Up healthy, port `3001`.
- NATS/Postgres/Redis : conteneurs Up.
- Odin controller : Up.
- Rust binaries : présents (`ethan-health`, `ethan-capability-contract`).

## 2. Playwright

- Dépendance déjà déclarée dans `interfaces/webui/package.json` (`@playwright/test`).
- Navigateur Chromium téléchargé dans le cache local (`~/.cache/ms-playwright`).
- Aucune dépendance globale ajoutée.
- Commande : `ETHAN_WEBUI_URL=http://127.0.0.1:3001 ETHAN_E2E_EMAIL=... ETHAN_E2E_PASSWORD=... npx playwright test --project=chromium`.

## 3. Tests navigateur exécutés

1. `npx playwright test tests/e2e/login.spec.ts` : 3/3 réussis.
2. `npx playwright test --project=chromium` (suite complète) : **20 passed, 1 failed, 1 skipped**, durée 44 s.
   - Échec : `app.spec.ts` "Ctrl+K ouvre la palette de commandes" (sélecteur non trouvé).
   - Aucun échec sur l'authentification ni les parcours majeurs authentifiés.

Statut WebUI : `PARTIALLY_VALIDATED`

## 4. Qualification Docker

Non destructif uniquement :
- inspecté `docker ps` ;
- inspecté routes OpenAPI réelles ;
- testé appels API avec et sans authentification ;
- pas d'install/start/stop/remove d'application.

Statut Docker lifecycle application : `NOT_TESTED` dans cette mission.

## 5. ODIN / Frames (réel)

- API `/v1/plugins/odin/status` : service présent, état `not_installed`, action `install`.
- API `/v1/plugins/frame/status` : service présent, état `not_installed`.
- Aucun démarrage de conteneur applicatif effectué.

Statut : `PARTIALLY_VALIDATED`

## 6. Quantar (réel)

- API `/v1/quantar/status` : `task_runtime=real-task`, `runtime=ready` après correction.
- Résultat en image actuelle : in-process indisponible (`tradingagents` absent), mais runtime Docker disponible.
- Aucune tâche contrôle réel à cause de l'absence de tradingagents dans l'environnement testé.

Statut : `PARTIALLY_VALIDATED`

## 7. Parcours réels réalisés

- login WebUI : succès
- shell authentifié chargé : succès
- appels API protégés sans token : 401 démontré
- ODIN status / Frames status / Quantar status : JSON cohérent avec token
- Rust Health : validé au niveau façade Python

## 8. Anomalies

1. `:npx` warning `npmrc` inoffensif.
2. Playwright exige browser install (fait, cache local).
3. Échec command palette (un sélecteur DOM probablement couplé à l'animation/overlay).
4. Route `/v1/health/rust` absente selon OpenAPI de l'image déployée.

## 9. Preuves

- `npx playwright test tests/e2e/login.spec.ts` : 3 passed
- suite e2e : 20 passed, 1 failed, 1 skipped
- `curl` API protected endpoints : 401 démontré.

## 10. Limites

- Pas de tests graphiques sur Settings/Capabilities/Odin/Frame.
- Pas de Docker lifecycle.
- Pas de WebUI dynamique simulée.
- Pas de capture supplémentaire au-delà du HTML reporter Playwright.

## 11. Statut final

WebUI : `PARTIALLY_VALIDATED`
Docker Applications : `PARTIALLY_VALIDATED`
Quantar : `PARTIALLY_VALIDATED`
Rust Capability Contract : `VALIDATED`
