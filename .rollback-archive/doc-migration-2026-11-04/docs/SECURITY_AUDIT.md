# Audit Sécurité ETHAN - OS IA Personnel

**Date** : 2026-07-21  
**Auteur** : Security Architect  
**Version** : 1.0  
**Statut** : 🔴 CRITIQUE

---

## 1. Score Global de Risque : **3.2/10** (ÉLEVÉ)

```
ETHAN Security Posture
├── Isolation       : 2/10  🔴 Critical
├── Secrets         : 4/10  ⚠️ Warning  
├── Network         : 5/10  🟡 Moderate
├── AuthZ/AuthN     : 1/10  🔴 Critical
└── Hardening       : 4/10  ⚠️ Warning
```

---

## 2. Ports Exposés (P0)

### Services Docker - Ports exposés vers l'extérieur

| Service | Port | Protocole | Risque | Recommandation |
|---------|------|-----------|--------|----------------|
| **NATS** | 4222 | TCP (Client) | 🔴 **AuthN Absente** | ❌ Binding 127.0.0.1 uniquement |
| **NATS** | 8222 | TCP (HTTP/monitoring) | 🔴 **Info disclosure** | ❌ Binding 127.0.0.1 uniquement |
| **NATS** | 6222 | TCP (Cluster) | 🟢 Interne | ✅ Ok en dev |
| **Redis** | 6379 | TCP | 🔴 **Pas d'AUTH** | ❌ AUTH + Binding 127.0.0.1 |
| **PostgreSQL** | 5432 | TCP | 🔴 **Password weak** | ❌ AUTH forte + TLS |
| **API** | 8000 | TCP/HTTP | 🟡 Dev seulement | ⚠️ Auth requise en prod |
| **WebUI** | 3000 | TCP/Node | 🟡 Dev seulement | ⚠️ Auth requise en prod |
| **Kernel** | 8080 | TCP | 🟡 Dev seulement | ⚠️ Auth requise en prod |

### Problèmes :

```yaml
# docker-compose.yml - PROBLÈME : External binding
nats:
  ports:
    - "4222:4222"    # ❌ Tous accès
    - "8222:8222"    # ❌ Monitoring exposé
redis:
  ports:
    - "6379:6379"    # ❌ Tous accès
postgres:
  ports:
    - "5432:5432"    # ❌ Tous accès
```

---

## 3. Secrets (P0)

### 3.1 Secrets en clair détectés

| Fichier | Type | Risque |
|---------|------|--------|
| `infrastructure/secrets/*.txt` | Passwords | 🔴 Fichiers texte en clair |
| `.env.example` | Template | ⚠️ `POSTGRES_PASSWORD=change-me-in-prod` |
| `.env` (potentiel) | Runtime | 🔴 Variables d'env non chiffrées |

### 3.2 Aucune gestion de secrets

```python
# infrastructure/secrets/README.md
# ❌ Recommande des fichiers .txt :
echo "mon_mot_de_passe_securise" > infrastructure/secrets/postgres_password.txt
```

### 3.3 Variables d'environnement non protégées

```dockerfile
# deploy/Dockerfile.api
ENV PYTHONPATH=/app/core:/app/interfaces/api:/app/sdk:/app
# ❌ Les variables sont visibles dans `docker inspect`
```

---

## 4. Authentification & Autorisation (P0)

### 4.1 API - Aucune authentification

```python
# interfaces/api/main.py - Analyse des routes
@app.get("/health")     # ❌ Public
@app.get("/version")    # ❌ Public
@app.post("/v1/chat")   # ❌ Public (pas de JWT/API key)
```

### 4.2 NATS - Aucune authentification

```bash
# docker-compose.yml
nats:
  command: ["-js"]
  # ❌ Pas de --user, --password, ou --auth
```

### 4.3 Redis - Aucune authentification

```yaml
# ❌ Aucune configuration AUTH
redis:
  # REDIS_PASSWORD non définie
```

---

## 5. Sandbox & Isolation (P0)

### 5.1 Plugin Sandbox - INACTIF

```python
# plugins/sandbox.py
@contextlib.asynccontextmanager
async def enforce(self):
    try:
        yield self
    finally:
        pass  # ❌ NOOP - Aucune isolation
```

### 5.2 Imports non restreints dans plugins

```python
# plugins/loader.py - Import direct
spec.loader.exec_module(mod)  # ❌ Le module a accès à tout
```

### 5.3 User Docker socket

```yaml
# ethan-core.service
Group=docker  # ❌ Accès au socket Docker = root equiv
```

---

## 6. Escalade de Privilèges (P0)

### 6.1 Vecteurs d'escalade

