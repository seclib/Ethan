# ETHAN API Startup Fix

## Executive Summary

`ethan-api` entrait en boucle de redémarrage (`restarting/unhealthy`) immédiatement après son démarrage. Le diagnostic a montré que l'infrastructure (NATS, Redis, PostgreSQL) était **saine** ; le crash provenait d'une **erreur de code Python** dans le lifespan FastAPI de l'API Gateway, provoquée par l'utilisation d'attributs inexistants sur l'objet `CoreDomainServices`.

Deux causes racines identifiées et corrigées. L'API démarre désormais proprement (`Application startup complete`), répond `200` sur `/health/ready`, et `RestartCount=0`.

## Initial Failure

```text
Container ethan-api Started
api(restarting/unhealthy)

AttributeError: 'CoreDomainServices' object has no attribute 'tool_servers'
  File "/app/interfaces/api/main.py", line 355, in lifespan
    tool_servers=core_domains.tool_servers,
ERROR:    Application startup failed. Exiting.
```

## Root Cause

### Cause 1 (bloquante, P0) — `core_domains.tool_servers` inexistant

- `CoreDomainServices` (défini dans `interfaces/api/routers/v1.py:192`) n'expose **que** `agents`, `missions`, `knowledge`, `rag`.
- `interfaces/api/main.py` (lifespan) référençait `core_domains.tool_servers` lors de la construction du `IntegrationManager`.
- Le vrai `ToolServerManager` était créé **plus tard** dans le lifespan, avec `ToolManager` — après l'usage.

### Cause 2 (bloquante en cascade, P0) — `core_domains.chats` inexistant

- Même objet `CoreDomainServices` sans attribut `chats`.
- `SearchManager` recevait `chat_store=core_domains.chats` → aurait levé la même erreur une fois la Cause 1 corrigée.
- Un `ChatStore` local (même instance que celle injectée au router `/v1/chat`) existait déjà dans le lifespan.

## Evidence

```text
AttributeError: 'CoreDomainServices' object has no attribute 'tool_servers'
AttributeError: 'CoreDomainServices' object has no attribute 'chats'   (prédite, même pattern)
```

- `interfaces/api/routers/v1.py:192-206` → `__init__` ne définit que agents/missions/knowledge/rag.
- `interfaces/api/main.py:355` → `tool_servers=core_domains.tool_servers` (Crash 1).
- `interfaces/api/main.py:386` → `chat_store=core_domains.chats` (Crash 2).
- `interfaces/api/main.py:434/481` → `ToolManager` + `ToolServerManager` créés trop tard (après leur usage).

## Files Inspected

| File | Rôle dans le diagnostic |
|------|--------------------------|
| `docker-compose.yml` | Bloc service `api` : image, command, healthcheck, env, depends_on |
| `deploy/Dockerfile.api` | COPIES `core/`, `interfaces/api/` ; CMD uvicorn ; HEALTHCHECK `/health/ready` |
| `deploy/Dockerfile.python-base` | Base partagée (deps Python `.[server,dev]`) |
| `interfaces/api/main.py` | Lifespan FastAPI — composition des managers |
| `interfaces/api/routers/v1.py` | `CoreDomainServices` (attributs réels) |
| `core/integrations/__init__.py` | Signature `IntegrationManager(..., tool_servers=None)` |
| `core/search/__init__.py` | Signature `SearchManager(..., chat_store=None, ...)` |
| `core/state/chats.py` | `ChatStore` existant |
| `.env` | Variables (aucune incohérence responsable du crash) |
## Files Modified

| File | Changement |
|------|------------|
| `interfaces/api/main.py` | Réorganisation du lifespan (détails ci-dessous) |

## Exact Changes

### 1. Création avancée des managers partagés (avant `IntegrationManager`)

```python
# --- ToolManager + ToolServerManager (Core-owned, partagés) ---
from core.security.integration import build_secure_enforcer
from core.tools.manager import ToolManager
from core.tools.servers import ToolServerManager

secure_enforcer = build_secure_enforcer()
tool_manager = ToolManager(store=domain_store, policy_enforcer=secure_enforcer)
await tool_manager.initialize()
tool_servers_manager = ToolServerManager(store=domain_store, registry=tool_manager.registry)
```

→ `ToolManager`/`ToolServerManager` créés **une seule fois**, avant leur premier consommateur.

### 2. `IntegrationManager` branché sur l'instance partagée

