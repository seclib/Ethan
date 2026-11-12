# QUANTAR API — Rebuild et redéploiement ciblé

Date : 2026-11-04
Statut : validations HTTP réussies, validation visuelle non complète (pas de navigateur local)

## 1. Audit source

Routes Quantar attendues déclarées dans `interfaces/api/routers/quantar.py`, préfixe `/v1/quantar`, inclus dans `interfaces/api/main.py` (ligne 1202).

Endpoints clés :
- `GET /status`
- `GET /config`
- `GET /lifecycle/status`
- `POST /tasks`
- `GET /tasks/{task_id}`
- `GET /tasks/{task_id}/logs`
- `GET /tasks/{task_id}/result`

## 2. Audit Docker

- Image précédente : `ethan-api:latest` (`a6742f066ea4db6fcd008cc9db7e32af6b924869b27a93e234f3db0bfad7c38f`)
- Rollback : `ethan-api:rollback-20261104`
- Nouvelle image : `ethan-api:latest` (`41895ba3c1b29165a9b8f86dae1203eb049f5931c15d343c20d7c7fae636b082`)
- Dockerfile officiel : `deploy/Dockerfile.api`
- service redéployé : `ethan-api` uniquement

## 3. Commandes exécutées

- build : `docker compose -f docker-compose.yml build --no-cache api`
- déploy : `docker compose -f docker-compose.yml up -d --no-deps --force-recreate api`

## 4. Résultats HTTP (authentifié)

- `/v1/quantar/status` : 200
- `/v1/quantar/config` : 200
- `/v1/quantar/lifecycle/status` : 200
- `/api/v1/quantar/status` via proxy WebUI : 200
- `/api/v1/quantar/config` via proxy WebUI : 200
- `/api/v1/quantar/lifecycle/status` via proxy WebUI : 200

Retourné `available=false` (TradingAgents absent du conteneur API), sans erreur bloquante pour la page.

## 5. Validation WebUI

- `/quantar` authentifié : HTTP 200
- marqueur `ETHAN Quantar` présent
- proxy Quantar actif
- pas de preuve visuelle browser (pas de Chromium/Playwright)

## 6. Régession

- santé API : 200
- routes Quantar actives dans le nouveau conteneur
- service `ethan-api` seul redéployé, autres services préservés

## Conclusion

Le pair `frontend + API` est maintenant aligné pour Quantar. Les routes API sont accessibles et le frontend peut les appeler correctement. La validation finale visuelle complète reste conditionnée à la présence d'un navigateur.
