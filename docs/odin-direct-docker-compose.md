# Migration Odin — Architecture Docker directe (sans `odin-controller`)

## Résumé

L'architecture de gestion du cycle de vie d'Odin a été simplifiée : le service intermédiaire `odin-controller` a été supprimé. `core/plugins/odin.py` pilote désormais **directement** `docker compose` via subprocess depuis le Core ETHAN, sans passer par un contrôleur dédié.

---

## Architecture avant / après

### Avant

```
WebUI → API → odin-controller (service dédié, socket Docker) → docker compose
```

- Service `odin-controller` dans `docker-compose.yml`
- Variables d'env : `ETHAN_ODIN_CONTROLLER_URL`, `ETHAN_ODIN_CONTROLLER_TOKEN`, `ETHAN_ODIN_REPO_DIR`
- Réseau isolé `odin-control`
- Socket Docker monté sur `odin-controller`
- Logique de pilotage dans une interface/service séparé

### Après

```
WebUI → API → ETHAN Core (OdinService) → docker compose subprocess (projet `odin`)
```

- Pas de service `odin-controller`
- Socket Docker monté uniquement sur le service `api`
- Pas de variable d'environnement controller
- Pas de réseau dédié `odin-control`
- Logique de pilotage dans le Core (`core/plugins/odin.py`)

---

## Fichiers modifiés

| Fichier | Modification |
|---------|--------------|
| `core/plugins/odin.py` | Suppression du bloc controller dans `_run_docker` ; ajout `import shutil` et `import subprocess` ; correction `check_health` |
| `core/plugins/odin_compose_config.py` | Suppression de `ODIN_CONTROLLER_URL` |
| `docker-compose.yml` | Suppression `odin-controller` du `depends_on` de `api` ; suppression `- odin-control` des réseaux ; suppression du réseau `odin-control` |
| `tests/core/test_odin.py` | Suppression des références controller ; réécriture des tests pour le subprocess direct ; mise à jour des assertions `allowed_actions` |
| `tests/core/test_odin_compose_controller.py` | Inchangé (9 tests passent) |
| `tests/interfaces/test_odin_api.py` | Inchangé (7 tests passent) |
| `docs/plugins/odin-compose-controller.md` | Réécriture complète : architecture directe, opérations autorisées, confinement, gestion manuelle, sécurité |

---

## Flux d'appel (après migration)

```
WebUI (interface)
  │  HTTP / API REST
  ▼
interfaces/api/main.py  (API ETHAN)
  │  appel méthode OdinService
  ▼
core/plugins/odin.py    (Core — OdinService)
  │  docker compose subprocess
  ▼
docker compose -p odin -f examples/odin/compose.yaml <action>
```

---

## Opérations autorisées (allowlist stricte)

| Action | Commande docker compose |
|--------|-------------------------|
| Démarrer | `compose -p odin -f examples/odin/compose.yaml up -d` |
| Arrêter | `compose -p odin -f examples/odin/compose.yaml stop` |
| Redémarrer | `compose -p odin -f examples/odin/compose.yaml restart` |
| Désinstaller | `compose -p odin -f examples/odin/compose.yaml down` |
| État | `compose -p odin -f examples/odin/compose.yaml ps --all --format json` |
| Valider config | `compose -p odin -f examples/odin/compose.yaml config` |
| Logs | `compose -p odin -f examples/odin/compose.yaml logs --tail=N --no-color` |

Aucune commande Docker arbitraire n'est acceptée.

---

## Confinement

`OdinService._validate_confinement()` vérifie à chaque appel que le fichier Compose visé est exactement `examples/odin/compose.yaml` sous la racine ETHAN. Tout autre chemin est refusé (fail-closed).

La variable d'environnement `ETHAN_ODIN_REPO_DIR` peut surcharger le répertoire du dépôt, mais le fichier Compose doit rester `compose.yaml` à la racine de ce répertoire.

---

## Gestion manuelle depuis le dépôt Odin

Depuis `/home/fatsio/AI/Ethan/examples/odin` :

```sh
# Vérifier la configuration
docker compose --project-name odin -f compose.yaml config

# Démarrer Odin
docker compose --project-name odin -f compose.yaml up -d

# Voir l'état des conteneurs
docker compose --project-name odin -f compose.yaml ps --all

# Arrêter Odin
docker compose --project-name odin -f compose.yaml stop

# Redémarrer Odin
docker compose --project-name odin -f compose.yaml restart

# Désinstaller (stop + suppression des conteneurs, volumes conservés)
docker compose --project-name odin -f compose.yaml down

# Voir les logs
docker compose --project-name odin -f compose.yaml logs --tail=100 --no-color
```

---

## Sécurité

- Le socket Docker est monté **uniquement** sur le service `api` de la stack ETHAN.
- Les secrets (tokens, clés API) sont automatiquement redactés dans les logs et sorties d'erreur (`OdinService._redact_secrets`).
- Aucun démarrage automatique non sollicité au boot d'ETHAN.
- L'authentification et le RBAC sont gérés par l'API ETHAN sur les routes WebUI.

---

## Validation des tests

| Suite de tests | Résultat |
|----------------|----------|
| `tests/core/test_odin.py` | 17 passed |
| `tests/core/test_odin_compose_controller.py` | 9 passed |
| `tests/interfaces/test_odin_api.py` | 7 passed |
| `tests/deployment/test_docker.py` | 11 passed |
| `tests/security/test_nats_auth.py` | 10 passed |
| `docker compose config` | Valide |
| WebUI `npm run typecheck` | (à confirmer) |
| WebUI `npm run build` | (à confirmer) |

---

## Commandes de gestion Odin depuis son dépôt

Le projet Compose s'appelle `odin`. Toutes les opérations se font depuis le dépôt Odin ou via l'API ETHAN :

```sh
# Depuis le dépôt
cd examples/odin
docker compose --project-name odin -f compose.yaml up -d      # démarrer
docker compose --project-name odin -f compose.yaml stop        # arrêter
docker compose --project-name odin -f compose.yaml restart     # redémarrer
docker compose --project-name odin -f compose.yaml down        # désinstaller
docker compose --project-name odin -f compose.yaml ps --all    # état
docker compose --project-name odin -f compose.yaml logs --tail=100 --no-color  # logs
```

```sh
# Via l'API ETHAN (équivalent)
POST /api/v1/odin/start
POST /api/v1/odin/stop
POST /api/v1/odin/restart
POST /api/v1/odin/uninstall
GET  /api/v1/odin/status
```

---

## Règles d'architecture ETHAN respectées

✅ Le Core représente l'intelligence — `OdinService` est dans `core/plugins/`  
✅ Le Runtime représente l'orchestration — pilotage direct via subprocess  
✅ Les Interfaces ne définissent pas les capacités métier — WebUI ne fait que déclencher via l'API  
✅ Pas de doublon : pas de `interfaces/webui/odin/` avec une logique concurrente  
✅ ETHAN fonctionne sans WebUI — le Core pilote Odin indépendamment  
✅ Secrets non stockés dans le code/git/logs — redaction automatique dans les logs  
| `docs/odin-direct-docker-compose.md` | **Nouveau** : synthèse de la migration (ce document) |