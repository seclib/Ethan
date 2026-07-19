# Guide d'Implémentation P0 — Actions Critiques

**Objectif** : Corriger les problèmes bloquants qui empêchent le bon fonctionnement du système.  
**Date** : 2026-07-19  
**Priorité** : P0 (Critique)  
**Temps estimé** : 2-4h  
**Responsable** : Équipe Core

---

## Vue d'ensemble des actions P0

```
┌─────────────────────────────────────────────────────────────┐
│                    Actions P0 à implémenter                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ✅ P0-1 : Corriger healthchecks Docker                    │
│     └─ Fichier : docker-compose.yml (ligne 135)            │
│     └─ Action : /v1/health → /health                       │
│     └─ Status : DÉJÀ CORRIGÉ                               │
│                                                             │
│  ⏳ P0-2 : Mettre à jour README.md                          │
│     └─ Fichier : README.md (lignes 5-8, 28-43, 557+)      │
│     └─ Action : Corriger gRPC → HTTP, health endpoint      │
│     └─ Status : À FAIRE                                    │
│                                                             │
│  ✅ P0-3 : Ajouter logs explicites dans ./ethan up         │
│     └─ Fichier : scripts/cmd-up.sh                         │
│     └─ Action : Logs + vérifications + attente healthchecks │
│     └─ Status : DÉJÀ CORRIGÉ                               │
│                                                             │
│  ✅ P0-4 : Configurer PYTHONPATH dans launcher             │
│     └─ Fichier : ethan (ligne 10)                          │
│     └─ Action : Ajouter PYTHONPATH dans le launcher        │
│     └─ Status : DÉJÀ CORRIGÉ                               │
│                                                             │
│  ✅ P0-5 : Améliorer ./ethan status                        │
│     └─ Fichier : scripts/cmd-status.sh                     │
│     └─ Action : Tests de connectivité réelle               │
│     └─ Status : DÉJÀ CORRIGÉ                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Actions déjà complétées

Les actions suivantes ont été implémentées lors des sessions précédentes :

### ✅ P0-1 : Healthchecks Docker corrigés

**Fichier** : `docker-compose.yml`  
**Modification** :

```yaml
# AVANT (ligne 135)
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/v1/health"]

# APRÈS
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
```

**Validation** :

```bash
# Tester le healthcheck
curl -f http://localhost:8000/health

# Vérifier que Docker utilise le bon endpoint
docker compose ps --services --filter "health=healthy"
```

---

### ✅ P0-3 : Logs explicites dans `./ethan up`

**Fichier** : `scripts/cmd-up.sh`  
**Modifications** :

1. **Ajout de logs de débogage** :

```bash
info "Répertoire ETHAN : ${ETHAN_ROOT}"
info "Fichier compose : ${COMPOSE_FILE}"
info "Services à démarrer : ${SERVICES:-<tous>}"
```

2. **Vérification du fichier docker-compose.yml** :

```bash
if [ ! -f "${COMPOSE_FILE}" ]; then
    error "Fichier docker-compose.yml introuvable : ${COMPOSE_FILE}"
    exit 1
fi
success "Fichier docker-compose.yml trouvé"
```

3. **Log explicite de la commande Docker** :

```bash
info "Exécution : docker compose -f \"${COMPOSE_FILE}\" up -d"
if ! docker_compose up -d; then
    error "Échec de 'docker compose up -d'"
    info "Vérifier les logs Docker : docker compose logs"
    exit 1
fi
success "Commande 'docker compose up -d' exécutée avec succès"
```

4. **Attente des healthchecks avec progression** :

```bash
info "Attente des healthchecks (cela peut prendre 30-60s)..."
MAX_WAIT=90
WAITED=0
SLEEP_INTERVAL=3

