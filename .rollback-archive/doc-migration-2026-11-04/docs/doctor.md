# ETHAN Doctor — Diagnostic de santé

## Vue d'ensemble

La commande `./ethan doctor` effectue un diagnostic complet du système ETHAN. Elle vérifie que chaque composant est **réellement opérationnel**, pas seulement présent.

## Usage

```bash
# Diagnostic standard
./ethan doctor

# Mode verbeux (détails supplémentaires)
./ethan doctor --verbose

# Sortie JSON (pour intégration/automatisation)
./ethan doctor --json

# Aide
./ethan doctor --help
```

## Checks effectués

### 1. Environnement
- ✅ Variable `ETHAN_ROOT` définie
- ✅ `ETHAN_ROOT` dans `PATH`
- ✅ `PYTHONPATH` configuré
- ✅ `NODE_ENV` défini
- ✅ virtualenv présent et activé
- ✅ Versions : Python 3, Node.js, npm

**En cas d'échec** : La cause, la commande de correction, le fichier concerné et la priorité sont affichés.

### 2. Imports Python
Chaque module est testé individuellement :
- ✅ `core` → Core Kernel
- ✅ `core.kernel` → CognitiveKernel
- ✅ `sdk` → SDK modules
- ✅ `runtime` (optionnel)
- ✅ `plugins` (optionnel)

### 3. Docker
- ✅ Docker CLI installé
- ✅ Docker daemon actif
- ✅ Docker Compose disponible
- ✅ `docker-compose.yml` présent et syntaxe valide
- ✅ Images ETHAN construites
- ✅ Containers en cours d'exécution
- ✅ Volumes présents
- ✅ Réseau `ethan-core` actif

### 4. Services Docker
Chaque service est vérifié :
- ✅ Container en cours d'exécution
- ✅ Healthcheck Docker
- ✅ Port exposé

Services vérifiés :
- NATS (ethan-nats:4222)
- Redis (ethan-redis:6379)
- PostgreSQL (ethan-postgres:5432)
- API Gateway (ethan-api:8000)
- Core Kernel (ethan-kernel:8080)
- Cognitive Modules (ethan-modules)
- WebUI (ethan-ui:3000)

### 5. Connectivité HTTP
- ✅ API Gateway répond sur `/`
- ✅ `/health` accessible
- ✅ `/api/v1/version` accessible
- ✅ Swagger UI (`/docs`) accessible
- ✅ WebSocket endpoint (`/api/v1/events/ws`)
- ✅ WebUI répond sur `/`
- ✅ WebUI peut contacter l'API

### 6. Services d'infrastructure
Tests de connectivité réels :
- ✅ NATS : port 4222 ouvert + monitoring 8222
- ✅ Redis : port 6379 ouvert + PING/PONG
- ✅ PostgreSQL : port 5432 ouvert + connexion + requête SQL

### 7. Core
- ✅ Import `CognitiveKernel`
- ✅ Providers détectés
- ✅ Plugins enregistrés

### 8. SDK
- ✅ `sdk.event`
- ✅ `sdk.autonomy`
- ✅ `sdk.learning`
- ✅ `sdk.module`
- ✅ `sdk.goals`
- ✅ `sdk.metacognition`
- ✅ Compatibilité SDK ↔ Core

### 9. CLI
- ✅ Répertoire CLI présent
- ✅ `./ethan` exécutable
- ✅ Commande `ethan doctor --help` fonctionne

### 10. WebUI (Frontend)
- ✅ Répertoire WebUI présent
- ✅ `package.json` présent
- ✅ `node_modules` installé
- ✅ Next.js configuré

## Résultats

Chaque test affiche :

```
✓ PASS    # Succès - le composant est opérationnel
⚠ WARNING # Avertissement - fonctionne mais avec limitations
✗ FAIL    # Échec - le composant n'est pas opérationnel
```

## En cas d'échec

Pour chaque échec, le doctor affiche :

```
→ Cause: <explication du problème>
→ Correction: <commande pour corriger>
→ Fichier: <fichier concerné>
→ Priorité: high|medium|low
```

### Exemple

```
✗ NATS : container absent ou arrêté
→ Cause: Le container ethan-nats n'est pas en cours d'exécution
→ Correction: docker compose up -d ethan-nats
→ Fichier: docker-compose.yml
→ Priorité: high
```

