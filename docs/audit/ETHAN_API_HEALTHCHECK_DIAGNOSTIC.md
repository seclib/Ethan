# ETHAN — Diagnostic API Healthcheck (`running/unhealthy`)

**Date** : 14/08/2026  
**Auteur** : Audit SRE / Principal Backend Engineer  
**Statut** : Diagnostic complet — Phase 1 terminée (aucune modification)

---

## 1. Résumé exécutif

Le service API ETHAN (`ethan-api`) est marqué `running/unhealthy` pendant le démarrage car **le processus de démarrage de l'API prend ~2min15s**, alors que le HEALTHCHECK Docker le déclare `unhealthy` après ~40s (`start_period: 10s` + `retries: 3` × `interval: 10s`).

**Cause racine** : le `ProviderManager.initialize()` bloque ~2min15s en tentant de joindre Ollama via `http://host.docker.internal:11434`. Le conteneur API est sur le réseau `ethan-core` (172.20.0.0/16), mais `host.docker.internal` est mappé à `172.17.0.1` (passerelle du bridge Docker par défaut), qui est **injoignable** depuis ce réseau. Le client `httpx.AsyncClient(timeout=300.0)` attend le timeout TCP (~2min15s) avant d'abandonner.

**État actuel** : après le démarrage complet, l'API est **healthy** (tous les healthchecks passent). Le problème est un **démarrage trop lent** causé par une mauvaise configuration réseau, pas une API cassée.

---

## 2. Architecture observée

| Élément | Valeur |
|---|---|
| Service Compose | `api` |
| Conteneur | `ethan-api` |
| Image | `ethan-api` (build `deploy/Dockerfile.api`) |
| Commande | `uvicorn interfaces.api.main:app --host 0.0.0.0 --port 8000 --workers 1` |
| Port interne | `8000` |
| Port exposé | `127.0.0.1:8000` |
| Réseau | `ethan-core` (172.20.0.0/16, gateway 172.20.0.1) |
| Dépendances | `nats` (healthy), `postgres` (healthy), `redis` (healthy) |
| HEALTHCHECK (compose) | `curl -fsS http://localhost:8000/health/ready` — interval 10s, timeout 5s, retries 3, start_period 10s |
| HEALTHCHECK (Dockerfile) | `curl -fsS http://localhost:8000/health/ready` — interval 30s, timeout 5s, retries 3, start_period 15s |

**Note** : le HEALTHCHECK du `docker-compose.yml` **override** celui du Dockerfile. Les deux utilisent la même route `/health/ready`.

---

## 3. État des conteneurs

```
NAME              STATUS                        PORTS
ethan-api         Up 4 minutes (healthy)        127.0.0.1:8000->8000/tcp
ethan-kernel      Up 2 minutes (healthy)        127.0.0.1:8080->8080/tcp
ethan-modules     Up 2 minutes (healthy)
ethan-nats        Up 4 minutes (healthy)        127.0.0.1:4222->4222/tcp
ethan-postgres    Up 4 minutes (healthy)        127.0.0.1:5432->5432/tcp
ethan-redis       Up 4 minutes (healthy)        127.0.0.1:6379->6379/tcp
ethan-ui          Up About a minute (healthy)   127.0.0.1:3000->3000/tcp
ethan-pg_backup   Up About a minute (healthy)   5432/tcp
```

**`docker inspect ethan-api`** :
- `RestartCount=0`
- `StartedAt=2026-08-14T06:39:44Z`
- `State.Status=running`
- `State.Health.Status=healthy`
- `FailingStreak=0`

**Conclusion** : tous les conteneurs sont actuellement healthy. Le problème est transitoire, lié au démarrage.

---

## 4. Analyse du HEALTHCHECK

### Commande exécutée
```bash
curl -fsS http://localhost:8000/health/ready
```

### Paramètres (compose — effectif)
| Paramètre | Valeur |
|---|---|
| Interval | 10s |
| Timeout | 5s |
| Retries | 3 |
| Start period | 10s |

