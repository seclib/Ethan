# Boot depuis un système vierge

## Prérequis machine

### Matériel minimum
| Ressource | Minimum | Recommandé |
|-----------|---------|------------|
| RAM       | 4 Go    | 8 Go       |
| Disque    | 10 Go   | 20 Go      |
| CPU       | 2 cœurs | 4 cœurs    |

### Logiciels requis
```bash
# Docker (obligatoire)
docker --version                # Docker 24+ recommandé
docker compose version          # Docker Compose v2

# Python (pour le CLI ethan)
python3 --version               # Python 3.10+

# Node.js (pour le WebUI, optionnel)
node --version                  # Node 18+
npm --version

# Utilitaires (pour les healthchecks)
which curl nc wget              # Doivent être disponibles
```

## Installation

### 1. Cloner le dépôt
```bash
git clone git@github.com:seclib/Ethan.git
cd Ethan
```

### 2. Configurer l'environnement
```bash
cp .env.example .env
# Éditer .env avec vos mots de passe
# Variables minimales :
#   POSTGRES_PASSWORD= votremotdepasse
#   REDIS_PASSWORD= votremotdepasse
```

### 3. Lancer le boot
```bash
./ethan up
```

## Procédure de boot détaillée

### Étape 1 : Préflight
Le script `cmd-preflight.sh` vérifie automatiquement :
- Docker et Docker Compose disponibles
- Ports libres (8000, 8080, 4222, 6379, 5432)
- RAM ≥ 4 Go, disque ≥ 10 Go
- Si la stack est déjà en cours d'exécution, les vérifications de ports sont ignorées

### Étape 2 : Build des images Docker
Le build s'effectue en deux phases :
1. **Image de base Python** (`ethan/python-base`) — dépendances installées une seule fois
2. **Images spécifiques** (api, kernel, modules, pg_backup, ui) — héritent de l'image de base

### Étape 3 : Démarrage des services
L'ordre de démarrage est :
```
1. nats (message broker)       → healthy
2. redis (cache/state)         → healthy
3. postgres (persistence)      → healthy
4. api (API Gateway)            → healthy
5. kernel (moteur cognitif)    → healthy
6. modules (modules cognitifs) → healthy
7. pg_backup (backup DB)       → healthy
8. ui (WebUI)                  → healthy (optionnel)
```

### Étape 4 : Vérification

```bash
# Statut global
./ethan status
# Doit afficher 7/7 ou 8/8 services healthy

# Vérification API
curl http://localhost:8000/health
# → {"status":"ok","service":"api"}

# Vérification détaillée
curl http://localhost:8000/health/detailed
# → {"status":"ok","checks":{"nats":"connected","redis":"connected","postgresql":"connected"}}

# WebUI (si activé)
# http://localhost:3001
```

## Architecture des services

```
┌─────────────────────────────────────────────────────────┐
│                     ethan-core (réseau)                  │
│                                                         │
│  ┌─────────┐  ┌─────────┐  ┌──────────┐               │
│  │  nats   │  │  redis  │  │ postgres │               │
│  │ :4222   │  │ :6379   │  │ :5432    │               │
│  └────┬────┘  └─────────┘  └──────────┘               │
│       │                                                │
│  ┌────▼────┐  ┌──────────┐  ┌───────────┐             │
│  │  api    │  │  kernel  │  │  modules  │             │
│  │ :8000   │  │ :8080    │  │           │             │
│  └────────┘  └──────────┘  └───────────┘             │
│                                                         │
│  ┌──────────┐  ┌──────────┐                            │
│  │ pg_backup│  │    ui    │                            │
│  │          │  │ :3000    │                            │
│  └──────────┘  └──────────┘                            │
└─────────────────────────────────────────────────────────┘
```

## Healthchecks

Chaque service a un healthcheck qui vérifie sa fonctionnalité réelle :

| Service   | Healthcheck                                    | Intervalle |
|-----------|------------------------------------------------|------------|
| nats      | `nc -z localhost 4222`                         | 5s         |
| redis     | `redis-cli ping`                               | 5s         |
| postgres  | `pg_isready + SELECT 1`                        | 5s         |
| api       | `curl /health/detailed` (vérifie NATS+Redis+PG)| 10s        |
| kernel    | Connexion NATS avec `asyncio.wait_for`         | 10s        |
| modules   | Connexion NATS avec `asyncio.wait_for`         | 10s        |
| pg_backup | `pg_isready`                                   | 30s        |
| ui        | `curl http://localhost:3001`                   | 10s        |

## En cas d'échec

### Diagnostic rapide
```bash
# Logs détaillés
./ethan doctor --verbose

# Statut Docker
docker compose ps -a

# Logs d'un service spécifique
docker compose logs <service>
# Services : api, kernel, modules, nats, redis, postgres, pg_backup, ui
```