## Résumé final

```
◆ Résumé

  ✗ Problèmes détectés : 12 FAIL, 11 WARNING, 30 PASS

  ℹ Actions prioritaires :
  ℹ   1. Vérifier les logs : ./ethan logs
  ℹ   2. Diagnostic des services : docker compose ps
  ℹ   3. Redémarrer : ./ethan restart
  ℹ   4. Réinstaller : ./ethan install

  ⏱ 11:29:46
```

## Codes de sortie

- `0` : Aucun échec (système sain)
- `N` : Nombre d'échecs détectés

Cela permet d'utiliser le doctor dans des scripts CI/CD :

```bash
./ethan doctor || exit 1
```

## Architecture du diagnostic

```
┌─────────────────────────────────────────┐
│     ETHAN Doctor Diagnostic Flow        │
└─────────────────────────────────────────┘

1. Environnement (variables, outils)
   ├─ ETHAN_ROOT, PATH, PYTHONPATH
   ├─ Python, Node.js, npm
   └─ virtualenv

2. Imports Python (vérification réelle)
   ├─ core
   ├─ core.kernel (CognitiveKernel)
   ├─ sdk
   ├─ runtime (optionnel)
   └─ plugins (optionnel)

3. Docker (infrastructure)
   ├─ daemon
   ├─ compose
   ├─ images
   ├─ containers
   ├─ volumes
   └─ networks

4. Services Docker (containers)
   ├─ ethan-nats
   ├─ ethan-redis
   ├─ ethan-postgres
   ├─ ethan-api
   ├─ ethan-kernel
   ├─ ethan-modules
   └─ ethan-ui

5. Connectivité HTTP (tests réels)
   ├─ API Gateway (http://localhost:8000/)
   ├─ /health
   ├─ /api/v1/version
   ├─ /docs (Swagger)
   ├─ /api/v1/events/ws (WebSocket)
   ├─ WebUI (http://localhost:3000/)
   └─ WebUI → API connectivité

6. Services d'infrastructure
   ├─ NATS : port 4222 + monitoring
   ├─ Redis : port 6379 + PING
   └─ PostgreSQL : port 5432 + connexion SQL

7. Core
   ├─ Import CognitiveKernel
   ├─ Providers registry
   └─ Plugin registry

8. SDK
   ├─ Tous les modules SDK
   └─ Compatibilité SDK ↔ Core

9. CLI
   ├─ Répertoire présent
   ├─ Exécutable
   └─ Commande fonctionnelle

10. WebUI
    ├─ package.json
    ├─ node_modules
    └─ Next.js config
```

## Différences avec l'ancien doctor

| Ancien | Nouveau |
|--------|---------|
| Vérifie présence des processus | Vérifie opérationnalité réelle |
| Tests basiques (commande existe) | Tests de connectivité (port, HTTP, WebSocket) |
 | Aucune correction suggérée | Cause + correction + fichier + priorité |
| ~100 lignes | ~800 lignes |
| Pas de JSON | Sortie JSON pour intégration |
| Pas de verbosity | Mode `--verbose` |

## Intégration CI/CD

```yaml
# .github/workflows/doctor.yml
name: ETHAN Health Check
on: [push, pull_request]
jobs:
  doctor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start ETHAN
        run: ./ethan up
      - name: Run Doctor
        run: ./ethan doctor --json > doctor.json
      - name: Upload Results
        uses: actions/upload-artifact@v3
        with:
          name: doctor-report
          path: doctor.json
```

## Maintenance

Le doctor est maintenu dans `scripts/cmd-doctor.sh` avec sa bibliothèque partagée `scripts/ethan-lib.sh`.

Pour ajouter un nouveau check :

1. Ajouter une section dans `check_services()` ou créer une nouvelle fonction
2. Utiliser `check_pass()`, `check_warn()`, `check_fail()` pour les résultats
3. Utiliser `show_fix()` pour afficher les corrections
4. Appeler la nouvelle fonction dans `main()`

## Support

- Documentation : [docs/ethan-launcher.md](./ethan-launcher.md)
- Logs : `./ethan logs`
- Issues : https://github.com/ethan/Ethan/issues