### Route testée
`GET /health/ready` → `interfaces/api/main.py:564`

### Comportement de la route
```python
async def _health_readiness() -> Response | dict:
    nc = _message_router._nats
    nats_ok = nc is not None and nc.is_connected
    if not nats_ok:
        return Response(status_code=503, ...)  # ← curl -f échoue
    return {"status": "ok", ...}
```

**Point critique** : la route `/health/ready` retourne **503** si NATS n'est pas connecté. `curl -f` échoue sur 503 → conteneur `unhealthy`.

### Chronologie du démarrage
| Temps | Événement |
|---|---|
| 06:39:44 | Uvicorn démarre, NATS connecté |
| 06:39:45 | ProviderManager : Ollama initialisé |
| **06:39:45 → 06:42:00** | **BLOCAGE ~2min15s** : `list_models()` Ollama timeout |
| 06:42:00 | ProviderManager prêt, ConfigurationService prêt |
| 06:42:00 | Uvicorn écoute sur 8000 |
| ~06:42:10 | Premier `/health/ready` → 200 OK |

**Le HEALTHCHECK commence à `start_period: 10s` après le démarrage du conteneur (06:39:44)**. Il échoue pendant ~2min15s (l'API n'écoute pas encore). Avec `retries: 3` × `interval: 10s` = ~40s, le conteneur est déclaré `unhealthy` à ~06:40:24.

---

## 5. Analyse des logs

### Séquence de démarrage (extraits clés)
```
06:39:44.903 INFO  API Gateway connecting to NATS: nats://nats:4222
06:39:44.906 INFO  API Gateway connected to NATS
06:39:45.027 INFO  ProviderManager PostgreSQL pool connected
06:39:45.039 WARNING  PostgreSQL provider load failed: relation "llm_providers" does not exist
06:39:45.105 INFO  Ollama provider initialized (http://host.docker.internal:11434)
06:42:00.285 WARNING  Failed to list Ollama models: All connection attempts failed  ← 2min15s de blocage
06:42:00.286 INFO  ProviderManager ready (default=ollama, providers=1)
06:42:00.291 INFO  ConfigurationService ready
INFO:  Application startup complete.
INFO:  Uvicorn running on http://0.0.0.0:8000
```

### Première erreur significative
```
06:39:45.039 WARNING  PostgreSQL provider load failed: relation "llm_providers" does not exist
```
→ Non bloquant (fallback mémoire), mais indique une migration manquante.

### Blocage principal
```
06:39:45.105 → 06:42:00.285  (2min15s)
```
→ `provider.list_models()` sur Ollama bloque car `host.docker.internal:11434` est injoignable.

### Autres erreurs
```
WARNING  Core record list failed for missions: relation "core_domain_records" does not exist
WARNING  Core record list failed for chats: relation "core_domain_records" does not exist
```
→ Migration 005 non appliquée.

---

## 6. Dépendances

| Service | Status | Health | Port | Connectivité API |
|---|---|---|---|---|
| NATS | running | healthy | 4222 | ✅ `nats_connected: true` |
| Redis | running | healthy | 6379 | ✅ `redis: connected` |
| PostgreSQL | running | healthy | 5432 | ✅ `postgresql: connected` |
| Ollama (hôte) | running | — | 11434 | ❌ `host.docker.internal:11434` timeout |

### Test direct depuis le conteneur API
```bash
# Depuis ethan-api
curl -sv -m 3 http://host.docker.internal:11434/api/tags
# → Connection timed out after 3002 milliseconds

curl -sv -m 3 http://172.20.0.1:11434/api/tags
# → Connection timed out after 3002 milliseconds
```

### Cause réseau
- `host.docker.internal` est mappé à `172.17.0.1` (passerelle du bridge Docker par défaut)
- Le conteneur API est sur le réseau `ethan-core` (172.20.0.0/16, gateway 172.20.0.1)
- **Aucune des deux passerelles ne route vers l'hôte** pour le port 11434
- Ollama écoute sur `*:11434` sur l'hôte, mais le trafic depuis le réseau ethan-core n'atteint pas l'hôte

