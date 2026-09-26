# Installation d'ETHAN — Debian 13 (Trixie)

Procédure complète, exécutable de bout en bout : clone → configuration →
démarrage → vérification (santé, login, chat réel, projets).
Durée estimée : ~10 minutes (hors téléchargement d'images et de modèles).

> **Principe** : ETHAN ne embarque **aucun LLM**. Un **Ollama externe**
> (installé sur l'hôte) fournit l'inférence. La WebUI est une interface
> parmi d'autres : tout tourne sans elle (seule la vérification visuelle
> en a besoin).

---

## 1. Prérequis système

| Besoin | Version | Vérification | Installation |
|---|---|---|---|
| Docker Engine | ≥ 24 | `docker --version` | `curl -fsSL https://get.docker.com \| sh` |
| Docker Compose | v2 (plugin) | `docker compose version` | inclus avec Docker Engine |
| Python | ≥ 3.10 | `python3 --version` | `sudo apt install python3` (3.13 sur Trixie) |
| Node.js + npm | ≥ 20 | `node --version` | uniquement pour le dev WebUI local |
| curl, git | — | `curl --version` | `sudo apt install curl git` |
| Ollama (hôte) | — | `ollama --version` | voir §2 |
| RAM / disque | ≥ 4 Go / ≥ 10 Go | `free -h && df -h` | — |

Le lancement **via Docker** n'exige ni pip ni npm sur l'hôte ; Python sert
aux scripts de vérification (smoke, parsing JSON) et aux tests.
`./ethan install` (venv + npm + systemd) est réservé au mode dev local.

Ports utilisés par défaut (tous liés en `127.0.0.1` — jamais exposés au
réseau) : voir §7.

---

## 2. Ollama externe (obligatoire — jamais dans Docker)

ETHAN **ne définit aucun service Ollama** dans ses fichiers compose
(`docker-compose.yml`, `docker-compose.dev.yml`, `docker-compose.prod.yml`).
L'inférence est consommée depuis l'hôte :

```bash
# Installation (script officiel)
curl -fsSL https://ollama.com/install.sh | sh

# Démarrage du service + téléchargement du modèle par défaut
ollama serve &            # (ou : sudo systemctl enable --now ollama)
ollama pull llama3.1      # ~4,7 Go
ollama list               # doit afficher llama3.1:latest
```

Le conteneur `api` rejoint l'hôte via `host.docker.internal`
(déclaré en `extra_hosts: host-gateway`). Configuration dans `.env` :

```bash
OLLAMA_BASE_URL=http://host.docker.internal:11434   # défaut — ne pas changer
OLLAMA_DEFAULT_MODEL=llama3.1                       # modèle actif
```

Vérification depuis l'intérieur du conteneur (le smoke le fait déjà) :

```bash
docker compose exec -T api curl -sf http://host.docker.internal:11434/api/tags
```

---

## 3. Cloner et configurer

```bash
git clone git@github.com:seclib/Ethan.git
cd Ethan

cp .env.example .env
```

Éditer `.env` (valeurs minimales) :

```bash
# Sécurité — obligatoire avant toute mise en service
JWT_SECRET=$(openssl rand -hex 32)          # remplace le placeholder
POSTGRES_PASSWORD=<mot-de-passe-fort>
REDIS_PASSWORD=<mot-de-passe-fort>

# Ollama (§2) — les défauts conviennent
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_DEFAULT_MODEL=llama3.1
```

- `.env` n'est **jamais commité** (`.gitignore`).
- Aucun secret en clair dans le code, les logs ou les événements.
- Les clés optionnelles (`OPENAI_API_KEY`, `GRAFANA_*`, ports…) sont
  documentées en §7-§8.

---

## 4. Démarrage

```bash
chmod +x ethan                      # au besoin
./ethan preflight                   # dépendances, ports libres, ressources
./ethan pull-images                 # pulls séquentiels avec retries
./ethan up                          # infra → santé → migrations → Core → plugins → WebUI
./ethan wait-for-services           # attend /health/ready de l'API
./ethan status                      # 8/8 healthy attendu
```

`./ethan up` exécute déjà le préflight, les pulls, l'infra, les
healthchecks, les migrations et le démarrage complet ; les étapes
séparées ci-dessus servent à diagnostiquer précisément où un problème
surviendrait.

Résultat attendu :

```text
✓ ethan-nats      ✓ ethan-redis      ✓ ethan-postgres   ✓ ethan-pg_backup
✓ ethan-api       ✓ ethan-kernel     ✓ ethan-modules    ✓ ethan-ui
```

**Accès** : WebUI → <http://localhost:3001> · API → <http://localhost:8000>
· Swagger → <http://localhost:8000/docs>

---

## 5. Vérification de bout en bout

### 5.1 Smoke automatisé (recommandé)

```bash
./ethan smoke                 # ou : make smoke
# options : --skip-llm (sans Ollama)  --timeout 300 (modèle froid)
```

Le smoke vérifie réellement, contre la stack tournée :

1. **Stack** — les 8 conteneurs sont `healthy` ;
2. **Santé** — `GET /health`, `/health/ready` (status=ok), `/v1/version`,
   WebUI `GET /` ;
3. **Ollama** — joignable *depuis le conteneur api*
   (`host.docker.internal:11434`) et modèle `OLLAMA_DEFAULT_MODEL` présent ;
4. **Auth** — `POST /auth/register` puis `POST /auth/login` → JWT réel
   (compte local `ethan-smoke`, voir §8) ;
5. **Chat** — `POST /v1/chat/completions` : inférence **réelle** via
   Ollama (timeout 180 s pour le premier chargement du modèle) ;
6. **Chats** — création, message persisté (`GET …/messages` ≥ 1),
   suppression (`/chats`) ;
7. **Projets** — CRUD complet `GET/POST/PATCH/DELETE /v1/projects`
   (le rôle `standard` détient la permission `memory`).

Codes de sortie : `0` conforme · `1` échec · `2` stack hors ligne ·
`3` python3 manquant.

### 5.2 Vérifications manuelles (WebUI)

1. Ouvrir <http://localhost:3001> ;
2. Se connecter (créer un compte via `/register` ou compte existant) ;
3. Envoyer un message : la réponse doit afficher **ETHAN SMOKE OK** à
   l'envers ou toute réponse du modèle (preuve d'inférence) ;
