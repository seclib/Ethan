# ETHAN — Lanceur officiel

## Usage

```bash
./ethan <commande> [options]
```

## Commandes

| Commande | Description | Options |
|----------|-------------|--------|
| `install` | Installer ETHAN (dépendances + config) | — |
| `up` | Démarrer les services Docker | `[service...]` |
| `down` | Arrêter les services Docker | `[service...]` |
| `restart` | Redémarrer les services | `[service...]` |
| `status` | État des services | `[service...]` |
| `doctor` | Diagnostiquer l'installation | — |
| `logs` | Afficher les logs | `[service...] [-f] [--tail=N]` |
| `api` | Lancer l'API Gateway en dev | `[--port=8000] [--reload]` |
| `webui` | Lancer l'interface web (dev) | `[--build] [--port=3000]` |
| `cli` | Lancer le CLI | `[arguments...]` |
| `desktop` | Lancer l'application desktop | `[--dev]` |
| `update` | Mettre à jour ETHAN | `[--branch=main]` |
| `help` | Afficher l'aide | — |

## Architecture

```
ethan/                    ← racine
├── ethan                 ← dispatcher (exécutable)
├── scripts/
│   ├── ethan-lib.sh      ← bibliothèque commune (couleurs, helpers)
│   ├── cmd-install.sh    ← installation
│   ├── cmd-up.sh         ← docker compose up
│   ├── cmd-down.sh       ← docker compose down
│   ├── cmd-restart.sh    ← docker compose restart
│   ├── cmd-status.sh     ← docker compose ps + infos
│   ├── cmd-doctor.sh     ← diagnostic complet
│   ├── cmd-logs.sh       ← docker compose logs
│   ├── cmd-webui.sh      ← next dev / next start
│   ├── cmd-cli.sh        ← python CLI
│   ├── cmd-desktop.sh    ← desktop (Electron / Tauri)
│   └── cmd-update.sh     ← git pull + rebuild
```

## Exemples

```bash
# Démarrer tous les services (Docker)
./ethan up

# Démarrer seulement l'API et la base
./ethan up api postgres

# Lancer l'API en dev local
./ethan api

# Lancer le frontend en dev (auto-démarre l'API si absente)
./ethan webui --port=4000

# Diagnostic complet
./ethan doctor

# Mise à jour depuis une branche spécifique
./ethan update --branch=develop
```

## Séquence de démarrage automatique

### ./ethan webui (dev local)

1. Vérifie Node.js (`require_node`)
2. Installe les dépendances frontend si nécessaire
3. Vérifie si l'API répond sur `http://localhost:8000/api/v1/version`
4. Si l'API est absente, lance `./ethan api` en arrière-plan
5. Attend le healthcheck HTTP (timeout 30s)
6. Lance Next.js en dev sur `http://localhost:3000`

Résultat :
- Frontend : `http://localhost:3000`
- API : `http://localhost:8000`

### ./ethan api (dev local)

1. Vérifie Python 3 (`require_python`)
2. Crée le venv `.venv` si absent
3. Installe les dépendances avec `pip install -e ".[server,dev]"`
4. Lance Uvicorn : `api.main:app` sur le port 8000
5. Affiche les logs dans `logs/api.log`

### ./ethan up (Docker)

1. Vérifie Docker (`require_docker`)
2. Lance `docker compose up -d`
3. Affiche les ports :
   - Frontend : `http://localhost:3000`
   - API : `http://localhost:8000`
   - NATS : `http://localhost:8222`

### ./ethan doctor (diagnostic complet)

Vérifie **réellement** l'opérationnalité de chaque composant :

**Environnement**
- ETHAN_ROOT, variables d'environnement
- Python 3, Node.js, npm, Docker

**Imports Python**
- `core`, `core.kernel`, `sdk`, `runtime`, `plugins`

**Docker**
- Daemon, Compose, images, containers, volumes, réseaux

**Services Docker**
- NATS, Redis, PostgreSQL, API Gateway, Core Kernel, WebUI

**Healthchecks HTTP**
- `/api/v1/version`, `/api/v1/health`
- `/docs` (Swagger), `/api/v1/events/ws` (WebSocket)
- Connectivité WebUI → API

**Core / SDK**
- Import `CognitiveKernel`
- Imports SDK : `event`, `autonomy`, `learning`, `module`, `goals`, `metacognition`

**Plugins / Frontend / CLI**
- Répertoires présents
- `node_modules` installé

**Résultat**
- PASS / WARNING / FAIL pour chaque test
- Compteurs globaux
- Corrections suggérées en cas d'échec

### ./ethan status

Affiche l'état des services Docker et vérifie :
- Containers Docker (NATS, Redis, PostgreSQL, API, Core, WebUI)
- URL accessibles pour l'API et le WebUI

## Architecture

```
ethan/                    ← racine
├── ethan                 ← dispatcher (exécutable)
├── scripts/
│   ├── ethan-lib.sh      ← bibliothèque commune (couleurs, helpers)
│   ├── cmd-install.sh    ← installation
│   ├── cmd-up.sh         ← docker compose up
│   ├── cmd-down.sh       ← docker compose down
│   ├── cmd-restart.sh    ← docker compose restart
│   ├── cmd-status.sh     ← état des services
│   ├── cmd-doctor.sh     ← diagnostic complet
│   ├── cmd-logs.sh       ← docker compose logs
│   ├── cmd-api.sh        ← uvicorn api.main:app
│   ├── cmd-webui.sh      ← next dev / next start
│   ├── cmd-cli.sh        ← python CLI
│   ├── cmd-desktop.sh    ← desktop (Electron / Tauri)
│   └── cmd-update.sh     ← git pull + rebuild
```

## Design

Le lanceur suit la charte graphique définie dans `.clinerules/CLI_DESIGN.md` :
- `◆` pour les sections (bleu)
- `✓` / `✗` pour succès/erreur
- `ℹ` pour les informations
- `→` pour les actions
- `⏱` pour les timings
- Couleurs ANSI 16 couleurs (terminal-safe)