---

## 7. PostgreSQL / Migrations

### État de la base
```
Schema |       Name        | Type  | Owner
public | audit_log         | table | ethan
public | checkpoints       | table | ethan
public | config_changes    | table | ethan
public | cost_log          | table | ethan
public | events            | table | ethan
public | events_outbox     | table | ethan
public | experiences       | table | ethan
public | goal_steps        | table | ethan
public | goals             | table | ethan
public | modules           | table | ethan
public | schema_migrations | table | ethan
public | sessions          | table | ethan
public | snapshots         | table | ethan
public | users             | table | ethan
```

### Migrations appliquées
```
0001_initial_schema          | 2026-07-31 13:59:40
0002_stabilize_legacy_schema | 2026-07-31 13:59:40
0003_create_users_table      | 2026-08-02 07:38:54
```

### Migrations manquantes
- **004_create_llm_providers_table.sql** → table `llm_providers` absente
- **005_create_core_domain_records.sql** → table `core_domain_records` absente

### Impact
- `llm_providers` absente → ProviderStore bascule en mémoire (warnings, non bloquant)
- `core_domain_records` absente → CoreRecordStore bascule en mémoire (warnings, non bloquant)
- **Non bloquant pour le healthcheck**, mais dégradation fonctionnelle

### Cause
Le script `cmd-up.sh` tente d'exécuter les migrations via `cmd-migrate.sh` (alembic), mais :
1. Le répertoire `deploy/postgres/alembic/` ne contient **pas** de répertoire `versions/` (aucune migration alembic)
2. `cmd-migrate.sh` exécute `alembic upgrade head` → échoue silencieusement (pas de versions)
3. Les migrations SQL (`004`, `005`) ne sont **jamais exécutées** par le script

---

## 8. NATS

- **Status** : running, healthy
- **Healthcheck** : `wget -qO- http://127.0.0.1:8222/healthz` → OK
- **Connectivité API** : `nats_connected: true` (confirmé par `/health/ready` → 200)
- **Conclusion** : NATS fonctionne correctement, **n'est pas la cause** du problème

---

## 9. Redis

- **Status** : running, healthy
- **Healthcheck** : `redis-cli -a <password> ping` → PONG
- **Connectivité API** : `redis: connected` (confirmé par `/health/detailed`)
- **Conclusion** : Redis fonctionne correctement, **n'est pas la cause** du problème

---

## 10. API / Health endpoint

### Routes disponibles
| Route | Comportement | Statut |
|---|---|---|
| `/health` | Readiness (NATS) | 200 si NATS connecté, 503 sinon |
| `/health/live` | Liveness (process HTTP) | Toujours 200 |
| `/health/ready` | Readiness (NATS) | 200 si NATS connecté, 503 sinon |
| `/health/detailed` | Vérifie NATS + Redis + PostgreSQL | 200 si tout OK, 503 sinon |

### Test direct
```bash
curl -s -o /dev/null -w "HTTP %{http_code} - %{time_total}s\n" http://localhost:8000/health/ready
# HTTP 200 - 0.004070s

curl -s http://localhost:8000/health/live
# {"status":"ok","service":"api"}

curl -s http://localhost:8000/health/detailed
# {"status":"ok","checks":{"api_nats":"connected","nats":"connected","redis":"connected","postgresql":"connected"}}
```

### Analyse
- L'API est **fonctionnelle** une fois démarrée
- Le healthcheck `/health/ready` est un **readiness** (dépend de NATS), pas un liveness
- Le HEALTHCHECK Docker devrait utiliser `/health/live` (liveness) pour ne pas marquer le conteneur `unhealthy` si NATS tombe temporairement

---

## 11. ETHAN Supervisor

### Script `scripts/cmd-up.sh`
- Séquence : infrastructure → migrations → api → kernel → modules → pg_backup/ui
- `wait_for_health "api" 120` : attend 120s max pour que l'API soit healthy
- Affiche `Progression : 0/1 healthy` et `api(running/unhealthy)`

