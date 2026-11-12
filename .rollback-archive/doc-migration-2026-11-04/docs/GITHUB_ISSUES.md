# ETHAN GitHub Issues - Tickets de Correction
*Exportés depuis les audits - Format compatible GitHub Issues*

---

## Issue #1: PYTHONPATH Cassé - Imports qui échouent

**Priority:** P0 - CRITICAL  
**Labels:** bug, foundation, imports

### Description
Le système ne peut pas importer `core.kernel`, `sdk`, et `plugins` en raison d'un PYTHONPATH incorrect. Le package `sdk` n'est pas inclus dans pyproject.toml.

### Impact
🔴 Système non fonctionnel - Kernel et modules ne peuvent pas démarrer

### Root Cause
- `pyproject.toml` packages=["core"] uniquement, sdk absent
- `plugins/loader.py` cherche `cli/plugins/` qui n'existe pas
- `deploy/Dockerfile.api` PYTHONPATH inclut sdk mais le package n'existe pas

### Files
- `pyproject.toml` (packages)
- `plugins/loader.py` (BUILTIN_DIR)
- `deploy/Dockerfile.api` (PYTHONPATH)

### Solution
```toml
# pyproject.toml
packages = ["core", "sdk", "plugins"]
```

### Validation Test
```bash
./ethan python3 -c "from core.kernel import CognitiveKernel; print('OK')"
./ethan python3 -c "import sdk; print('OK')"
./ethan python3 -c "import plugins; print('OK')"
```

---

## Issue #2: Sandbox Plugins Inactif - RCE Possible

**Priority:** P0 - CRITICAL  
**Labels:** security, vulnerability, plugins

### Description
Le sandbox plugins ne protège en rien - `enforce()` fait uniquement `yield self` sans isolation réelle.

### Impact
🔴 RCE - Un plugin malveillant peut accéder à tout le système

### Root Cause
```python
# plugins/sandbox.py
@contextlib.asynccontextmanager
async def enforce(self):
    yield self  # ❌ NOOP
    pass
```

### Files
- `plugins/sandbox.py`
- `plugins/loader.py`

### Solution
Implémenter subprocess isolation avec resource limits (memory, CPU, file descriptors)

### Validation Test
```python
# Plugin malveillant
import os
os.system("id")  # Doit être bloqué par sandbox
```

---

## Issue #3: Services Systemd Non Déployés

**Priority:** P0 - CRITICAL  
**Labels:** deployment, systemd

### Description
L'install script ne déploie pas les services systemd dans `/etc/systemd/system/`.

### Impact
🔴 Pas de démarrage auto - nécessite intervention manuelle

### Root Cause
```bash
# install/install.sh
# ❌ Pas de copie vers /etc/systemd/system/
# ❌ Pas de systemctl enable
```

### Files
- `install/install.sh`
- `infrastructure/systemd/ethan-core.service`

### Solution
Ajouter dans install.sh:
```bash
cp infrastructure/systemd/*.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable ethan-core.service
```

### Validation Test
```bash
sudo ethan install
systemctl status ethan-core  # Doit être enabled
```

---

## Issue #4: BUILTIN_DIR Incorrect - Plugins Non Découvrables

**Priority:** P0 - CRITICAL  
**Labels:** bug, plugins, discovery

### Description
`plugins/loader.py` cherche `cli/plugins/` qui n'existe pas. Le répertoire correct est `plugins/`.

### Impact
🔴 Plugins intégrés non chargés

### Root Cause
```python
# plugins/loader.py
BUILTIN_DIR = Path(__file__).parent.parent / "cli" / "plugins"  # ❌ N'existe pas
```

### Files
- `plugins/loader.py`

### Solution
```python
BUILTIN_DIR = Path(__file__).parent / "builtin"
```

### Validation Test
```bash
./ethan python3 -c "from plugins.loader import PluginLoader; l = PluginLoader(); print(l.list())"
```