while [ "$WAITED" -lt "$MAX_WAIT" ]; do
    HEALTHY=$(docker_compose ps --services --filter "health=healthy" 2>/dev/null | wc -l)
    TOTAL=$(docker_compose ps --services 2>/dev/null | wc -l)
    
    if [ "$TOTAL" -gt 0 ] && [ "$HEALTHY" -eq "$TOTAL" ]; then
        success "Tous les healthchecks sont OK ($HEALTHY/$TOTAL)"
        break
    fi
    
    dim "  Progression : $HEALTHY/$TOTAL healthy, $RUNNING/$TOTAL running (${WAITED}s/${MAX_WAIT}s)"
    sleep "$SLEEP_INTERVAL"
    WAITED=$((WAITED + SLEEP_INTERVAL))
done
```

**Validation** :

```bash
# Tester ./ethan up
./ethan down
./ethan up

# Résultat attendu :
# - Logs explicites à chaque étape
# - Progression toutes les 3s
# - "Tous les healthchecks sont OK (7/7)"
```

---

### ✅ P0-4 : PYTHONPATH configuré dans le launcher

**Fichier** : `ethan` (ligne 9-10)  
**Modification** :

```bash
# AVANT
export ETHAN_ROOT="$(cd "$(dirname "$0")" && pwd)"

# APRÈS
export ETHAN_ROOT="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="${ETHAN_ROOT}:${PYTHONPATH:-}"
```

**Validation** :

```bash
# Tester que Python peut importer core
./ethan python3 -c "import core.kernel; print('OK')"

# Tester que Python peut importer sdk
./ethan python3 -c "import sdk.event; print('OK')"

# Tester que Python peut importer plugins
./ethan python3 -c "import plugins; print('OK')"
```

---

### ✅ P0-5 : `./ethan status` vérifie la connectivité réelle

**Fichier** : `scripts/cmd-status.sh`  
**Modifications** :

1. **Ajout de tests de connectivité pour chaque service** :

```bash
SERVICES_LIST=(
    "ethan-nats:NATS:4222"
    "ethan-redis:Redis:6379"
    "ethan-postgres:PostgreSQL:5432"
    "ethan-api:API Gateway:8000"
    "ethan-kernel:Core Kernel:8080"
    "ethan-modules:Cognitive Modules:—"
    "ethan-ui:WebUI:3000"
)
```

2. **Tests spécifiques par service** :

```bash
# NATS : port TCP
if nc -z localhost 4222 2>/dev/null; then
    success "$label : port $port répond"
fi

# Redis : PING/PONG
if redis-cli ping 2>/dev/null | grep -q "PONG"; then
    success "$label : PING répond"
fi

# PostgreSQL : connexion
if PGPASSWORD="${POSTGRES_PASSWORD:-ethan_dev_pass}" psql -h localhost -U ethan -d ethan -c "SELECT 1" &>/dev/null; then
    success "$label : connexion OK"
fi

# API Gateway : health endpoint
if curl -sf "http://localhost:${port}/health" >/dev/null 2>&1; then
    success "$label : /health répond"
fi

# WebUI : HTTP
if wait_for_http "http://localhost:${port}/" 3; then
    success "$label : répond"
fi
```

**Validation** :

```bash
# Tester ./ethan status
./ethan status

