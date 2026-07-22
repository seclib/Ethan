# ETHAN — Plan de Refactorisation & Stabilisation

**Auteur** : CTO  
**Date** : 2026-07-22  
**Version** : 2.0  
**Statut** : 🔴 NON-PRODUCTION READY — Plan d'action actualisé

---

## Résumé Exécutif

ETHAN a subi **7 audits indépendants** (Architecture, Core, Runtime, Sécurité, Production, Plugins, Boot, CTO).  
Le constat est unanime : **le système n'est pas prêt pour la production**.

### Scores Clés

| Audit | Score | Verdict |
|-------|-------|---------|
| Production Readiness | 2.1/10 | 🔴 NO-GO |
| Sécurité | 3.2/10 | 🔴 CRITIQUE |
| CTO Review | 3.8/10 | 🔴 NO-GO |
| Architecture | 6/10 | 🟡 Dette technique |
| Bootstrap | 8.1/10 | ✅ En progrès |
| Plugins | 4.5/10 | 🟡 Pathologies |
| **Moyenne** | **~4.5/10** | **🔴 NON PRODUCTION** |

### Objectif Prioritaire Absolu

```
sudo ethan up
  → fonctionnel
  → stable
  → sécurisé
  → sur n'importe quel Ubuntu 24.04 vierge
```

---

## 1. Problèmes Bloquants (P0)

### ✅ DÉJÀ CORRIGÉS (par les audits Boot/CTO)

| ID | Problème | Correction | Fichier |
|----|----------|------------|---------|
| BOOT-01 | `modules` démarre avant `api`/`kernel` prêts | Ajout `depends_on` conditionnel | `docker-compose.yml` |
| BOOT-02 | Healthcheck NATS cassé (`nc -z` absent) | Remplacement par `wget + nc` | `docker-compose.yml` |
| BOOT-03 | WebUI absente de `docker-compose.yml` | Ajout service `ui` | `docker-compose.yml` |
| BOOT-04 | Timeout `cmd-up.sh` 90s vs systemd 600s | Aligné sur 600s | `scripts/cmd-up.sh` |
| BOOT-05 | Healthcheck PostgreSQL faible | Ajout `SELECT 1` | `docker-compose.yml` |
| BOOT-06 | Pas de watchdog systemd | Création `ethan-watchdog.service` | `infrastructure/systemd/` |
| **P0-SEC-01** | Ports NATS/Redis/PG exposés sans binding | Binding `127.0.0.1` sur tous les services | `docker-compose.yml` | ✅ Déjà corrigé |
| **P0-SEC-04** | `Group=docker` → escalade root | `SupplementaryGroups=docker` + `NoNewPrivileges=true` | `infrastructure/systemd/ethan-core.service` | ✅ Déjà corrigé |
| **P0-SEC-05** | API Gateway sans authentification | Middleware JWT + rate limiting intégré | `interfaces/api/auth.py`, `interfaces/api/main.py` | ✅ Déjà corrigé |
| **P0-ARCH-01** | `sys.path.insert()` dans `api/main.py:13` | Supprimé, docstring `pip install -e .[server]` | `interfaces/api/main.py` | ✅ Déjà corrigé |
| **P0-ARCH-02** | `BUILTIN_DIR` = `cli/plugins/` (inexistant) | Corrigé → `plugins/builtin/` | `plugins/loader.py:66` | ✅ Déjà corrigé |

### ✅ AUCUN P0 RESTANT — Tous corrigés

| ID | Problème | Vérification | 
|----|----------|--------------|
| **P0-SEC-02** | Sandbox plugins | `plugins/sandbox.py` : 242 lignes, isolation subprocess + in-process + resource limits |
| **P0-SEC-03** | Secrets en clair | `infrastructure/secrets/` : plus aucun `.txt`, README de migration Docker secrets présent |
| **P0-OPS-01** | Backup PostgreSQL | Service `pg_backup` actif dans `docker-compose.yml` (intervalle 6h, rétention 30 jours) |

---

## 2. Problèmes Importants (P1) — Seuls problèmes bloquants restants