### Bug dans la supervision
1. **Timeout trop court** : l'API met ~2min15s à démarrer, mais le superviseur attend 120s
2. **Migrations non exécutées** : `cmd-migrate.sh` (alembic) échoue car pas de répertoire `versions/`
3. **Le superviseur interprète correctement Docker Health** : `running/unhealthy` est exact

### Chronologie du problème
```
06:39:44  API démarre
06:39:54  HEALTHCHECK start_period terminé (10s)
06:40:24  HEALTHCHECK unhealthy (3 retries × 10s)
06:41:44  Superviseur timeout (120s) → "Progression : 0/1 healthy"
06:42:00  API enfin prête (2min15s)
06:42:10  API healthy (mais superviseur a déjà abandonné)
```

---

## 12. Cause racine

### P0 — Blocage du démarrage API sur Ollama (2min15s)

**SYMPTÔME** : L'API met ~2min15s à démarrer, le HEALTHCHECK la déclare `unhealthy` après ~40s.

**CAUSE** : `ProviderManager.initialize()` → `_register(ollama)` → `provider.list_models()` → `httpx.get("http://host.docker.internal:11434/api/tags")`. Le conteneur API est sur le réseau `ethan-core` (172.20.0.0/16), mais `host.docker.internal` est mappé à `172.17.0.1` (bridge Docker par défaut), injoignable depuis ce réseau. Le client `httpx.AsyncClient(timeout=300.0)` attend le timeout TCP (~2min15s).

**PREUVE** :
- Logs : `06:39:45.105` → `06:42:00.285` (gap de 2min15s)
- `docker exec ethan-api curl -sv -m 3 http://host.docker.internal:11434/api/tags` → `Connection timed out`
- `docker exec ethan-api curl -sv -m 3 http://172.20.0.1:11434/api/tags` → `Connection timed out`
- Ollama sur l'hôte : `curl http://localhost:11434/api/tags` → OK (répond)

**IMPACT** : API `unhealthy` pendant le démarrage, superviseur timeout, démarrage ETHAN interrompu.

**CORRECTION RECOMMANDÉE** :
1. **Option A (recommandée)** : Ajouter un service `ollama` dans `docker-compose.yml` (profil `llm`) et configurer `OLLAMA_BASE_URL=http://ollama:11434`
2. **Option B** : Utiliser `network_mode: host` pour le service API (non recommandé)
3. **Option C** : Configurer Ollama pour écouter sur `0.0.0.0` et utiliser l'IP de la passerelle ethan-core (172.20.0.1) — nécessite iptables

**RISQUE** : Faible. La correction est non destructive.

---

### P1 — Migrations 004/005 non appliquées

**SYMPTÔME** : Warnings `relation "llm_providers" does not exist`, `relation "core_domain_records" does not exist`.

**CAUSE** : Le script `cmd-migrate.sh` utilise alembic, mais `deploy/postgres/alembic/` n'a pas de répertoire `versions/`. Les migrations SQL `004_create_llm_providers_table.sql` et `005_create_core_domain_records.sql` ne sont jamais exécutées.

**PREUVE** :
- `schema_migrations` : seulement 0001, 0002, 0003
- Tables `llm_providers` et `core_domain_records` absentes
- `deploy/postgres/alembic/` : seulement `alembic.ini` et `env.py` (pas de `versions/`)

**IMPACT** : Dégradation fonctionnelle (fallback mémoire), non bloquant pour le healthcheck.

**CORRECTION RECOMMANDÉE** : Exécuter les migrations SQL manuellement :
```bash
docker exec -i ethan-postgres psql -U ethan -d ethan -f - < deploy/postgres/migrations/004_create_llm_providers_table.sql
docker exec -i ethan-postgres psql -U ethan -d ethan -f - < deploy/postgres/migrations/005_create_core_domain_records.sql
```

**RISQUE** : Faible. Les migrations sont idempotentes (`CREATE TABLE IF NOT EXISTS`).

---

### P2 — Configuration `host.docker.internal` incorrecte