4. Créer un projet → le voir dans le sélecteur → le supprimer ;
5. Recharger la page : la conversation persiste (`/chats/{id}/messages`).

### 5.3 Tests automatisés (optionnels)

```bash
pytest tests/test_boot.py -v                 # boot + health (skip si stack à l'arrêt)
pytest tests/test_features_deployed.py -v    # 18 capacités contre l'API réelle
pytest tests/test_api_contract_p0.py tests/test_api_contract_domains.py -v
```

---

## 6. Endpoints de santé (healthchecks)

### Du host (vérification opérateur)

| Service | Endpoint | Attendu |
|---|---|---|
| API | `GET http://localhost:8000/health` | `{"status":"ok","service":"api"}` |
| API | `GET http://localhost:8000/health/ready` | `{"status":"ok"}` (dépendances connectées) |
| API | `GET http://localhost:8000/health/detailed` | checks `nats`/`redis`/`postgresql` = `connected` |
| API | `GET http://localhost:8000/v1/version` | 200 + version |
| Kernel | `GET http://localhost:8080/health/ready` | `{"running":true}` |
| NATS | `GET http://localhost:8222/healthz` | 200 |
| WebUI | `GET http://localhost:3001/` | 200 |

### Healthchecks Docker (auto-contrôle des conteneurs)

Chaque service du compose déclare son healthcheck (`interval` 10-30 s,
`start_period` adapté). Vérification : `docker inspect <container>
--format '{{.State.Health.Status}}'` — `./ethan status` les résume.

---

## 7. Ports et variables d'environnement

### Ports host (tous liés en `127.0.0.1`)