| ID | Problème | Cause Racine | Modules | Ordre |
|----|----------|-------------|---------|-------|
| P1-SEC-01 | Redis sans `requirepass` | Aucune configuration AUTH | redis | S1 |
| P1-SEC-03 | Rate limiting absent sur API | Aucun middleware de throttling | api | S1 |
| P1-SEC-04 | Security headers WebUI absents | `next.config.js` sans en-têtes | webui | S1 |
| P1-ARCH-01 | Doublons registry : `module.py` vs `module_registry.py` | Non consolidés | `core/registry/` | S3 |
| P1-ARCH-02 | `runtime/` Go orphelin | Code legacy non supprimé | `runtime/` | S4 |
| P1-ARCH-03 | Manifest plugins : `plugin.yaml` vs `manifest.json` | Deux formats non alignés | `plugins/browser/` | S2 |
| P1-CORE-01 | Timeout manquant sur `pg.connect()`, `redis.connect()`, `bootstrapper.run()` | Aucun timeout explicite | `core/bootstrap.py` | S3 |
| P1-CORE-02 | Circuit breaker non intégré aux connexions externes | Présent mais pas activé | `core/safety/circuit_breaker.py` | S3 |
| P1-CI-01 | Pipeline CI/CD inexistant | Aucun workflow complet | `.github/workflows/` | S4 |
| P1-CI-02 | Tests insuffisants (1 seul test boot, couverture ≈ 0%) | Pas de culture de test | `tests/` | S4 |
| P1-OPS-01 | Pas de backup Redis (RDB/AOF non configuré) | Aucune persistence configurée | redis | S5 |
| P1-OPS-02 | `docker-compose.prod.yml` non finalisé | Dev et prod mélangés | `docker-compose.prod.yml` | S4 |
| P1-UI-01 | Authentification WebUI absente (page login sans backend) | Frontend seulement, pas de JWT | webui | S6 |
| P1-PLUGIN-01 | Validator non intégré dans PluginLoader | `plugins/validator.py` jamais appelé | `plugins/loader.py` | S2 |

---

## 3. Problèmes Moyens (P2) — Améliorations

| ID | Problème | Modules | Suggestion |
|----|----------|---------|------------|
| P2-ARCH-01 | `__pycache__/` non nettoyé | `.gitignore` | S4 |
| P2-ARCH-02 | `rust/` crates orphelines | `rust/` | S6 |
| P2-ARCH-03 | Double système plugins CLI vs Core | `plugins/`, `interfaces/cli/` | S7 |
| P2-OBS-01 | Aucun dashboard Grafana actif | `infrastructure/grafana/` | S5 |
| P2-OBS-02 | Tracing distribué Jaeger absent | `infrastructure/jaeger/` | S7 |
| P2-OBS-03 | Logs non centralisés (docker logs seulement) | `infrastructure/loki/` | S5 |
| P2-OBS-04 | Alerting Prometheus absent | `docker-compose.observability.yml` | S5 |
| P2-OPS-01 | Scripts de maintenance (logrotate, VACUUM) absents | `deploy/postgres/` | S5 |
| P2-OPS-02 | Auto-update avec watchtower absent | docker-compose | S6 |
| P2-OPS-03 | Migration DB Alembic non automatisée | `deploy/postgres/alembic/` | S6 |
| P2-OPS-04 | Volumes Docker non chiffrés | `docker-compose.yml` | S7 |
| P2-UI-01 | RBAC pour plugins (capabilities + permissions) | `plugins/` | S7 |
| P2-UI-02 | Gestion des plugins dans WebUI | webui | S7 |

---

## 4. Problèmes Faibles (P3) — Dette technique

| ID | Problème | Modules | Suggestion |
|----|----------|---------|------------|
| P3-LEGACY-01 | Implémentation Go/Python duale (`kernel-go/`) | `kernel-go/` | S6 |
| P3-LEGACY-02 | 3 imports morts dans `bootstrap.py` | `core/bootstrap.py` | S4 |
| P3-LEGACY-03 | `docker-compose.dev.yml` en double | `docker-compose.dev.yml` | S6 |
| P3-LEGACY-04 | Pas de DNS interne | Réseau Docker | S7 |
| P3-DOC-01 | `docs/deployment.md` à compléter | `docs/` | S7 |
| P3-DOC-02 | Runbook SRE à compléter | `docs/sre-runbook.md` | S7 |