**SYMPTÔME** : `host.docker.internal` mappé à `172.17.0.1` (bridge par défaut), injoignable depuis le réseau `ethan-core`.

**CAUSE** : `extra_hosts: - "host.docker.internal:host-gateway"` dans `docker-compose.yml` mappe vers la passerelle du bridge Docker par défaut, pas vers la passerelle du réseau `ethan-core`.

**PREUVE** :
- `docker exec ethan-api getent hosts host.docker.internal` → `172.17.0.1`
- Le conteneur est sur `ethan-core` (gateway 172.20.0.1)
- Les deux passerelles timeout sur le port 11434

**IMPACT** : Ollama injoignable depuis l'API → blocage du démarrage.

**CORRECTION RECOMMANDÉE** : Utiliser un service Ollama Docker (Option A de P0).

**RISQUE** : Faible.

---

### P3 — HEALTHCHECK inapproprié (readiness vs liveness)

**SYMPTÔME** : Le HEALTHCHECK Docker utilise `/health/ready` (readiness) qui dépend de NATS.

**CAUSE** : `/health/ready` retourne 503 si NATS est déconnecté. Le HEALTHCHECK Docker devrait utiliser `/health/live` (liveness) pour vérifier que le process HTTP répond, et laisser la readiness à l'orchestrateur.

**PREUVE** : `interfaces/api/main.py:564-567` — `/health/ready` dépend de `_message_router._nats`.

**IMPACT** : Si NATS tombe temporairement, le conteneur API est marqué `unhealthy` alors que l'API fonctionne.

**CORRECTION RECOMMANDÉE** : Changer le HEALTHCHECK Docker pour utiliser `/health/live` :
```yaml
healthcheck:
  test: ["CMD", "curl", "-fsS", "http://localhost:8000/health/live"]
```

**RISQUE** : Faible. `/health/live` est toujours 200 si le process HTTP répond.

---

### P4 — Bug dans `_register` (list_models sans await)

**SYMPTÔME** : `provider.list_models()` est appelé sans `await` dans `_register`.

**CAUSE** : `core/llm/provider_manager.py:566` :
```python
models = provider.list_models() if hasattr(provider.list_models, "__call__") else []
```
`list_models()` est une coroutine (`async def`), donc `hasattr(..., "__call__")` est True, mais l'appel sans `await` retourne un coroutine object, pas la liste.

**PREUVE** : `core/llm/providers/ollama.py:117` — `async def list_models(self)`.

**IMPACT** : Les modèles ne sont pas enregistrés dans le registry (le `if models:` est toujours True car un coroutine object est truthy, mais `await models` échoue silencieusement dans le `try/except`).

**CORRECTION RECOMMANDÉE** :
```python
models = await provider.list_models() if hasattr(provider.list_models, "__await__") else []
```

**RISQUE** : Faible. Amélioration de robustesse.

---

## 13. Corrections recommandées (ordre d'intervention)

### Ordre 1 — P0 : Résoudre le blocage Ollama
1. Ajouter un service `ollama` dans `docker-compose.yml` (profil `llm`)
2. Configurer `OLLAMA_BASE_URL=http://ollama:11434` dans l'API
3. Rebuild et redémarrer

### Ordre 2 — P1 : Appliquer les migrations manquantes
1. Exécuter `004_create_llm_providers_table.sql`
2. Exécuter `005_create_core_domain_records.sql`
3. Vérifier `schema_migrations`

### Ordre 3 — P3 : Corriger le HEALTHCHECK
1. Changer le HEALTHCHECK Docker pour `/health/live`
2. Garder `/health/ready` pour la readiness (superviseur)

### Ordre 4 — P4 : Corriger le bug `_register`
1. Ajouter `await` devant `provider.list_models()`

### Ordre 5 — P2 : Corriger `host.docker.internal`
1. Résolu par l'ajout du service Ollama (Ordre 1)

---

## 14. Tests à effectuer après correction

