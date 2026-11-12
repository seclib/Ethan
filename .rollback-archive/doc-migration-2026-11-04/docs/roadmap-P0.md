# Roadmap P0 — Actions Critiques (Immédiat)

**Objectif** : Corriger les problèmes bloquants qui empêchent le bon fonctionnement du système.

**Date de création** : 2026-07-19  
**Statut** : En attente d'implémentation  
**Propriétaire** : Équipe Core

---

## P0-1 : Corriger les healthchecks Docker

**Fichier concerné** : `docker-compose.yml`  
**Ligne** : 135 (service `api`)

### Problème

```yaml
# ACTUEL (INCORRECT)
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/v1/health"]
```

L'endpoint `/v1/health` n'existe pas. L'endpoint réel est `/health`.

### Solution

```yaml
# CORRIGÉ
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
```

### Validation

```bash
# Test manuel
curl -f http://localhost:8000/health

# Vérifier le healthcheck Docker
docker compose ps --services --filter "health=healthy"
```

### Impact

- **Avant** : Healthcheck échoue silencieusement, services déclarés healthy alors qu'ils ne sont pas prêts
- **Après** : Healthcheck fonctionnel, garantit que le service est réellement opérationnel

### Statut

- [x] **Identifié** (2026-07-19)
- [x] **Corrigé** dans `docker-compose.yml`
- [ ] **Testé** en environnement de production
- [ ] **Validé** par l'équipe

---

## P0-2 : Mettre à jour README.md

**Fichier concerné** : `README.md`  
**Lignes** : 5-8, 28-43, 557+

### Problèmes

1. **Ligne 5-8** : Promet gRPC mais l'API est HTTP (FastAPI)
2. **Ligne 28-43** : Mentionne gRPC (port 50051) mais ce port n'existe pas dans `docker-compose.yml`
3. **Ligne 557+** : Documente `/health` mais le healthcheck Docker utilise `/v1/health`

### Solution

 Remplacer la section "API exposée" :

```markdown
**API exposée** :
- **HTTP REST** (port 8000) — `GET /health`, `GET /version`, `POST /api/v1/events`
- **WebSocket** (port 8000) — `WS /api/v1/events/ws`
- **Python API** — `CognitiveKernel` injecté via dépendances
```

### Statut

- [x] **Identifié** (2026-07-19)
- [ ] **Corrigé** dans README.md
- [ ] **Validé** par l'équipe

---

## P0-3 : Ajouter des logs explicites dans `./ethan up`

**Fichier concerné** : `scripts/cmd-up.sh`  
**Lignes** : 16-27 (ancienne version)

### Problème

Avant les modifications récentes, `./ethan up` n'avait aucun log explicite :

```bash
# ANCIEN
docker_compose up -d
sleep 2
RUNNING=$(docker_compose ps --services --filter "status=running" | wc -l)
success "$RUNNING/$TOTAL services en cours d'exécution"
```

### Solution

Ajout de logs explicites et vérifications :

```bash
# NOUVEAU
info "Répertoire ETHAN : ${ETHAN_ROOT}"
info "Fichier compose : ${COMPOSE_FILE}"
info "Services à démarrer : ${SERVICES:-<tous>}"

if [ ! -f "${COMPOSE_FILE}" ]; then
    error "Fichier docker-compose.yml introuvable : ${COMPOSE_FILE}"
    exit 1
fi

success "Fichier docker-compose.yml trouvé"

if [ -n "$SERVICES" ]; then
    info "Exécution : docker compose -f \"${COMPOSE_FILE}\" up -d ${SERVICES}"
    if ! docker_compose up -d $SERVICES; then
        error "Échec de 'docker compose up -d ${SERVICES}'"
        info "Vérifier les logs Docker : docker compose logs"
        exit 1
    fi
    success "Commande 'docker compose up -d ${SERVICES}' exécutée avec succès"
else
    info "Exécution : docker compose -f \"${COMPOSE_FILE}\" up -d"
    if ! docker_compose up -d; then
        error "Échec de 'docker compose up -d'"
        info "Vérifier les logs Docker : docker compose logs"
        exit 1
    fi
    success "Commande 'docker compose up -d' exécutée avec succès"
fi
```

### Impact

- **Avant** : Aucun log, impossible de debugger
- **Après** : Logs complets, vérification du code de retour, timeout explicite

### Statut

- [x] **Identifié** (2026-07-19)
- [x] **Corrigé** dans `scripts/cmd-up.sh`
- [ ] **Testé** en environnement de production
- [ ] **Validé** par l'équipe

---

## P0-4 : Configurer PYTHONPATH dans le launcher

**Fichier concerné** : `ethan` (ligne 10)  
**Impact** : Toutes les commandes `./ethan`

### Problème

Le launcher ne configure pas `PYTHONPATH`, donc `python3 -c "import core.kernel"` échoue.

### Solution

Ajouter dans `ethan` :

```bash
export ETHAN_ROOT="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="${ETHAN_ROOT}:${PYTHONPATH:-}"
```

### Validation

```bash
# Test
./ethan python3 -c "import core.kernel; print('OK')"
```

### Statut

- [x] **Identifié** (2026-07-19)
- [x] **Corrigé** dans `ethan`
- [ ] **Testé** en environnement de production
- [ ] **Validé** par l'équipe

---

## P0-5 : Améliorer `./ethan status` pour vérifier la connectivité réelle

**Fichier concerné** : `scripts/cmd-status.sh`

### Problème

Avant, `./ethan status` ne vérifiait que `docker ps`, pas la connectivité réelle.

### Solution

Ajout de tests de connectivité pour chaque service :
- NATS : port TCP 4222
- Redis : PING/PONG
- PostgreSQL : connexion + SELECT 1
- API Gateway : `/health` + `/version`
- WebUI : HTTP sur `/`

### Statut

- [x] **Identifié** (2026-07-19)
- [x] **Corrigé** dans `scripts/cmd-status.sh`
- [ ] **Testé** en environnement de production
- [ ] **Validé** par l'équipe

---

## Résumé P0

| ID | Action | Priorité | Fichier | Statut |
|----|--------|----------|---------|--------|
| P0-1 | Corriger healthchecks Docker | **P0** | `docker-compose.yml` | ✅ Corrigé |
| P0-2 | Metter à jour README.md | **P0** | `README.md` | ⏳ En cours |
| P0-3 | Ajouter logs explicites dans `./ethan up` | **P0** | `scripts/cmd-up.sh` | ✅ Corrigé |
| P0-4 | Configurer PYTHONPATH dans launcher | **P0** | `ethan` | ✅ Corrigé |
| P0-5 | Améliorer `./ethan status` | **P0** | `scripts/cmd-status.sh` | ✅ Corrigé |

### Actions immédiates

1. **Tester** les corrections en environnement de développement
2. **Valider** que `./ethan up` attend les healthchecks
3. **Vérifier** que `./ethan status` affiche les tests de connectivité
4. **Mettre à jour** README.md pour refléter la réalité (HTTP, pas gRPC)

---

## Notes

- Les corrections P0-1 à P0-5 ont été implémentées lors des sessions précédentes
- La documentation README.md nécessite encore une mise à jour manuelle
- Les tests en environnement de production sont requis pour valider les corrections

**Dernière mise à jour** : 2026-07-19