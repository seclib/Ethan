# ETHAN — Hardening & Correctifs de Sécurité

**Date** : 2026-07-22  
**Version** : 1.0  
**Statut** : ✅ Tous les P0 sont corrigés

---

## Résumé

Ce document liste l'ensemble des correctifs de sécurité et de stabilité appliqués à ETHAN suite aux audits indépendants. Tous les problèmes bloquants (P0) sont résolus.

---

## 1. Problèmes Bloquants (P0) — Tous corrigés

### 1.1 BOOT-01 : Ordre de démarrage des services

**Problème** : `modules` démarrait avant `api` et `kernel`, causant des échecs d'enregistrement silencieux.

**Correction** : Ajout de `depends_on` conditionnel dans `docker-compose.yml` :
```yaml
modules:
  depends_on:
    api:
      condition: service_healthy
    kernel:
      condition: service_healthy
```

**Fichier** : `docker-compose.yml`

---

### 1.2 BOOT-02 : Healthcheck NATS

**Problème** : La commande `nc -z localhost 4222` n'était pas disponible dans l'image `nats:alpine`.

**Correction** : Remplacement par `wget -qO- http://localhost:8222/healthz` pour le monitoring HTTP + vérification de connectivité.

**Fichier** : `docker-compose.yml`

---

### 1.3 BOOT-03 : WebUI absente

**Problème** : Le service `ui` n'était défini que dans `docker-compose.prod.yml`, pas dans le fichier principal.

**Correction** : Ajout du service `ui` dans `docker-compose.yml` avec `npm run dev` en mode développement.

**Fichier** : `docker-compose.yml`

---

### 1.4 BOOT-04 : Timeout incohérent

**Problème** : `cmd-up.sh` timeout à 90s, systemd à 600s.

**Correction** : Alignement du timeout à 600s dans `scripts/cmd-up.sh`.

**Fichier** : `scripts/cmd-up.sh`

---

### 1.5 BOOT-05 : Healthcheck PostgreSQL

**Problème** : Le healthcheck PostgreSQL utilisait uniquement `pg_isready`, qui ne vérifie pas que la base répond.

**Correction** : Ajout de `psql -c 'SELECT 1'` pour une vérification réelle.

**Fichier** : `docker-compose.yml`

---

### 1.6 BOOT-06 : Watchdog systemd

**Problème** : Aucune supervision des conteneurs Docker après le démarrage.

**Correction** : Création de `ethan-watchdog.service` + `ethan-watchdog.timer` (toutes les 30s), adossés à un circuit breaker par service (`scripts/cmd-watchdog.sh`) : détection `exited`/`restarting`/`dead` (lecture avec `ps --all`), redémarrage borné à 5 échecs consécutifs, puis circuit ouvert (plus de redémarrage automatique + alerte journal systemd), réarmement progressif après stabilité. Voir Runbook SRE § 7.3.

**Fichiers** : `infrastructure/systemd/ethan-watchdog.service`, `infrastructure/systemd/ethan-watchdog.timer`, `scripts/cmd-watchdog.sh`

---

### 1.7 P0-SEC-01 : Ports exposés

**Problème** : NATS (4222), Redis (6379), PostgreSQL (5432) accessibles depuis l'extérieur.

**Correction** : Binding de tous les ports sur `127.0.0.1` uniquement :
```yaml
ports:
  - "127.0.0.1:4222:4222"
  - "127.0.0.1:6379:6379"
  - "127.0.0.1:5432:5432"
```

**Fichier** : `docker-compose.yml`

**Test** : `nc -zv localhost 6379` doit refuser la connexion.

---

### 1.8 P0-SEC-02 : Sandbox plugins

**Problème** : Le sandbox était un placeholder vide (`yield self` sans isolation).

**Correction** : Implémentation complète (242 lignes) avec :
- `enforce()` : désactive `eval`, `exec`, `open` + resource limits (`RLIMIT_AS`, `RLIMIT_NOFILE`)
- `run_in_subprocess()` : isolation par processus séparé avec timeout, env restreint, mode `-I`
- `PermissionSet` : vérification de permissions par pattern glob
- `ResourceLimits` : mémoire (512MB), CPU (50%), temps (30s), file descriptors (100)
- `SecurityError` : exception spécifique pour violations

**Fichier** : `plugins/sandbox.py`

**Test** : Un plugin avec `exec('import os; os.system("rm -rf /")')` doit être bloqué.

---

### 1.9 P0-SEC-03 : Secrets en clair

**Problème** : Fichiers `*.txt` contenant des mots de passe en clair dans `infrastructure/secrets/`.