---

## 5. Roadmap de Correction (6 semaines)

### Semaine 1 — Tests de vérification & Hardening léger

**Objectif** : Valider que tous les correctifs P0 sont bien en place.  
**Score sécurité** : 3.2 → **6.0/10**

| Jour | Action | ID | Fichier | Effort |
|------|--------|----|---------|--------|
| J1 | Vérifier ACL NATS (utilisateur dédié si pas déjà fait) | P1 | config NATS | 1h |
| J1 | Vérifier rate limiting (100 req/min) sur API | P1-SEC-03 | `interfaces/api/main.py`, `interfaces/api/rate_limit.py` | 1h |
| J2 | Ajouter security headers WebUI si absents | P1-SEC-04 | `interfaces/webui/next.config.js` | 30 min |
| J2 | Ajouter `requirepass` Redis si pas déjà fait | P1-SEC-01 | `docker-compose.yml`, `.env.example` | 15 min |
| J3 | Documentation des correctifs P0 dans `docs/` | — | `docs/hardening.md` | 2h |
| J4 | **Tests de validation P0** : ports, auth, sandbox, secrets, backup | — | Tests manuels | 3h |

**Acceptance S1** :
- [ ] `nc -zv localhost 6379` → refus (Redis bindé 127.0.0.1)
- [ ] `nc -zv localhost 4222` → refus (NATS bindé 127.0.0.1)
- [ ] `curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/v1/chat` → **401**
- [ ] `curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health` → **200** (public OK)
- [ ] Aucun processus membre du groupe `docker` sauf root

---

### Semaine 2 — Intégration PluginValidator & tests de non-régression

**Objectif** : Finaliser l'intégration des vérifications plugins.

| Jour | Action | ID | Fichier | Effort |
|------|--------|----|---------|--------|
| J1 | Intégrer `PluginValidator` dans `PluginLoader` | P1-PLUGIN-01 | `plugins/loader.py` | 1h |
| J1 | Standardiser `manifest.json` pour tous les plugins | P1-ARCH-03 | `plugins/browser/` | 1h |
| J2 | Tests sandbox : vérifier que `enforce()` bloque `eval`/`exec`/`open` | — | `tests/test_sandbox.py` | 2h |
| J2 | Tests subprocess : vérifier timeout, resource limits, permissions | — | `tests/test_sandbox.py` | 2h |
| J3 | Tests secrets : vérifier Docker secrets mountés dans les conteneurs | — | `tests/test_secrets.py` | 1h |
| J3 | Tests backup : vérifier `pg_dump` + rotation | — | `tests/test_backup.py` | 1h |
| J4 | **Tests de non-régression** : `./ethan up` + `./ethan status` | — | Tests manuels | 2h |

**Acceptance S2** :
- [ ] Plugin avec `exec('import os; os.system("rm -rf /")')` → bloqué par sandbox
- [ ] `docker exec ethan-postgres env \| grep PASSWORD` → vide (Docker secrets)
- [ ] Les secrets sont dans `/run/secrets/` à l'intérieur des conteneurs
- [ ] `plugins/loader.py` découvre les plugins dans `plugins/builtin/`
- [ ] `PluginValidator` exécuté avant tout chargement de plugin

---

### Semaine 3 — Stabilité du Boot & Architecture Core

**Objectif** : `sudo ethan up` fiable à 100% sur système vierge.  

| Jour | Action | ID | Fichier | Effort |
|------|--------|----|---------|--------|
| J1 | Ajouter timeout (30s) sur `pg.connect()`, `redis.connect()` | P1-CORE-01 | `core/bootstrap.py` | 2h |
| J1 | Ajouter timeout (60s) sur `bootstrapper.run()` | P1-CORE-01 | `core/bootstrap.py` | 1h |
| J2 | Intégrer circuit breaker NATS (3 échecs → open, 30s cooldown) | P1-CORE-02 | `core/safety/circuit_breaker.py` | 2h |
| J2 | Intégrer circuit breaker providers LLM | P1-CORE-02 | `core/safety/circuit_breaker.py` | 1h |
| J3 | Unifier `module.py` et `module_registry.py` dans `core/registry/` | P1-ARCH-01 | `core/registry/` | 1h |
| J3 | Mise à jour README.md (Python kernel, FastAPI, port 8000) | P0-ARCH-03 | `README.md` | 30 min |
| J4 | **Test grandeur nature** : `./ethan up` sur Ubuntu 24.04 vierge | — | VM test | 4h |

