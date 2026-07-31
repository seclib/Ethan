# Rapport SRE & Architecture : Stabilisation ETHAN

## Root Cause

Trois causes racines bloquantes ont été identifiées et corrigées :

### P0-1 : Redis Auth RESP3
**Cause** : `redis-py` 5.x utilise RESP3 par défaut, qui envoie la commande HELLO avant AUTH. Avec `requirepass` activé sur Redis 7+, la connexion est rejetée.
**Fix** : Ajout de `protocol=2` dans `redis_state.py` et `interfaces/api/main.py`, et changement du format URL de `redis://:password@host` vers `redis://default:password@host` dans `docker-compose.yml` et `.env.example`.

### P0-2 : Shadowing Bootstrap
**Cause** : `core/bootstrap/` (package avec `__init__.py`) shadowait `core/bootstrap.py` (module). L'import `from core.bootstrap import main` échouait.
**Fix** : Renommage de `core/bootstrap.py` → `core/ethan_bootstrap.py`. Mise à jour de `docker-compose.yml` et `deploy/Dockerfile.kernel`.

### P0-3 : Dual Event Incompatible
**Cause** : Trois classes `Event` coexistaient avec des signatures incompatibles :
- `core/ethan_types/event.py` : `payload=`, `EventType` enum
- `core/ethan_types/sdk/event.py` : `data=`, `EventType` class
- `core/bus/nats_bus.py` : `payload=`, `context=`, `session_id=`

**Fix** : 
- `core/ethan_types/sdk/event.py` → shim qui réexporte depuis `core/ethan_types/event.py`
- `core/ethan_types/event.py` → ajout du champ `data` comme alias de `payload` (via `__post_init__`), ajout de `from_dict()`/`from_json()`, fusion de toutes les constantes `EventType` du SDK
- `core/bus/nats_bus.py` → import depuis le canonical `Event`, suppression de la classe locale

## Files Modified

| Fichier | Changement |
|---------|------------|
| `core/state/redis_state.py` | `protocol=2` ajouté à `from_url()` |
| `interfaces/api/main.py` | `protocol=2` dans le healthcheck Redis |
| `docker-compose.yml` | URL Redis `redis://default:...`, healthchecks HTTP, flags `ENABLE_*` à `false`, dépendance modules `service_started` |
| `.env.example` | URL Redis `redis://default:...` |
| `core/ethan_bootstrap.py` | Renommé depuis `core/bootstrap.py`, ajout serveur HTTP `/health` sur port 8080, timeout 120s sur bootstrapper |
| `deploy/Dockerfile.kernel` | `COPY core/ethan_bootstrap.py`, healthcheck `curl -f http://localhost:8080/health` |
| `deploy/Dockerfile.module` | Healthcheck `curl -sf http://localhost:8081/health` |
| `core/ethan_types/event.py` | Champ `data` alias, `from_dict()`/`from_json()`, constantes EventType fusionnées |
| `core/ethan_types/sdk/event.py` | Shim réexportant depuis `core/ethan_types/event.py` |
| `core/bus/nats_bus.py` | Import canonical Event, `connect()` avec paramètre optionnel |
| `core/modules/__main__.py` | Serveur HTTP `/health` sur port 8081, retry NATS |

## Validation Commands

```bash
# 1. Build et démarrage
DOCKER_BUILDKIT=0 docker build -f deploy/Dockerfile.python-base -t ethan/python-base:latest .
DOCKER_BUILDKIT=0 docker compose build
docker compose up -d

# 2. Vérification statut
docker compose ps
# Résultat : 7/7 healthy (kernel, api, modules, nats, redis, postgres, pg_backup)

# 3. Health endpoints
curl -sf http://localhost:8080/health  # → {"status":"ok","service":"kernel","running":true}
curl -sf http://localhost:8000/health  # → {"status":"ok","service":"api"}

# 4. Logs kernel
docker compose logs kernel --tail 15
# → Bootstrap completed, Kernel started, 4 modules registered, health server on :8080
```

## Remaining Risks

1. **Docker BuildKit IPv6** : Le `# syntax=docker/dockerfile:1.4` dans les Dockerfiles provoque un échec réseau (IPv6 unreachable). Contournement : `DOCKER_BUILDKIT=0`.
2. **EventType dynamique** : Le code utilise encore `data=` dans 30+ appels Event. Le champ `data` alias fonctionne via `__post_init__`, mais une migration vers `payload=` serait plus propre.
3. **init.sql** : Le fichier `deploy/postgres/init.sql` doit contenir le schéma SQL (tables `events`, `goals`, `experiences`).
4. **Modules service** : Le service modules se connecte à NATS et expose `/health` mais ne charge aucun module cognitif réel.
5. **WebUI** : Le service UI démarre mais peut nécessiter du temps pour devenir healthy (npm run dev).