```python
integration_manager = IntegrationManager(
    store=domain_store,
    event_bus=event_bus,
    tool_servers=tool_servers_manager,   # était : core_domains.tool_servers
)
```

### 3. Suppression de la recréation en double (bloc CapabilityManagers)

- Ancien bloc `secure_enforcer`/`tool_manager`/`initialize()` **supprimé** (déplacé en 1).
- `tool_servers=ToolServerManager(store=..., registry=...)` → `tool_servers=tool_servers_manager`.

### 4. `SearchManager` branché sur le `ChatStore` existant

```python
search_manager = SearchManager(
    knowledge_manager=core_domains.knowledge,
    chat_store=chat_store,               # était : core_domains.chats
    rag_pipeline=core_domains.rag,
)
```

## Why The Fix Is Correct

- Aucune nouvelle architecture : on **réutilise** des instances déjà créées dans le lifespan.
- Le `ChatStore` local (ligne 187) était déjà l'instance officielle injectée au router `/v1/chat` via `set_chat_store` — le `SearchManager` partage désormais la même instance (pas de duplication).
- `ToolManager` + `ToolServerManager` sont des composants Core existants ; seule leur **création** a été déplacée avant leur premier consommateur.
- Aucun healthcheck n'a été affaibli, aucun `restart: always` ajouté, aucun service retiré.
## Docker Validation

```text
NAME          STATUS
ethan-api     Up 52 seconds (healthy)      ← RestartCount=0
ethan-kernel  Up 5 minutes  (healthy)
ethan-modules Up 41 seconds (healthy)
ethan-nats    Up 7 minutes  (healthy)
ethan-pg_backup Up 5 minutes (healthy)
ethan-postgres Up 7 minutes  (healthy)
ethan-redis   Up 7 minutes  (healthy)
ethan-ui      Up 41 seconds (healthy)
```

Plus de boucle de redémarrage. `docker inspect ethan-api --format='{{.RestartCount}}'` → `0`.

## API Validation

```text
GET /health/ready            → 200 OK        (healthcheck réellement satisfait)
GET /integrations            → 401           (route montée + auth active — pas de 500)
GET /search/types            → 401           (route montée + auth active — pas de 500)
```

Les routes des deux blocs corrigés sont enregistrées (OpenAPI) et répondent via leur manager.

## Dependency Validation

- Image rebâtie : `docker compose build api` → OK.
- Startup log : `ProviderManager ready (default=ollama, providers=3)` → providers Core chargés.
- `IntegrationManager ready (Core-owned app integrations)` → Cause 1 résolue.
- `SearchManager ready (unified search)` → Cause 2 résolue.
- `Application startup complete` → aucun `startup failed` dans les logs du nouveau conteneur.

## Database Validation

- PostgreSQL : `healthy` (inchangé).
- Aucune migration touchée — le crash était purement applicatif (lifespan), pas SQL.

## NATS Validation

- NATS : `healthy` (inchangé).
- `EventBus ready (NATS-backed)` dans les logs de démarrage — l'API s'abonne bien via NATS.

## Redis Validation

- Redis : `healthy` (inchangé).
- `CoreWebUIStore ready (persistent WebUI records)` — le store (Redis+PG) s'initialise.

## Healthcheck Validation

Le healthcheck Docker (`curl -fsS http://localhost:8000/health/ready`) est **réellement satisfait** (200). Il n'a pas été modifié ni désactivé.

## Regression Tests

```text
tests/test_integrations.py  → 23 passed
```

- Les autres services (kernel, modules, ui, nats, postgres, redis, pg_backup) sont tous `healthy`.
- `ethan-ui` (WebUI) redémarré proprement.

## Remaining Issues

Aucun problème restant bloquant identifié.

## Production Risk

- Faible : le changement est une réorganisation de la composition des dépendances déjà existantes au sein du lifespan ; aucun composant métier n'a été modifié.

## Final Status

**FIXED** — démontré par :
1. `docker compose ps` → `ethan-api ... (healthy)`
2. `docker inspect ethan-api --format='{{.RestartCount}}'` → `0`
3. Logs de démarrage : `Application startup complete`, aucun `startup failed`
4. `GET /health/ready` → `200`
5. Routes `/integrations` et `/search/*` montées et répondant (401 auth, comportement attendu)
6. `tests/test_integrations.py` → `23 passed`
