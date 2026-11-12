# Quantar WebUI — Rapport de rebuild et redéploiement ciblé

Date : 2026-11-04
Statut : redéploiement effectué, validation incomplète — blocage backend identifié

## Images

- ancienne image courante (avant build) : `sha256:8ce554078fd4be9fc37bbc82af0ee74ef79417e4b5a6f2855f6e2e6aabb52c9e`
- nouvelle image candidate : `ethan-ui:latest` construite depuis `deploy/Dockerfile.ui`
- rollback tag : `ethan-ui:rollback-20261104`

## Commandes

- `docker compose -f docker-compose.yml build --no-cache ui`
- `docker compose -f docker-compose.yml up -d --no-deps --force-recreate ui`
- santé conteneur : `wget -q --spider http://127.0.0.1:3001` → healthy au moment de la vérification

## Résultats

- `/quantar` authentifié : HTTP 200
- corps contient encore un composant par défaut "This page could not be found."
- HTML contient aussi le marqueur `ETHAN Quantar`
- `/api/v1/quantar/status` via proxy : `404 {"detail":"Not Found"}`
- API directe backend (`/v1/quantar/status`) : `404 {"detail":"Not Found"}`

## Cause complémentaire identifiée

La source locale expose les routes API Quantar dans `interfaces/api/main.py`, mais l'image `ethan-api` déployée ne les expose pas :
- `grep quantar_router` absent du code embarqué dans le conteneur ;
- l'endpoint `/v1/quantar/*` est donc `Not Found` sur l'instance active.

Il n'y a donc pas de preuve que la page Quantar est fonctionnelle à l'exécution réelle tant que le backend déployé n'est pas aligné.

## Validation visuelle

Non effectuée : aucun navigateur Chromium/Playwright disponible dans l'environnement local.

## Conclusion

Le redéploiement WebUI seul a été effectué sans toucher à PostgreSQL, Redis, NATS, Odin ou Quantar. Cependant une mise en cause supplémentaire apparaît au niveau de l'image `ethan-api` déployée, qui ne contient pas le router Quantar. La correction ne peut pas être déclarée terminée sans un alignement backend.


## Validation complémentaire postrédéploiement API

- Rebuild/redeploy final de `ethan-api` effectué (`ethan-api:latest`, nouvel ID).
- Routes Quantar maintenant accessibles via l'API déployée.
- `/v1/quantar/status` : 200 (disponibilité false attendue car TradingAgents absent du conteneur API)
- `/v1/quantar/config` : 200
- `/v1/quantar/lifecycle/status` : 200
- `/api/v1/quantar/*` via WebUI : 200 pour status, config et lifecycle/status.

## Conclusion finale

Le redéploiement initial de `ethan-ui` seul n'était pas suffisant : l'API déployée (`ethan-api`) ne contenait pas le router Quantar. Après alignement de l'image API, les routes Quantar sont atteignables et les appels frontend passent l'API. L'absence de navigateur local empêche la validation visuelle complète, mais la preuve HTTP et le SSR confirment le chargement de la page Quantar.