# Résultat attendu :
# - Chaque service affiche "healthy"
# - Tests de connectivité passent
# - "7/7 services opérationnels (healthy)"
```

---

## Action à compléter : P0-2

### ⏳ P0-2 : Mettre à jour README.md

**Fichier** : `README.md`  
**Sections à corriger** : 5-8, 28-43, 557+  
**Deadline** : 2026-07-26

---

### Problème 1 : Section 1.1 (ligne 5-8)

**ACTUEL** :
```markdown
> - `core` — Cerveau. Zéro UI. Zéro IO direct. Zéro dépendance OS/CLI. Expose gRPC.
> - `cli` — Terminal UI. Zéro logique cognitive. Client gRPC uniquement.
> - `plugins` — Extensions. Process indépendants. Connectés via NATS.
> - `interfaces` — Ponts vers le monde extérieur (API, Desktop, Shell, WebUI, MCP).
```

**PROBLÈME** : Mentionne gRPC, mais l'API est HTTP (FastAPI) + NATS.

**CORRECTION** :
```markdown
> - `core` — Cerveau. Zéro UI. Zéro IO direct. Zéro dépendance OS/CLI. Event-driven (NATS).
> - `cli` — Terminal UI. Zéro logique cognitive. Client NATS + HTTP.
> - `plugins` — Extensions. Process indépendants. Connectés via NATS.
> - `interfaces` — Ponts vers le monde extérieur (API, Desktop, Shell, WebUI, MCP).
```

---

### Problème 2 : Section 5 (ligne 28-43)

**ACTUEL** :
```markdown
**API exposée** :
- **gRPC** (port 50051) — `ProcessEvent`, `GetState`, `ExecuteTask`, `HealthCheck`
- **Python API** — `CognitiveKernel` injecté via dépendances
```

**PROBLÈME** : Port 50051 n'existe pas dans `docker-compose.yml`.

**CORRECTION** :
```markdown
**API exposée** :
- **HTTP REST** (port 8000) — `GET /health`, `GET /version`, `POST /api/v1/events`
- **WebSocket** (port 8000) — `WS /api/v1/events/ws`
- **Python API** — `CognitiveKernel` injecté via dépendances
```

---

### Problème 3 : Section 7.4 (ligne 557+)

**ACTUEL** :
```yaml
# Health endpoint
Endpoint: GET http://localhost:8080/health
```

**PROBLÈME** : Le healthcheck Docker utilise `/v1/health` (déjà corrigé), mais la documentation mentionne `/health` sans le préfixe correct.

**CORRECTION** :
```yaml
# Health endpoint
Endpoint: GET http://localhost:8000/health
```

---

### Procédure de correction

**Étape 1** : Sauvegarder le README actuel

```bash
cp README.md README.md.backup
```

**Étape 2** : Éditer le README.md

Utiliser un éditeur de texte ou `sed` pour corriger les sections.

**Option A : Avec sed**

```bash
# Corriger la section 1.1 (lignes 5-8)
sed -i '5,8s/gRPC/HTTP + NATS/' README.md

# Corriger la section 5 (ligne 28-43)
sed -i '28,43s/gRPC.*port 50051/HTTP REST (port 8000)/' README.md
sed -i '28,43s/ProcessEvent.*GetState/GET \/health, GET \/version/' README.md

# Corriger la section 7.4 (ligne 557+)
sed -i '557s/localhost:8080/localhost:8000/' README.md
```

**Option B : Édition manuelle**

1. Ouvrir `README.md` dans un éditeur
2. Aller à la ligne 5-8 et corriger
3. Aller à la ligne 28-43 et corriger
4. Aller à la ligne 557+ et corriger

**Étape 3** : Vérifier les corrections

```bash
# Vérifier que les mots "gRPC" ont disparu (sauf mention historique)
grep -n "gRPC" README.md

# Vérifier que les endpoints sont corrects
grep -n "localhost:8000" README.md

# Vérifier que la section API exposée est correcte
grep -A 3 "API exposée" README.md
```

**Étape 4** : Tester la documentation

```bash
# Générer la documentation (si mkdocs est utilisé)
mkdocs build

# Vérifier qu'il n'y a pas d'erreurs
mkdocs serve --dev-addr 127.0.0.1:8001
```

---

## Procédure complète de test P0

### Test 1 : Healthchecks

```bash
# Démarrer les services
./ethan up

# Vérifier les healthchecks
docker compose ps --services --filter "health=healthy"

# Tester l'endpoint de santé
curl -f http://localhost:8000/health
```

**Résultat attendu** : ✅ Tous les services healthy, `/health` répond 200

---

### Test 2 : Logs et connectivité

```bash
# Vérifier les logs de ./ethan up
./ethan down
./ethan up 2>&1 | head -30