1. **Rebuild** : `docker compose build api`
2. **Démarrage** : `./ethan up`
3. **Vérifier Docker health** : `docker compose ps` → `ethan-api` doit être `healthy` en < 30s
4. **Appeler le health endpoint** : `curl http://localhost:8000/health/ready` → 200
5. **Vérifier les logs** : `docker logs ethan-api` → pas de blocage > 10s
6. **Vérifier les dépendances** : `curl http://localhost:8000/health/detailed` → tout `connected`
7. **Vérifier la stabilité** : l'API doit rester healthy plusieurs cycles (5+ minutes)
8. **Vérifier les migrations** : `docker exec ethan-postgres psql -U ethan -d ethan -c "\dt"` → `llm_providers` et `core_domain_records` présentes
9. **Vérifier Ollama** : `docker exec ethan-api curl http://ollama:11434/api/tags` → répond
10. **Exécuter les tests** : `pytest tests/`

---

## 15. Diagnostic classé

| Priorité | Problème | Impact | Correction |
|---|---|---|---|
| **P0** | Blocage Ollama 2min15s (host.docker.internal injoignable) | API `unhealthy` au démarrage, superviseur timeout | Service Ollama Docker + `OLLAMA_BASE_URL=http://ollama:11434` |
| **P1** | Migrations 004/005 non appliquées | Dégradation fonctionnelle (fallback mémoire) | Exécuter les migrations SQL |
| **P2** | `host.docker.internal` mappé vers 172.17.0.1 | Ollama injoignable depuis ethan-core | Résolu par P0 |
| **P3** | HEALTHCHECK utilise `/health/ready` (readiness) | Conteneur `unhealthy` si NATS tombe | Utiliser `/health/live` pour Docker |
| **P4** | `list_models()` sans `await` dans `_register` | Modèles non enregistrés dans le registry | Ajouter `await` |

---

## 16. Vérification approfondie Ollama (feedback)

### 16.1 Où ETHAN teste Ollama

| Question | Réponse |
|---|---|
| Où ETHAN teste Ollama | `ProviderManager.initialize()` → `_register(ollama)` → `provider.list_models()` |
| Qui effectue le test | Le processus API (`uvicorn interfaces.api.main:app`) dans le conteneur `ethan-api` |
| À quel moment | Au démarrage (lifespan FastAPI, `interfaces/api/main.py:83-224`) |
| Quelle commande/API | `httpx.AsyncClient(timeout=300.0).get("http://host.docker.internal:11434/api/tags")` |
| Quelle URL | `http://host.docker.internal:11434` (valeur `OLLAMA_BASE_URL` du `.env`, défaut du code `core/llm/provider_manager.py:113`) |
| Depuis quel environnement | Depuis le conteneur `ethan-api` (réseau `ethan-core`, 172.20.0.0/16) |
| Depuis le conteneur API | Oui, c'est dans le conteneur que le test est exécuté |
| `localhost` est-il utilisé | Non — `OLLAMA_BASE_URL=http://host.docker.internal:11434` |
| L'adresse hôte est-elle accessible ? | **NON** — voir 16.2 |
| L'échec Ollama rend-il API unhealthy ? | **OUI indirectement** — le blocage de 2min15s pendant `list_models()` retarde le démarrage de l'API ; le HEALTHCHECK Docker (start_period 10s + 3 retries × 10s ≈ 40s) déclare `running/unhealthy` avant que l'API ne soit prête |
| Cette dépendance est-elle nécessaire pour `healthy` ? | **NON** — `/health/ready` ne vérifie que NATS. Ollama ne devrait pas bloquer la readiness. Le blocage vient de `_register()` dans ProviderManager |

### 16.2 Résolution réseau réelle

Tests effectués depuis le conteneur `ethan-api` :