---

## Issue #5: Ports Exposés Sans Authentification

**Priority:** P0 - CRITICAL  
**Labels:** security, network

### Description
NATS, Redis, PostgreSQL, et API sont exposés sur tous les interfaces sans AUTH.

### Impact
🔴 Attack surface - Compromission réseau possible

### Root Cause
```yaml
# docker-compose.yml
ports:
  - "4222:4222"  # ❌ Binds à 0.0.0.0
```

### Files
- `docker-compose.yml`

### Solution
```yaml
ports:
  - "127.0.0.1:4222:4222"  # ✅ Bind local uniquement
```

### Validation Test
```bash
ss -tlnp | grep -E "4222|6379|5432"  # Doit montrer 127.0.0.1 uniquement
```

---

## Issue #6: Alerting Prometheus Absent

**Priority:** P1 - HIGH  
**Labels:** monitoring, observability

### Description
Aucun alertmanager configuré, pas de rules de firing, pas de notifications.

### Impact
🟡 Silent failures - Downtime non détecté

### Root Cause
```yaml
# docker-compose.observability.yml
# ❌ Aucun alertmanager service
# ❌ Aucun rules directory
```

### Files
- `docker-compose.observability.yml`

### Solution
Ajouter alertmanager avec rules pour disque, mémoire, services unhealthy.

### Validation Test
```bash
curl -sf http://localhost:9093/api/v1/status  # Alertmanager up
```

---

## Issue #7: Backup Automatisé Absent

**Priority:** P1 - HIGH  
**Labels:** backup, reliability

### Description
Aucun script de backup programmé pour PostgreSQL ni Redis.

### Impact
🟡 Perte de données irréversible

### Root Cause
```bash
# ❌ Aucun cron job
# ❌ Aucun script automatisé
```

### Files
- `deploy/postgres/backup/backup.sh`

### Solution
```bash
# Crontab quotidien
0 3 * * * cd /opt/ethan && docker exec ethan-postgres pg_dump -U ethan ethan > /backup/$(date +%Y%m%d).sql
```

### Validation Test
```bash
ls -la /backup/*.sql  # Doit avoir des backups récents
```

---

## Issue #8: Healthchecks NATS/Redis Faibles

**Priority:** P1 - HIGH  
**Labels:** reliability, monitoring

### Description
Les healthchecks ne vérifient pas les dépendances réelles (connexion NATS, Redis, PostgreSQL).

### Impact
🟡 Faux positifs - Services marqués healthy alorsqu'ils ne sont pas prêts

### Solution
Utiliser les healthchecks actuels (corrigé dans RUNTIME-001)

### Validation Test
```bash
curl -sf http://localhost:8000/health/detailed  # Vérifie toutes les dépendances
```

---

## Issue #9: Dualité Go/Python Core

**Priority:** P1 - MEDIUM  
**Labels:** architecture, tech-debt

### Description
Core a une double implémentation : `core/kernel.py` (Python) et `core/main.go` (Go) non utilisé.

### Impact
🟡 Confusion développeurs, dette technique

### Root Cause
Décision d'architecture non finalisée

### Files
- `core/main.go`
- `core/kernel.py`
- `core/bootstrap.py`

### Solution
Choisir Python comme implémentation principale, archiver le Go.

---

## Issue #10: Restart=no dans Systemd

**Priority:** P1 - MEDIUM  
**Labels:** reliability

### Description
Le service systemd a `Restart=no`, pas de recovery automatique.

### Impact
🟡 Downtime prolongé en cas de crash

### Root Cause
```ini
# infrastructure/systemd/ethan-core.service
Restart=no  # ❌ Pas de restart
```

### Files
- `infrastructure/systemd/ethan-core.service`

### Solution
Utiliser ethan-watchdog.service pour monitoring (déjà présent).

### Validation Test
```bash
systemctl restart ethan-core  # Doit redémarrer automatiquement via watchdog