**Correction** : 
- Suppression de tous les fichiers `.txt`
- Documentation de migration vers Docker secrets dans `infrastructure/secrets/README.md`
- Variables d'environnement avec valeurs par défaut dans `.env.example`

**Fichiers** : `infrastructure/secrets/README.md`, `.env.example`

**Test** : `docker exec ethan-postgres env | grep PASSWORD` ne doit rien retourner.

---

### 1.10 P0-SEC-04 : Groupe Docker

**Problème** : `Group=docker` dans le service systemd donnait un accès root équivalent.

**Correction** : 
- Remplacement par `SupplementaryGroups=docker` (PID-specific, pas d'escalade)
- `NoNewPrivileges=true`
- `PrivateTmp=true`
- `ProtectSystem=full`
- `ReadWritePaths` restreint à `/opt/ethan`, `/var/lib/ethan`, `/var/log/ethan`

**Fichier** : `infrastructure/systemd/ethan-core.service`

---

### 1.11 P0-SEC-05 : Authentification API

**Problème** : Toutes les routes de l'API Gateway étaient publiques.

**Correction** : 
- Middleware JWT/Bearer sur toutes les routes sauf `/health`, `/metrics`, `/docs`
- Endpoint `POST /auth/login` pour obtenir un token
- Rate limiting intégré (100 req/min, 5 req/min sur login)
- Routes publiques explicitement listées dans `PUBLIC_PATHS`

**Fichiers** : `interfaces/api/auth.py`, `interfaces/api/main.py`, `interfaces/api/rate_limit.py`

**Test** : `curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/v1/chat` → **401**

---

### 1.12 P0-ARCH-01 : sys.path.insert()

**Problème** : `interfaces/api/main.py` modifiait `sys.path` manuellement.

**Correction** : Suppression du `sys.path.insert()`. Le package doit être installé via `pip install -e ".[server]"`.

**Fichier** : `interfaces/api/main.py`

---

### 1.13 P0-ARCH-02 : BUILTIN_DIR incorrect

**Problème** : `plugins/loader.py` cherchait les plugins dans `cli/plugins/` (inexistant).

**Correction** : `BUILTIN_DIR = Path(__file__).parent.parent / "plugins" / "builtin"` → `plugins/builtin/`.

**Fichier** : `plugins/loader.py:66`

---

### 1.14 P0-OPS-01 : Backup PostgreSQL

**Problème** : Script de backup existait mais jamais exécuté.

**Correction** : Service `pg_backup` dans `docker-compose.yml` avec :
- Intervalle de backup : 6 heures
- Rétention : 30 jours
- Healthcheck de connectivité PostgreSQL
- Volume dédié `postgres_backup`

**Fichiers** : `docker-compose.yml`, `deploy/postgres/backup/backup.sh`

---

### 1.15 BOOT-07 : Doctor sans faux positifs

**Problème** : Après le rebuild (core/ + sdk/ + plugins/), 6 checks du doctor produisaient des faux positifs sur un système sain (« 66 PASS, 6 WARNING ») : modules pré-rebuild référencés (`core.providers.*`, `core.registry`), dossier `runtime/` inexistant avec suggestion `pip install -e runtime` inapplicable, warning `PYTHONPATH` inconditionnel alors que les imports passent, `NODE_ENV` requis côté shell alors que le compose le fixe (`service ui`), et `redis-cli` absent du host limitant le test Redis à un simple test de port.

**Correction** :
- providers / plugins : checks re-pointés vers les modules actuels (`core.llm.provider_factory`, `core.plugins`) ;
- `runtime` : check neutralisé tant que le dossier `runtime/` n'existe pas ;
- `PYTHONPATH` : warning émis uniquement si `import core, sdk, plugins` échoue réellement ;
- `NODE_ENV` : plus de warning si `docker-compose.yml` fixe la valeur (service ui) ;
- Redis : fallback `docker exec ethan-redis redis-cli ping` (test réel via le conteneur) quand `redis-cli` est absent du host ;
- `tests/install/` : quarantaine rendue effective aussi en collecte ciblée (`collect_ignore_glob` conditionné à l'absence du paquet `openjarvis`) — 10 erreurs de collection éliminées.

Résultat : `./ethan doctor` → « Tout est opérationnel (71 PASS, 0 WARNING) ».

**Fichiers** : `scripts/cmd-doctor.sh`, `tests/install/conftest.py`

**Test** : `pytest tests/deployment/test_doctor_checks.py` (imports résolvables, aucun import pré-rebuild, gardes anti-régression, live `0 FAIL` sans faux positif).

---

## 2. Problèmes Importants (P1) — En cours

| ID | Problème | Statut | Semaine |
|----|----------|--------|---------|
| P1-SEC-01 | Redis requirepass | ✅ Configuré | S1 |
| P1-SEC-03 | Rate limiting API | ✅ Configuré (100 req/min) | S1 |
| P1-SEC-04 | Security headers WebUI | ✅ Corrigé | S1 |
| P1-ARCH-01 | Doublons registry | ⚠ Partiel — **CLI fusionné** (`plugin.py` unique, `plugin_cmd`/`plugins` supprimés, dispatch `discover` activé — Commit 5820a527) ; **Folders/Domains** : helpers mutualisés (`core/attachments.py`), écart fail-closed documenté ci-dessous ; restent `plugins/tool_registry`/`versioning` sans importeur (RFC) | S3 |
| P1-ARCH-03 | Manifest plugins | ✅ Manifest Core (`core/plugins/types.py`) | S2 |
| P1-CORE-01 | Timeouts bootstrap | ✅ Retry/backoff + `CONNECT_TIMEOUT` + `DEPENDENCY_STARTUP_TIMEOUT` | S3 |
| P1-CORE-02 | Circuit breaker | ✅ `core/safety/circuit_breaker.py` + watchdog systemd | S3 |
| P1-CI-01 | Pipeline CI/CD | ✅ `.github/workflows/ci.yml` (lint, test, build, integration, security, release) | S4 |
| P1-CI-02 | Tests insuffisants | ✅ Renforcé (1542 tests : boot, watchdog, doctor, validator, attachments) | S4 |
| P1-PLUGIN-01 | Validator non intégré | ✅ Capacité migrée `core/plugins/validator.py`, intégrée à `install_custom` (rejet 422) ; CLI `plugin_cmd` importe le Core (dispatch unifié `plugin.py`/`plugin_cmd.py` = RFC Phase 4) | S2 |
| P1-UI-01 | Auth WebUI | ✅ `(auth)/login` + middleware + JWT API (`auth_middleware`) | S6 |
| P1-PKG-01 | Code source sous un chemin ignoré | ✅ Corrigé — `core/security/data/` (anti-exfiltration) était exclu par le pattern `data/` du `.gitignore` : `core.agents.executor` était inimportable sur clone vierge (voir §3.2) | S3 |
| P1-CI-03 | Tests trackés cassés sur clone vierge | ✅ Corrigé — import invalide dans `tests/cli/ethan/regression/test_api_contracts.py` + RÈGLE 1 import-linter (`core.capabilities.registry → plugins.manager`) (voir §3.2) | S4 |
| P2-ORPH-01 | Modules orphelins inimportables | ✅ Corrigé — 3 `bootstrap.py` (`EventBus as NatsEventBus`) et 2 modules `core/orchestrator` (`core.orchestration` → `core.orchestrator`) ; reste `example_usage.py` (`SafetyValidator` disparu) (voir §3.2) | S5 |

---

## 3. Commandes de Vérification

### 3.1 Phase 4 — dette Folders vs Domains (état après mutualisation)

`core/folders/manager.py` et `core/domains/manager.py` étaient des
jumeaux structurels (copier-coller). Après la mutualisation des helpers
identiques dans `core/attachments.py` (provider, clé de membership,
normalisation de record, horodatage, sentinelle UNSET), **deux écarts
comportementaux assumés restent** — décision produit requise (RFC) :

| Point | FolderManager | DomainManager |
|---|---|---|
| Existence de la ressource à l'attach | **fail-closed** : résolu via provider, rejet si absente | non vérifié (relation possible « fantôme », purgée en lecture par auto-pruning) |
| Events | `FOLDER_*` | `DOMAIN_*` |

Recommandation : aligner `DomainManager` sur le fail-closed des dossiers
(même garantie « jamais de relation fantôme ») dans la RFC de fusion des
politiques — sans changer les APIs publiques.

### 3.2 Phase 4/5 — dette de packaging et modules orphelins (état 2026-09-24)

Vérification systématique effectuée dans un **worktree git détaché** (checkout
propre, sans travail local non commité), car plusieurs anomalies étaient
**masquées en local** par des fichiers présents mais non committés.

**Corrigé dans cette passe :**

| Anomalie | Cause racine | Correctif |
|---|---|---|
| `ModuleNotFoundError: core.security.data` → `core.agents.executor` inimportable, 4 modules de tests non collectés | `core/security/data/` était exclu par le pattern `data/` (`.gitignore` l.158) alors que `prompt_guard.py` et `integration.py` l'importent | Exception d'ignorabilité `!core/security/data/` + `!core/security/data/**` (même recette que `interfaces/api/models/`) et committion des 3 modules |
| `lint-imports` en `SyntaxError` | `tests/cli/ethan/regression/test_api_contracts.py` était tracké avec `from tests.cli/ethan.api_validator import ...` (slash) | Point au lieu du slash + newline final |
| `RÈGLE 1 — Core kernel indépendant` BROKEN : `core.capabilities.registry → plugins.manager` | Imports statiques « test de disponibilité » jamais utilisés | `_module_exposes()` (`importlib` + `hasattr`) : découverte identique, plus aucune dépendance statique `core → plugins` |
| 5 modules inimportables (P2-ORPH-01a/b) : 3 `bootstrap.py` + `core/orchestrator/cognitive_loop.py`, `example_usage.py` | Imports de noms disparus : `NatsEventBus` (absent de `core.bus.nats_bus`) et `core.orchestration` (renommé `core.orchestrator`) | Alias `EventBus as NatsEventBus` (idiome déjà en place dans `core/ethan_bootstrap.py`) et import depuis `core.orchestrator` — 5 fichiers, 1 ligne chacun ; `tests/core/test_cognitive_loop.py` collecte à nouveau ses 15 tests |

**Dette restante** (aucun de ces points n'est chargé par
`core/ethan_bootstrap.py`, `core/main.py` ni `python -m core.modules`) :

| ID | Fichiers | Symptôme | Correctif recommandé |
|---|---|---|---|
| P2-ORPH-01c | `core/orchestrator/example_usage.py` | Une fois l'import corrigé, reste `from core.safety import SafetyValidator` : la classe n'existe plus (`core.safety` expose `SafetyContext`, `DefaultSafetyChecker.check_permission`, `DefaultRoleRegistry`) | Fichier d'exemple sans importeur : le réécrire sur l'API actuelle ou le retirer |
| P2-PKG-02 | `tests/test_web_search.py` (tracké) | Importe `core.knowledge.web_search`, module non committé → erreur de collecte | Committer le module (`web_search.py`, `web_inspiration.py`, `web_research_service.py`) ou retirer le test |

**État mesuré sur clone propre** (commit `676403a3`) : `lint-imports` **5 kept /
0 broken**, `ast.parse` OK sur tout le dépôt, **1 seul module inimportable**
(`core/orchestrator/example_usage.py`, P2-ORPH-01c — fichier d'exemple sans
importeur).


```bash
# Test ports
nc -zv localhost 6379    # Doit échouer
nc -zv localhost 4222    # Doit échouer
nc -zv localhost 5432    # Doit échouer

# Test authentification API
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/v1/chat
# → 401

# Test healthcheck public
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health
# → 200

# Test secrets
docker exec ethan-postgres env | grep PASSWORD
# → vide

# Test sandbox
python3 -c "
from plugins.sandbox import PluginSandbox, SecurityError
import asyncio
async def test():
    s = PluginSandbox()
    async with s.enforce():
        try:
            eval('1+1')
            print('ERREUR: eval non bloqué')
        except SecurityError:
            print('OK: eval bloqué')
asyncio.run(test())
"

# Test backup
docker exec ethan-postgres pg_dump -U ethan ethan > /tmp/test_backup.sql
echo "OK: backup réussi ($(wc -c < /tmp/test_backup.sql) bytes)"
```

---

## 4. Architecture de Sécurité Actuelle

```
                    ┌─────────────────────────────┐
                    │      Internet / Réseau       │
                    │  (ports 80/443 uniquement)   │
                    └──────────┬──────────────────┘
                               │
                    ┌──────────▼──────────────────┐
                    │      Reverse Proxy          │
                    │  (Traefik/Caddy — futur)    │
                    └──────────┬──────────────────┘
                               │
                    ┌──────────▼──────────────────┐
                    │    API Gateway (port 8000)   │
                    │  • JWT Bearer authentication │
                    │  • Rate limiting (100 req/m) │
                    │  • CORS restreint            │
                    │  • Security headers          │
                    └──────────┬──────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
          ▼                    ▼                    ▼
   ┌──────────┐        ┌──────────┐        ┌──────────┐
   │   NATS   │        │  Redis   │        │   PG     │
   │ :4222    │        │ :6379    │        │ :5432    │
   │ 127.0.0.1│        │ 127.0.0.1│        │ 127.0.0.1│
   │ ACL + js │        │ require  │        │ password │
   │          │        │ pass     │        │ strong   │
   └──────────┘        └──────────┘        └──────────┘
```

---

## 5. Prochaines Étapes

1. **S2** : Intégrer `PluginValidator` dans `PluginLoader` + tests sandbox
2. **S3** : Timeouts bootstrap + circuit breaker + unification registry
3. **S4** : Pipeline CI/CD + tests unitaires
4. **S5** : Observabilité (Grafana, Loki, alerting)
5. **S6** : Authentification WebUI + finalisation

---

**Document généré le 2026-07-22 — CTO ETHAN**