```bash
# host.docker.internal → 172.17.0.1 (bridge par défaut)
docker exec ethan-api curl -sv -m 3 http://host.docker.internal:11434/api/tags
# → Connection timed out after 3002 milliseconds

# Passerelle du réseau ethan-core → 172.20.0.1
docker exec ethan-api curl -sv -m 3 http://172.20.0.1:11434/api/tags
# → Connection timed out after 3002 milliseconds

# IP LAN de l'hôte → 192.168.1.68
docker exec ethan-api curl -sv -m 5 http://192.168.1.68:11434/api/tags
# → Connection timed out after 5002 milliseconds

# localhost depuis le conteneur → 127.0.0.1
docker exec ethan-api curl -sv -m 3 http://localhost:11434/api/tags
# → Connection refused (pas d'IP du moteur sur la boucle locale)
```

### 16.3 Cause du blocage réseau : firewall UFW

```
Chain INPUT (policy DROP)
ufw-before-input ...
Chain FORWARD (policy DROP)
ufw-before-forward ...
```

Le firewall UFW de l'hôte bloque le trafic entrant depuis la passerelle Docker vers le port 11434. Ollama écoute sur `*:11434` sur l'hôte, mais UFW ne permet pas les connexions depuis les sous-réseaux Docker (172.17.0.0/16, 172.20.0.0/16) vers le port 11434.

### 16.4 Point critique — localhost

Confirmation du point critique du feedback :
- Sur l'hôte : `localhost:11434` = Ollama (fonctionne)
- Depuis le conteneur : `localhost:11434` = le conteneur lui-même (connection refused)
- `host.docker.internal` est mappé à `172.17.0.1` (bridge par défaut), mais ce réseau n'est pas accessible depuis `ethan-core`
- Les deux passerelles `172.17.0.1` et `172.20.0.1` timeout sur le port 11434

### 16.5 Architecture cible

Conformément au feedback :

```
HOST
 └── Ollama (indépendant, non géré par ETHAN)
       ↑
       │ HTTP API (port 11434)
       │
ETHAN API (conteneur)
       ↑
       │
ETHAN WebUI
```

ETHAN ne doit **pas** installer ni gérer Ollama comme service Docker ETHAN. Ollama est une dépendance externe optionnelle, uniquement requise pour les capacités LLM.

### 16.6 Politique de healthcheck

Le feedback soulève le point important : le HEALTHCHECK de l'API doit refléter **LIVENESS** (API process qui répond), pas **DEPENDENCY READINESS** (Ollama + NATS + PostgreSQL + Redis).

- Actuellement : `/health/ready` vérifie NATS (`nats_connected`), et le blocage Ollama retarde le démarrage.
- Recommandé : `/health/live` pour le HEALTHCHECK Docker (LIVENESS), et `/health/ready` pour la readiness orchestrée (dépendances), à séparer en 2 endpoints distincts.
- Une API peut être vivante alors qu'Ollama est temporairement indisponible : la politique `api = healthy` doit signifier "API fonctionne", pas "Toutes les dépendances fonctionnent".

## 16.7 Verification du déclenchement exact dans le code

L'hypothèse du feedback est validée : ETHAN teste bien Ollama via une logique ~équivalente à `ollama list` (ici `GET /api/tags`).

Le déclenchement exact se produit dans `core/llm/provider_manager.py:_register()` (ligne 561-576) :
```python
async def _register(self, provider, provider_id):
    await provider.initialize()
    models = provider.list_models() if hasattr(provider.list_models, "__call__") else []  # ligne 566 : SANS await
    if models:
        model_list = await models if hasattr(models, "__await__") else models  # ligne 572 : await ici
```
- `provider.list_models()` (ligne 566) crée une coroutine (pas encore exécutée)
- `await models` (ligne 572) exécute réellement `list_models()` → `httpx.get("http://host.docker.internal:11434/api/tags")`
- **Le blocage de 2min15s se produit À LA LIGNE 572**, pas à la ligne 566

Conclusion : bien que ce soit un bug `await` (P4), le blocage réel vient du fait que `list_models()` est exécutée pendant le lifespan startup AVANT que Uvicorn n'écoule. C'est l'étape 9 du feedback confirmée : **l'échec Ollama rend l'API unhealthy indirectement** en retardant le démarrage.

## 13.8 Politique de correction révisée (alignée sur le feedback)