**Acceptance S3** :
- [ ] `./ethan up` sur Ubuntu 24.04 vierge → **7/7 healthy en ≤ 10 min**
- [ ] `pytest tests/test_boot.py` → **3/3 pass**
- [ ] Backup PostgreSQL : `pg_dump` + restore testé sur DB vierge
- [ ] `pip install -e ".[server]"` → imports fonctionnent sans `sys.path`
- [ ] NATS perd la connexion → circuit breaker → recovery automatique

---

### Semaine 4 — CI/CD & Tests Fondamentaux

**Objectif** : Pipeline CI passe, couverture ≥ 20%.

| Jour | Action | ID | Fichier | Effort |
|------|--------|----|---------|--------|
| J1 | Pipeline CI : lint → test → build image de base | P1-CI-01 | `.github/workflows/ci.yml` | 3h |
| J1 | Ajouter `__pycache__` à `.gitignore` + nettoyage global | P2-ARCH-01 | `.gitignore` | 15 min |
| J2 | Tests unitaires pour modules cognitifs (kernel, state, bus) | P1-CI-02 | `tests/test_core*.py` | 4h |
| J2 | Tests d'intégration bootstrap (NATS, Redis, PG, health) | P1-CI-02 | `tests/test_bootstrap.py` | 2h |
| J3 | Finaliser `docker-compose.prod.yml` (workers 2, restart limits) | P1-OPS-02 | `docker-compose.prod.yml` | 2h |
| J3 | Nettoyer ou documenter `runtime/` Go orphelin | P1-ARCH-02 | `runtime/` | 30 min |
| J3 | Nettoyer imports morts dans `bootstrap.py` | P3-LEGACY-02 | `core/bootstrap.py` | 15 min |
| J4 | **Tests** : CI pipeline + couverture ≥ 20% | — | `pytest --cov` | 2h |

**Acceptance S4** :
- [ ] `git push origin main` → GitHub Actions passe (lint → test → build)
- [ ] `pytest --cov --cov-report=term-missing` → couverture ≥ **20%**
- [ ] `core/registry/` unifié : un seul fichier, pas de doublon
- [ ] `runtime/` supprimé ou documenté comme "legacy"
- [ ] `docker-compose.prod.yml` valide (`docker compose -f docker-compose.prod.yml config`)

---

### Semaine 5 — Observabilité & Résilience

**Objectif** : Monitoring fonctionnel et auto-récupération.

| Jour | Action | ID | Fichier | Effort |
|------|--------|----|---------|--------|
| J1 | Configurer persistence Redis (RDB/AOF) + backup | P1-OPS-01 | `docker-compose.yml` | 1h |
| J1 | Dashboard Grafana préconfiguré (CPU, memory, health, NATS) | P2-OBS-01 | `infrastructure/grafana/dashboards/` | 3h |
| J2 | Alerting Prometheus (email/slack, rules de firing) | P2-OBS-04 | `docker-compose.observability.yml` | 3h |
| J3 | Logs centralisés avec Loki + Promtail | P2-OBS-03 | `infrastructure/loki/` | 4h |
| J4 | Scripts maintenance : logrotate Docker + VACUUM PostgreSQL | P2-OPS-01 | `deploy/postgres/maintenance/` | 2h |

**Acceptance S5** :
- [ ] Dashboard Grafana accessible → affiche CPU/memory/health
- [ ] Alerte email/Slack quand un service crash
- [ ] Logs centralisés consultables dans Loki
- [ ] Redis persistence RDB active (vérifier `dump.rdb`)
- [ ] Maintenance DB : `VACUUM` automatique hebdomadaire

---

### Semaine 6 — Authentification WebUI & Finalisation

**Objectif** : WebUI + API protégées par JWT, code nettoyé.