### Problèmes courants et solutions

#### 1. Ports déjà occupés
```bash
# Vérifier les ports
sudo lsof -i :8000 -i :8080 -i :4222 -i :6379 -i :5432

# Solution : arrêter les processus qui occupent les ports
# ou modifier les ports dans docker-compose.yml
```

#### 2. Image Docker stale
```bash
# Rebuild complet des images
docker compose build --no-cache
docker compose up -d --force-recreate
```

#### 3. Kernel crash — `ModuleRegistry` signature
```
Error: TypeError: ModuleRegistry.__init__() takes 3 positional arguments but 4 were given
```
Solution : le code est déjà corrigé dans `core/bootstrap.py`. Rebuild l'image kernel :
```bash
docker compose build --no-cache kernel
docker compose up -d --force-recreate kernel
```

#### 4. API unhealthy — `nats.connect(timeout=2)`
```
Error: Client.connect() got an unexpected keyword argument 'timeout'
```
Solution : healthcheck mis à jour pour utiliser `asyncio.wait_for`. Rebuild :
```bash
docker compose build --no-cache api
docker compose up -d --force-recreate api
```

#### 5. Modules crash — `No module named modules.launcher`
```
Error: No module named modules.launcher
```
Solution : le service modules a été corrigé pour utiliser `python -m core.modules`. Rebuild :
```bash
docker compose build --no-cache modules
docker compose up -d --force-recreate modules
```

#### 6. Kernel crash — `Event object has no attribute 'to_json'`
```
Error: AttributeError: 'Event' object has no attribute 'to_json'
```
Solution : image Docker stale. Rebuild :
```bash
docker compose build --no-cache kernel
docker compose up -d --force-recreate kernel
```

#### 7. Conflit de réseau Docker
```bash
# Vérifier les réseaux
docker network ls | grep ethan

# Solution : supprimer et recréer
docker network rm ethan_ethan-core
./ethan up
```

## Redémarrage complet

```bash
# Arrêt complet
./ethan down

# Nettoyage des volumes (⚠️ supprime les données)
docker compose down -v

# Redémarrage
./ethan up
```

## Tests de validation

```bash
# Installer les dépendances de test
pip install pytest requests pytest-asyncio

# Lancer les tests de boot
pytest tests/test_boot.py -v

# Vérifications manuelles
nc -zv localhost 8000      # API doit répondre
curl http://localhost:8000/health  # Doit retourner 200
curl http://localhost:8000/health/detailed  # Doit retourner 200
```

## Comptes et authentification

### Compte par défaut (installation vierge)

La migration `deploy/postgres/migrations/003_create_users_table.sql` crée un compte admin :

| Champ | Valeur (dev uniquement) |
|---|---|
| Utilisateur | `admin` |
| Mot de passe | `admin` |
| Rôle | `admin` |

> ⚠️ **À changer immédiatement en production** (voir `docs/hardening.md`).
> L'activation de la 2FA TOTP est disponible sur la page `/security` de la WebUI
> ou via `POST /auth/2fa/setup` + `/auth/2fa/confirm`.

### Instance de développement actuelle

Le mot de passe du compte `admin` a été réinitialisé le 2026-08-24 :

| Champ | Valeur |
|---|---|
| Utilisateur | `admin` |
| Mot de passe | `admin123` |

### Réinitialiser le mot de passe admin

Générer un hash bcrypt dans le conteneur API (qui dispose de bcrypt) puis
l'appliquer en base :

```bash
docker exec ethan-api python3 -c \
  "import bcrypt; print(\"UPDATE users SET password_hash='\" + \
   bcrypt.hashpw(b'<NOUVEAU_MOT_DE_PASSE>', bcrypt.gensalt()).decode() + \
   \"' WHERE username='admin';\")" > /tmp/pwd.sql

docker exec -i ethan-postgres psql -U ethan -d ethan < /tmp/pwd.sql
rm /tmp/pwd.sql   # ne pas laisser le hash traîner dans /tmp
```

### Notes importantes

- La base PostgreSQL vit sur le volume Docker `ethan_postgres_data` :
  les mots de passe **persistent** aux redémarrages et rebuilds d'images.
- En revanche, `docker compose down -v` (suppression des volumes) repart
  d'une base vierge → la migration 003 recrée `admin` / `admin`.
- Le login refuse les comptes avec 2FA activée si aucun code TOTP valide
  n'est fourni (`totp_code` dans le payload de `/auth/login`).

## Références

- [Documentation complète](INDEX.md)
- [Architecture](architecture.md)
- [Déploiement](deployment.md)
- [Runbook SRE](sre-runbook.md)
- [Hardening](hardening.md)