Le feedback impose :
1. **Ollama ne doit PAS être installé, démarré, arrêté ou géré comme un service Docker ETHAN**
2. ETHAN doit seulement communiquer avec Ollama existant
3. `api = healthy` doit signifier "API fonctionne", pas "toutes les dépendances fonctionnent"

### Corrections alignées

| Ancienne correction (P0) | Correction révisée |
|---|---|
| ❌ Ajouter un service `ollama` dans docker-compose.yml | ✅ **Ne PAS ajouter de service Ollama** — Ollama reste sur l'hôte |
| ❌ `OLLAMA_BASE_URL=http://ollama:11434` | ✅ `OLLAMA_BASE_URL=http://172.20.0.1:11434` (adresse du gateway ethan-core vu depuis le conteneur) |
| ❌ Rebuild API | ✅ Corrections network + code |

### Corrections réelles

**1. Healthcheck — séparer LIVENESS et READINESS (P3)**
```yaml
healthcheck:
  test: ["CMD", "curl", "-fsS", "http://localhost:8000/health/live"]   # Liveness : process répond
```
Le `depends_on` et la readiness orchestrated doivent utiliser `/health/ready` (dépendances : NATS + pg + redis). Ollama ne doit **jamais** conditionner la readiness de l'API.

**2. Démarrage non-bloquant (responsabilité du ProviderManager)**
- Dans `core/llm/providers/ollama.py`, réduire le timeout du client httpx : `httpx.AsyncClient(timeout=5.0)` au lieu de `timeout=300.0`
- OU lancer `provider.initialize()` + `list_models()` en tâche de fond (`asyncio.create_task`) pour ne pas bloquer le lifespan
- L'API doit démarrer même si Ollama est injoignable ; le provider sera dégradé (modèles absents) mais l'API healthy

**3. Réseau pour joindre Ollama hôte (P2)**
- Ouvrir le port 11434 pour les réseaux Docker dans UFW :
  - `sudo ufw allow from 172.20.0.0/16 to any port 11434 proto tcp`
  - `sudo ufw allow from 172.17.0.0/16 to any port 11434 proto tcp`
- Configurer `OLLAMA_BASE_URL=http://172.20.0.1:11434` (gateway du réseau `ethan-core`)
- Cette correction est nécessaire uniquement si l'utilisateur veut réellement utiliser les modèles LLM via l'API
- Sans cette ouverture, Ollama reste une dépendance optionnelle non bloquante (correction 2)

**4. Alignement avec l'architecture cible**
```
HOST
 └── Ollama (indépendant, non géré par ETHAN)
       ↑
       │ permettre (UFW) + URL gateway
       │
ETHAN API (conteneur)
       ↑
       │
ETHAN WebUI
```

## 17. Conclusion

L'API ETHAN **n'est pas cassée**. Elle est fonctionnelle et healthy une fois démarrée. Le problème est un **démarrage trop lent** (~2min15s) causé par :

1. **P0–révisé** : le démarrage de l'API est bloqué par `_register()` qui attend Ollama pendant 2min15s (le conteur est sur ethan-core, `host.docker.internal` est mappé au bridge par défaut injoignable + UFW bloque le port 11434)
2. **P3** : le HEALTHCHECK Docker est un readiness (dépend de NATS) au lieu d'un liveness, avec un start_period trop court (10s vs 2min15s de démarrage)

Correction de principe :
- **Ne pas** ajouter un service Ollama Docker — Ollama reste hôte indépendant
- **Séparer** liveness (`/health/live` pour Docker) et readiness (`/health/ready` pour le superviseur)
- **Rendre le démarrage de l'API non-bloquant** : le provider LLM ne doit pas bloquer le lifespan
- **Ouvrir UFW (si besoin)** et configurer `OLLAMA_BASE_URL=http://172.20.0.1:11434` pour joindre Ollama hôte

Avec ces corrections, l'API démarre en < 30s même si Ollama est absent, et le HEALTHCHECK actuel (ou un healthcheck `/health/live`) suffit.