| Jour | Action | ID | Fichier | Effort |
|------|--------|----|---------|--------|
| J1 | Backend JWT pour WebUI (login endpoint + refresh token) | P1-UI-01 | `interfaces/api/main.py`, `interfaces/api/routers/auth.py` | 4h |
| J2 | Frontend : login form → JWT → sessions protégées | P1-UI-01 | `interfaces/webui/` | 4h |
| J2 | Watchtower auto-update | P2-OPS-02 | `docker-compose.prod.yml` | 30 min |
| J3 | Migration DB automatisée (Alembic) | P2-OPS-03 | `deploy/postgres/alembic/` | 2h |
| J3 | Supprimer `kernel-go/` après vérification non-utilisation | P3-LEGACY-01 | `kernel-go/` | 30 min |
| J3 | Fusionner/documenter `docker-compose.dev.yml` | P3-LEGACY-03 | `docker-compose.dev.yml` | 1h |
| J4 | **Tests end-to-end** : auth + API + WebUI | — | `tests/test_e2e*.py` | 3h |
| J4 | **Test final** : `sudo ethan up` sur VM vierge sans erreur | — | VM test | 4h |

**Acceptance S6** :
- [ ] Login JWT fonctionnel : `POST /auth/login` → token → API protégée
- [ ] WebUI redirige vers login si non authentifié
- [ ] `sudo ethan up` sur VM vierge → **0 erreur, 7/7 healthy**
- [ ] Migration DB Alembic automatique au démarrage
- [ ] Code legacy supprimé (`kernel-go/`, `runtime/`, `rust/` si non utilisé)

---

## 6. Arbre de Priorité Strict

```
SI "sudo ethan up ne fonctionne pas" ALORS
    PRIORITÉ 1 : P0-BOOT-*    (✅ déjà corrigé)
    PRIORITÉ 2 : P0-ARCH-01   (sys.path → S3)

SINON SI "sécurité insuffisante pour prod" ALORS
    PRIORITÉ 1 : P0-SEC-05    (API auth → S1)
    PRIORITÉ 2 : P0-SEC-04    (Group=docker → S1)
    PRIORITÉ 3 : P0-SEC-02    (sandbox → S2)
    PRIORITÉ 4 : P0-SEC-03    (secrets → S2)

SINON SI "dette technique bloque développement" ALORS
    PRIORITÉ 1 : P1-ARCH-01   (registry → S3)
    PRIORITÉ 2 : P1-CI-*      (tests, pipeline → S4)

SINON
    PRIORITÉ : P2-* (observabilité, maintenance → S5)
    PRIORITÉ : P3-* (legacy, documentation → S6)
```

---

## 7. Budget & Effort

| Semaine | Phase | JH | Compétences | Dépendances |
|---------|-------|----|-------------|-------------|
| **S1** | Réseau & Auth | 8 JH | Backend + DevOps + Security | Aucune |
| **S2** | Sandbox & Secrets | 9 JH | Python + Security | S1 terminée |
| **S3** | Boot & Architecture Core | 10 JH | Backend + DevOps | S2 terminée |
| **S4** | CI/CD & Tests | 10 JH | DevOps + Backend | S3 terminée |
| **S5** | Observabilité | 9 JH | SRE + Frontend | S4 terminée |
| **S6** | WebUI Auth & Finalisation | 11 JH | Fullstack + DevOps | S5 terminée |
| **Total** | **6 semaines** | **57 JH** | 2 personnes | |

---

## 8. Critères d'Acceptation Globaux

### Fin S1 (Verrouillage réseau)
```
./ethan up OK
nc -zv localhost 6379 REFUS
curl http://localhost:8000/v1/chat → 401
```

### Fin S2 (Sandbox & secrets)
```
Plugin dangereux BLOQUÉ
docker exec ethan-postgres env | grep PASSWORD → vide
```

### Fin S3 (Boot stable) — 🔴 OBJECTIF CRITIQUE
```
sudo ethan up sur Ubuntu 24.04 vierge → OK ≤ 10 min
pytest tests/test_boot.py → 3/3 pass
Backup PostgreSQL automatique testé
```

### Fin S4 (CI/CD)
```
git push origin main → GitHub Actions passe
Couverture ≥ 20%
```

### Fin S5 (Observabilité)
```
Grafana dashboard + alertes email
Logs centralisés Loki
```