| Vecteur | Sévérité | Description |
|---------|----------|-------------|
| Docker socket | 🔴 Crit | `Group=docker` donne les droits root |
| Plugin loader | 🔴 Crit | `exec_module()` sans sandbox |
| NoNewPrivileges=false | 🟡 Élevé | Les plugins peuvent hériter |

### 6.2 Service systemd

```ini
# infrastructure/systemd/ethan-core.service
User=%i  # ❌ Template - peut être root!
Group=docker  # 🔴 Equiv root
NoNewPrivileges=true  # ✅ Bon, mais...
ProtectSystem=false  # ⚠️ Nécessaire pour volumes
```

---

## 7. Hardening Recommandé (P1-P3)

### 7.1 Docker Compose - Ports internes seulement

```yaml
# docker-compose.prod.yml
services:
  nats:
    ports: []  # ❌ Supprimer les expositions
    # Utiliser network interne seulement
    
  redis:
    command: ["redis-server", "--requirepass", "${REDIS_PASSWORD}"]
    secrets:
      - redis_password
      
  postgres:
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/postgres_password
    secrets:
      - postgres_password
      
  api:
    ports:
      - "127.0.0.1:8000:8000"  # ✅ Binding local uniquement
```

### 7.2 Authentification API

```python
# interfaces/api/main.py
# Ajouter :
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

@app.middleware("auth")
async def auth_middleware(request: Request, call_next):
    # Vérifier JWT/API key
    pass
```

### 7.3 Secrets avec HashiCorp Vault

```yaml
# docker-compose.yml
vault:
  image: hashicorp/vault:latest
  cap_add:
    - IPC_LOCK
  environment:
    VAULT_DEV_ROOT_TOKEN_ID: ${VAULT_ROOT_TOKEN}
```

### 7.4 Security Headers WebUI

```typescript
// interfaces/webui/next.config.js
headers: [
  {
    key: 'X-Frame-Options',
    value: 'DENY'
  },
  {
    key: 'X-Content-Type-Options',
    value: 'nosniff'
  }
]
```

---

## 8. Table de Risques

| ID | Risque | Sévérité | Exploitabilité | Impact | CVSS |
|----|--------|-----------|----------------|--------|------|
| S1 | Ports exposés sans auth | 🔴 Crit | Élevée | Critique | 9.8 |
| S2 | Sandbox plugins inactif | 🔴 Crit | Élevée | Critique | 9.1 |
| S3 | Secrets en clair fichiers | 🔴 Crit | Moyenne | Élevée | 7.5 |
| S4 | Docker socket accessible | 🔴 Crit | Moyenne | Critique | 8.8 |
| S5 | API sans authentification | 🔴 Crit | Élevée | Élevée | 8.2 |
| S6 | Redis sans AUTH | 🟡 Élevé | Moyenne | Élevée | 6.5 |
| S7 | PostgreSQL password weak | 🟡 Élevé | Faible | Élevée | 5.9 |

---

## 9. Actions Prioritaires (Roadmap)

### P0 - Critique (24h)

- [ ] **Fermer ports NATS/Redis/Postgres** vers l'extérieur
- [ ] **Activer AUTH sur Redis** (`--requirepass`)
- [ ] **Implémenter authentification API** (JWT/Bearer)
- [ ] **Corriger sandbox plugins** (subprocess isolation)

### P1 - Élevé (1 semaine)

- [ ] **Migrer secrets vers Vault** ou Docker secrets
- [ ] **Chiffrer volumes Docker** (AES-256)
- [ ] **Ajouter Rate Limiting** sur API
- [ ] **Security headers WebUI**

### P2 - Moyen (1 mois)

- [ ] **RBAC pour plugins** (capabilities + permissions)
- [ ] **Audit logging** complet
- [ ] **WAF intégration** (Traefik + ModSecurity)
- [ ] **Tests de pénétration**

---

## 10. Checklist Hardening Production

```bash
# Avant mise en production:
# 1. Secrets
- [ ] Vault configuré ou Docker secrets
- [ ] POSTGRES_PASSWORD ≠ "change-me"
- [ ] REDIS_PASSWORD défini

# 2. Réseau
- [ ] Ports externes supprimés (sauf 80/443)
- [ ] Firewall ufw actif
- [ ] fail2ban configuré

# 3. Auth
- [ ] JWT activé sur API
- [ ] NATS auth activé
- [ ] Redis AUTH activé

# 4. Sandbox
- [ ] Plugin subprocess isolation
- [ ] Resource limits (memory, CPU)
- [ ] Network policies (plugins)

# 5. Monitoring
- [ ] Audit logs activés
- [ ] Health checks complets
- [ ] Alerting (grafana)
```

---

**Conclusion** : ETHAN n'est pas utilisable en production sans les correctifs P0. L'absence d'authentification et le sandbox plugins inactif sont des vulnérabilités critiques.

**Score de risque global : 3.2/10** - **Déploiement interdit sans hardening**.