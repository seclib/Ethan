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

**Correction** : Création de `ethan-watchdog.service` + `ethan-watchdog.timer` (toutes les 30s).

**Fichiers** : `infrastructure/systemd/ethan-watchdog.service`, `infrastructure/systemd/ethan-watchdog.timer`

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

## 2. Problèmes Importants (P1) — En cours

| ID | Problème | Statut | Semaine |
|----|----------|--------|---------|
| P1-SEC-01 | Redis requirepass | ✅ Configuré | S1 |
| P1-SEC-03 | Rate limiting API | ✅ Configuré (100 req/min) | S1 |
| P1-SEC-04 | Security headers WebUI | ✅ Corrigé | S1 |
| P1-ARCH-01 | Doublons registry | ❌ À faire | S3 |
| P1-ARCH-03 | Manifest plugins | ❌ À faire | S2 |
| P1-CORE-01 | Timeouts bootstrap | ❌ À faire | S3 |
| P1-CORE-02 | Circuit breaker | ❌ À faire | S3 |
| P1-CI-01 | Pipeline CI/CD | ❌ À faire | S4 |
| P1-CI-02 | Tests insuffisants | ❌ À faire | S4 |
| P1-PLUGIN-01 | Validator non intégré | ❌ À faire | S2 |
| P1-UI-01 | Auth WebUI | ❌ À faire | S6 |

---

## 3. Commandes de Vérification

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