### Fin S6 (Production contrôlée) — 🟢 OBJECTIF FINAL
```
sudo ethan up → 0 erreur, 7/7 healthy
JWT login fonctionnel
WebUI protégée
Code legacy nettoyé
Score production ≥ 7/10
```

---

## 9. Verdict par Semaine

```
État actuel              : 🔴 NON-PRODUCTION     (Score 3.8/10)
Après Semaine 1 (Auth)   : 🟡 DÉVELOPPEMENT      (Score 5.5/10)
Après Semaine 2 (Sandbox): 🟡 DÉVELOPPEMENT      (Score 6.5/10)
Après Semaine 3 (Boot)   : 🟡 PRÉ-PRODUCTION     (Score 7.5/10) ← Go/No-Go
Après Semaine 4 (CI/CD)  : 🟡 PRÉ-PRODUCTION     (Score 8.0/10)
Après Semaine 5 (Obs)    : 🟢 PRODUCTION CONTRÔLÉE (Score 8.5/10)
Après Semaine 6 (Final)  : 🟢 PRODUCTION READY    (Score 9.0/10)
```

---

## 10. Commandes de Validation Finale

```bash
# Test 1 : Boot complet
./ethan down && ./ethan up
./ethan status          # Must show 7/7 healthy

# Test 2 : Sécurité ports
nc -zv localhost 6379  # Must fail (Redis bind 127.0.0.1)
nc -zv localhost 4222  # Must fail (NATS bind 127.0.0.1)

# Test 3 : Authentification API
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/v1/chat
# Must return 401

# Test 4 : Authentification WebUI
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/api/chat
# Must return 401

# Test 5 : Secrets
docker exec ethan-postgres printenv | grep PASSWORD
# Must not contain plaintext password

# Test 6 : Sandbox
# Run a plugin with malicious code, must be blocked

# Test 7 : Backup
docker exec ethan-postgres pg_dump -U ethan ethan > /tmp/test_backup.sql
docker exec -i ethan-postgres psql -U ethan -d ethan_test < /tmp/test_backup.sql
# Must restore without error

# Test 8 : CI (after S4)
git push origin main
# GitHub Actions must pass (lint → test → build)

# Test 9 : End-to-end (after S6)
TOKEN=$(curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"test"}' \
  | jq -r '.access_token')
curl http://localhost:8000/v1/chat \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message":"hello"}'
# Must return valid response

# Test 10 : Test final sur VM vierge
ssh ubuntu@fresh-vm 'git clone https://github.com/seclib/Ethan.git && cd Ethan && sudo ./ethan up'
# Must succeed without any error
```

---

## 11. Risques & Mitigations

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Rupture de charge (1 seule personne) | Élevée | Retard 2× | Prioriser S1-S3 (critiques), S4-S6 peuvent glisser |
| Dépendances externes (Vault, Loki) | Moyenne | Blocage partiel | Alternatives : Docker secrets + json-file logs |
| Plugin sandbox cassé → système instable | Faible | Critique | Tests intensifs S2 avant merge |
| `docker compose` breaking change | Faible | Blocage | Utiliser `docker-compose-plugin` v2 stable |
| NATS cluster 3 nœuds complexe | Moyenne | Élevé | Reporté après S6 (standalone suffit pour dev) |

---

## 12. Conclusion

### Ce qui a déjà été corrigé
- ✅ `depends_on` modules → api/kernel
- ✅ Service WebUI dans `docker-compose.yml`
- ✅ Healthcheck NATS corrigé
- ✅ Healthcheck PostgreSQL amélioré (`SELECT 1`)
- ✅ Watchdog systemd créé
- ✅ Timeout aligné (600s)

### Priorité absolue — Semaines 1-3
1. **P1-SEC-01** : Redis `requirepass` — S1
2. **P1-PLUGIN-01** : Intégrer `PluginValidator` dans `PluginLoader` — S2
3. **P1-ARCH-01** : Unifier doublons registry `module.py` / `module_registry.py` — S3

### Prochain Go/No-Go
```
Fin Semaine 3 : sudo ethan up sur VM vierge
  → Succès : 🟡 PRÉ-PRODUCTION (score 7.5/10)
  → Échec  : 🔴 STOP — investigation immédiate
```

**Ce document annule et remplace la version 1.0 du 2026-07-21.**