Chaque mapping est **paramétrable via `.env`** — mêmes clés dans
`docker-compose.yml` et `scripts/ethan-lib.sh` (priorité : variable
d'env > .env > défaut) :

| Clé (`.env`) | Défaut | Service |
|---|---|---|
| `ETHAN_WEBUI_PORT` | `3001` | WebUI (côté host ; le conteneur reste en 3001) |
| `ETHAN_API_PORT` | `8000` | API Gateway |
| `ETHAN_KERNEL_PORT` | `8080` | Core Kernel |
| `NATS_PORT` | `4222` | NATS (messaging) |
| `NATS_MONITOR_PORT` | `8222` | NATS (monitoring /healthz) |
| `NATS_ROUTE_PORT` | `6222` | NATS (cluster) |
| `REDIS_PORT` | `6379` | Redis |
| `POSTGRES_PORT` | `5432` | PostgreSQL |

Les ports **internes** (URLs Docker type `postgres:5432`, `api:8000`,
`http://api:8000` côté WebUI) ne changent jamais : seul le côté host
l'est. Ne pas attribuer deux services au même port.

> ⚠ `./ethan up` (rapport final) et son healthcheck NATS affichent encore
> `3001`/`8222` en dur : fichiers WIP non modifiables en l'état. En cas de
> surcharge de `ETHAN_WEBUI_PORT` / `NATS_MONITOR_PORT`, se fier à
> `./ethan status` et `./ethan doctor`.

### Variables principales

| Clé | Rôle | Défaut / exemple |
|---|---|---|
| `JWT_SECRET` | Signature JWT — **obligatoire** | `$(openssl rand -hex 32)` |
| `JWT_EXPIRY_HOURS` | Durée de vie des tokens | `24` |
| `POSTGRES_PASSWORD` | Mot de passe base | — (à définir) |
| `REDIS_PASSWORD` | Mot de passe Redis | — (à définir) |
| `DATABASE_URL` | URL Postgres interne | `postgresql://ethan:${POSTGRES_PASSWORD}@postgres:5432/ethan` |
| `OLLAMA_BASE_URL` | Ollama vu du conteneur api | `http://host.docker.internal:11434` |
| `OLLAMA_DEFAULT_MODEL` | Modèle actif | `llama3.1` |
| `OPENAI_API_KEY` | Provider cloud optionnel | vide |
| `LOG_LEVEL` / `LOG_FORMAT` | Logging | `INFO` / `json` |

Observabilité (option `--observability`) : `GRAFANA_PORT`,
`PROMETHEUS_PORT`, `LOKI_PORT` ; vector stores dev : `QDRANT_PORT`,
`QDRANT_GRPC_PORT`, `CHROMADB_PORT`.

---

## 8. Comptes et rôles

- `POST /auth/register` crée un compte **`standard`**
  (permissions : read, write, chat, **memory**, files, agents, plugins,
  settings) — suffisant pour chat, projets et conversations.
- `admin` : toutes les permissions (création via `./ethan install` ou
  `python3 -m interfaces.cli.main`).
- Le smoke utilise un compte dédié **`ethan-smoke`** (mot de passe
  `smoke-ethan-2026` ; surcharge : `ETHAN_SMOKE_USER` /
  `ETHAN_SMOKE_PASSWORD`) : créé en base au premier run puis réutilisé.
  Suppression :
  `docker compose exec -T postgres psql -U ethan -d ethan -c "DELETE FROM users WHERE username='ethan-smoke';"`

---

## 9. Arrêt, redémarrage, rollback

```bash
./ethan status                  # état
./ethan restart                 # redémarrage progressif
./ethan down                    # arrêt progressif (SIGTERM 30 s) — données préservées
./ethan down && ./ethan up      # redémarrage complet (rollback opérationnel)
docker compose down -v          # ⚠ DÉSTRUCTIF : supprime aussi les volumes (données)
```

**Rollback applicatif** (retour à une version précédente) :

```bash
git log --oneline -5            # repérer le commit
git revert <sha>                # ou : git checkout <sha> -- <fichiers>
./ethan restart
./ethan smoke                   # re-vérification obligatoire
```

Les volumes (`ethan-postgres-data`, `ethan-redis-data`…) survivent à
`./ethan down` : un rollback ne touche jamais les données, sauf
`docker compose down -v` explicite.

---

## 10. Dépannage

| Symptôme | Cause probable | Action |
|---|---|---|
| `preflight` : port OCCUPÉ | service concurrent | `sudo ss -tlnp \| grep ':<port>'` ou surcharger la clé de port (§7) |
| `api` unhealthy / login 503 | Postgres pas prêt au 1er boot | `./ethan restart api && ./ethan wait-for-services` |
| Chat → 502/timeout | Ollama hors ligne ou modèle absent | `ollama list`, `ollama pull llama3.1`, vérifier `OLLAMA_BASE_URL` |
| Chat → modèle introuvable | `OLLAMA_DEFAULT_MODEL` ≠ modèle installé | aligner la clé sur `ollama list` |
| WebUI injoignable | build Next.js en cours ou port surchargé | `docker compose logs ui --tail 50`, vérifier `ETHAN_WEBUI_PORT` |
| `host.docker.internal` inconnu | Docker sans `host-gateway` | le compose le déclare (`extra_hosts`) ; vérifier `docker version` |
| JWT « invalid » après regen | `JWT_SECRET` modifié | redémarrer l'api et se re-connecter |
| Healthcheck NATS en échec | démarrage lent | `./ethan wait-for-services docker:nats` |

Logs : `./ethan logs <service>` · `docker compose logs -f api` ·
diagnostic complet : `./ethan doctor`.

---

## 11. Limitations connues

1. **`.env.example` et `scripts/cmd-up.sh` sont des fichiers WIP**
   (changes en cours) : les clés de ports de §7 ne sont pas encore
   listées dans `.env.example`, et le rapport final de `./ethan up`
   affiche `3001` en dur. Les valeurs par défaut étant inchangées, aucun
   impact tant qu'on ne surcharge pas les ports.
2. **CI** : `uv.lock`/`package-lock.json` existent mais l'CI installe via
   `pip install -e ".[server,dev]"` (pas de reproducibilité stricte de
   lockfile) — dette tracée, hors périmètre de cette procédure.
3. `docker-compose.dev.yml` n'ajoute que Qdrant/ChromaDB ; le « profil
   `llm` » mentionné historiquement n'existe pas dans les fichiers
   compose racine — Ollama reste strictement externe (§2).


