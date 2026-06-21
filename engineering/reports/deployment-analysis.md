# Deployment Analysis — Ethan

> RFC-001 — Analyse du déploiement
> Date : 2026-06-21

---

## 1. Docker

### 1.1 Dockerfiles

| Fichier | Usage | Base | Multi-stage |
|---------|-------|------|-------------|
| `Dockerfile` | Backend original | python:3.12-slim | Oui |
| `Dockerfile.backend` | Backend restructuré | python:3.12-slim | Oui |
| `Dockerfile.frontend` | Frontend production | node:22-slim → nginx:alpine | Oui |
| `Dockerfile.gpu` | GPU NVIDIA support | nvidia/cuda | Oui |
| `Dockerfile.gpu.rocm` | GPU AMD support | rocm/dev-ubuntu | Oui |
| `Dockerfile.sandbox` | Sandbox sécurisé | python:3.12-slim | Non |

**Observations :**
- Multi-stage builds bien implémentés
- Images optimisées (python-runtime stage)
- GPU support (NVIDIA + AMD)
- Sandbox isolé

### 1.2 Docker Compose

**Production** (`docker-compose.yml`) :
- 10 services
- 12 volumes persistants
- Réseau dédié `jarvis-network`
- Healthchecks sur tous les services
- Restart policies : `unless-stopped`

**Développement** (`docker-compose.dev.yml`) :
- Hot reload backend (uvicorn --reload)
- Hot reload frontend (Vite dev server)
- Volumes montés pour code live
- Debug port 5678

**GPU** :
- `docker-compose.gpu.nvidia.yml` — GPU NVIDIA
- `docker-compose.gpu.rocm.yml` — GPU AMD

### 1.3 .dockerignore

- Exclut .git, node_modules, __pycache__, etc.
- Présent et correctement configuré

---

## 2. Reverse Proxy (Traefik)

### 2.1 Configuration

| Fichier | Usage |
|---------|-------|
| `deploy/traefik/traefik.yml` | Configuration principale (entrypoints, providers, etc.) |
| `deploy/traefik/dynamic.yml` | Routage dynamique (frontend, backend, websocket) |

### 2.2 Routage

```
http://localhost/          → frontend:80
http://localhost/api       → backend:8000
http://localhost/docs      → backend:8000/docs
http://localhost/ws        → backend:8000/ws
http://localhost:8080      → Traefik dashboard
```

### 2.3 SSL

- Let's Encrypt activé via `certificatesResolvers.letsencrypt`
- Certificats stockés dans volume `traefik-letsencrypt`
- Auto-renouvellement automatique

---

## 3. Monitoring

### 3.1 Prometheus

| Aspect | Détail |
|--------|--------|
| Port | 9090 |
| Retention | 30 jours |
| Scraping | Toutes les 10-15s |
| Alertes | 12 règles (Backend, Traefik, Redis, PostgreSQL, Ollama, Système) |

**Targets scrapés :**
- Backend : `/metrics`
- Traefik : `/metrics`
- Redis : `/metrics`
- PostgreSQL : `/metrics`

### 3.2 Grafana

| Aspect | Détail |
|--------|--------|
| Port | 3000 |
| Datasource | Prometheus (provisioning automatique) |
| Dashboard | Ethan Overview (CPU, RAM, API latency, agents, errors) |

---

## 4. Déploiement Native

### 4.1 Linux (systemd)

- Fichier : `deploy/systemd/ethan.service`
- Service systemd pour exécution en tant que daemon

### 4.2 macOS (launchd)

- Fichier : `deploy/launchd/com.ethan.plist`
- Service launchd pour macOS

### 4.3 Windows

- Fichiers : `deploy/windows/install.ps1`, `deploy/windows/jarvis-service.ps1`
- Installation automatisée via PowerShell
- Windows service

---

## 5. Kubernetes

**État : ❌ VIDE**

- Dossier `deploy/kubernetes/` existe mais est vide
- Aucun manifest K8s
- Aucun Helm chart

**Risque :** Impossible de déployer sur Kubernetes actuellement.

---

## 6. CI/CD

### 6.1 GitHub Actions

- `.github/workflows/` — Présent mais non analysé en détail

### 6.2 Pre-commit

- Fichier : `.pre-commit-config.yaml` — Présent
- Ruff pour linting Python

---

## 7. Recommandations

| Priorité | Recommandation | Justification |
|----------|---------------|---------------|
| **Haute** | Créer manifests Kubernetes | Absence totale de support K8s |
| **Haute** | Multi-arch images (amd64 + arm64) | Nécessaire pour Raspberry Pi, NAS |
| **Moyenne** | Image size optimization | Images Python ~500MB |
| **Moyenne** | Healthcheck améliorés pour services critiques | Certains healthchecks sont basiques |
| **Moyenne** | Sécurité Docker (non-root user) | Vérifier que les services tournent en non-root |
| **Faible** | Docker Scout / Trivy scanning | Security scanning manquant |