# Vérifier ./ethan status
./ethan status

# Vérifier la connectivité
curl -f http://localhost:8000/health
curl -f http://localhost:8000/version
curl -f http://localhost:3000/
```

**Résultat attendu** : ✅ Logs explicites, tous les services connectés

---

### Test 3 : PYTHONPATH

```bash
# Tester les imports
./ethan python3 -c "import core; print('core OK')"
./ethan python3 -c "import sdk.event; print('sdk OK')"
./ethan python3 -c "import plugins; print('plugins OK')"
```

**Résultat attendu** : ✅ Tous les imports fonctionnent

---

### Test 4 : Documentation

```bash
# Vérifier le README
grep -n "gRPC" README.md | grep -v "historique" || echo "Aucune mention de gRPC"

# Vérifier les endpoints
grep -n "localhost:8000" README.md | head -5

# Générer la documentation
mkdocs build 2>&1 | tail -20
```

**Résultat attendu** : ✅ Documentation à jour, pas d'erreur de génération

---

## Checklist d'implémentation P0

### P0-1 : Healthchecks Docker ✅ DÉJÀ FAIT

- [x] Corriger `/v1/health` → `/health` dans `docker-compose.yml`
- [x] Tester avec `curl -f http://localhost:8000/health`
- [x] Vérifier que les healthchecks deviennent healthy

### P0-2 : Mettre à jour README.md ⏳ À FAIRE

- [ ] Corriger section 1.1 (gRPC → HTTP + NATS)
- [ ] Corriger section 5 (port 50051 → 8000)
- [ ] Corriger section 7.4 (localhost:8080 → localhost:8000)
- [ ] Ajouter section "Architecture réelle"
- [ ] Tester la génération de documentation

### P0-3 : Logs explicites dans `./ethan up` ✅ DÉJÀ FAIT

- [x] Ajouter logs de débogage
- [x] Ajouter vérification du fichier docker-compose.yml
- [x] Ajouter log de la commande Docker
- [x] Ajouter vérification du code de retour
- [x] Ajouter attente des healthchecks avec progression

### P0-4 : PYTHONPATH dans launcher ✅ DÉJÀ FAIT

- [x] Ajouter `export PYTHONPATH="${ETHAN_ROOT}:${PYTHONPATH:-}"`
- [x] Tester les imports (core, sdk, plugins)

### P0-5 : Améliorer `./ethan status` ✅ DÉJÀ FAIT

- [x] Ajouter tests de connectivité NATS (port TCP)
- [x] Ajouter tests Redis (PING/PONG)
- [x] Ajouter tests PostgreSQL (connexion + SELECT 1)
- [x] Ajouter tests API Gateway (/health + /version)
- [x] Ajouter tests WebUI (HTTP)

---

## Commandes rapides

### Démarrer et vérifier

```bash
# Démarrer les services
./ethan up

# Vérifier le status
./ethan status

# Tester la connectivité
curl -f http://localhost:8000/health
curl -f http://localhost:3000/

# Voir les logs
./ethan logs api
./ethan logs kernel
```

### Arrêter

```bash
./ethan down
```

### Tester les imports

```bash
./ethan python3 -c "import core.kernel; print('OK')"
./ethan python3 -c "import sdk.event; print('OK')"
```

---

## Support

- **Documentation** : `docs/service-orchestration.md`
- **Audit** : `docs/audit-ethan-up.md`
- **Résumé** : `docs/audit-ethan-up-RESUME.md`
- **Roadmap** : `docs/roadmap-P0.md`, `docs/roadmap-global.md`

---

## Prochaines étapes

1. **Implémenter P0-2** : Mettre à jour README.md
2. **Tester P0 complet** : Exécuter tous les tests de validation
3. **Valider par l'équipe** : Faire relire les modifications
4. **Passer à P1** : Décisions structurelles (runtime/, rust/, doublons)

**Dernière mise à jour** : 2026-07-19