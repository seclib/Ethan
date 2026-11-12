# Stratégie de Tests ETHAN

## Objectif
Chaque modification ETHAN doit pouvoir être validée automatiquement.

## Fichiers de tests

### Shell (bash)

- **`test_boot.sh`** — Vérifie les prérequis système avant démarrage :
  - Docker installé
  - Docker Compose v2 disponible
  - `docker-compose.yml` présent et valide
  - Ports requis libres (8000, 8080, 3000, 4222, 6379, 5432)
  - Syntaxe du compose valide

- **`test_runtime.sh`** — Vérifie le runtime après démarrage :
  - API health endpoint (`/health`)
  - NATS healthz
  - Redis ping
  - PostgreSQL ready
  - Skip si services non démarrés

- **`test_docker.sh`** — Vérifie l'état Docker :
  - Docker daemon actif
  - Pas de conteneurs en erreur (exited/dead/restarting)
  - Réseau `ethan_default` présent

- **`test_cli.sh`** — Vérifie les commandes CLI :
  - `ethan status`
  - `ethan doctor`
  - `ethan plugin --help`
  - `ethan service status`
  - Commande inconnue rejetée

### Python (pytest)

- **`test_core.py`** — Vérifie les composants core :
  - Imports core (`kernel`, `bootstrap`, `bus`, `state`, `ethan_types`)
  - Module diagnostic fonctionnel
  - Registry CLI détecte toutes les commandes
  - Ports disponibles

## Exécution

```bash
# Tests prérequis (sans services démarrés)
bash tests/test_boot.sh

# Tests Docker (avec services démarrés)
bash tests/test_docker.sh
bash tests/test_runtime.sh

# Tests Python
python3 tests/test_core.py

# Tests CLI
bash tests/test_cli.sh
```

## Intégration CI

Ces tests peuvent être ajoutés au workflow GitHub Actions pour valider chaque PR.