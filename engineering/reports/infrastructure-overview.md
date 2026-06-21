# Infrastructure Overview — Ethan

> RFC-002 — Analyse de l'infrastructure
> Date : 2026-06-21

---

## 1. Infrastructure Docker

### 1.1 Architecture Réseau

```
Internet
    │
    ▼
┌──────────┐
│  Traefik  │  Ports: 80 (HTTP), 443 (HTTPS), 8080 (Dashboard)
│  v3.1     │  Réseau: jarvis-network (bridge)
└────┬─────┘
     │
     ├──────────────────┬──────────────────┐
     ▼                  ▼                  ▼
┌──────────┐     ┌──────────┐     ┌──────────────┐
│ Frontend │     │ Backend  │     │  Prometheus  │
│ Nginx:80 │     │ FastAPI  │     │  Port: 9090  │
└──────────┘     │ :8000    │     └──────┬───────┘
                 └────┬─────┘            │
                      │             ┌────┴──────┐
                      │             │  Grafana  │
                      │             │ Port:3000 │
                      │             └───────────┘
         ┌────────────┼────────────┐
         ▼            ▼            ▼
    ┌────────┐  ┌──────────┐  ┌────────┐
    │ Ollama │  │  Redis   │  │Postgres│
    │:11434  │  │  :6379   │  │ :5432  │
    └────────┘  └──────────┘  └────────┘
                    │
         ┌──────────┴──────────┐
         ▼                     ▼
    ┌──────────┐         ┌──────────┐
    │ ChromaDB │         │  Qdrant  │
    │ :8000    │         │ :6333    │
    └──────────┘         └──────────┘
```

### 1.2 Volumes Persistants

| Volume | Montage | Service | Usage |
|--------|---------|---------|-------|
| jarvis-config | /etc/ethan | backend | Configuration |
| jarvis-logs | /var/log/ethan | backend | Logs applicatifs |
| jarvis-workspace | /workspace | backend | Espace de travail |
| jarvis-memory | /var/lib/ethan/memory | backend | Base SQLite |
| jarvis-uploads | /var/lib/ethan/uploads | backend | Fichiers uploadés |
| jarvis-cache | /var/lib/ethan/cache | backend | Cache disque |
| jarvis-models | /var/lib/ethan/models | backend | Modèles téléchargés |
| ollama-models | /root/.ollama | ollama | Modèles LLM |
| redis-data | /data | redis | Persistance Redis |
| postgres-data | /var/lib/postgresql/data | postgres | Données PostgreSQL |
| chromadb-data | /chroma/chroma | chromadb | Index vectoriels |
| qdrant-data | /qdrant/storage | qdrant | Index vectoriels |
| prometheus-data | /prometheus | prometheus | Métriques |
| grafana-data | /var/lib/grafana | grafana | Dashboards |

**Total : 14 volumes**

### 1.3 Dépendances de Service

```
Service         Dépend de              Type
─────────────────────────────────────────────────
traefik         (aucune)               -
frontend        backend:healthy        required
backend         ollama:healthy         optional
ollama          (aucune)               -
postgres        (aucune)               -
redis           (aucune)               -
chromadb        (aucune)               -
qdrant          (aucune)               -
prometheus      (aucune)               -
grafana         prometheus:healthy     required
```

---

## 2. Infrastructure Native

### 2.1 Linux (systemd)

```
Fichier: deploy/systemd/ethan.service

[Unit]
Description=Ethan AI Assistant
After=network.target

[Service]
Type=simple
User=ethan
ExecStart=/usr/local/bin/jarvis serve
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 2.2 macOS (launchd)

```
Fichier: deploy/launchd/com.ethan.plist

Label: com.ethan
ProgramArguments: /usr/local/bin/jarvis serve
RunAtLoad: true
KeepAlive: true
```

### 2.3 Windows (PowerShell)

```
Fichiers:
├── install.ps1          → Installation automatisée
└── jarvis-service.ps1   → Windows Service wrapper

Installation:
powershell -ExecutionPolicy Bypass -File install.ps1
```

---

## 3. Build Infrastructure

### 3.1 Python Build

```
Build system: Hatchling + hatch-vcs
Package manager: uv (uv.lock)
Python: 3.10 - 3.13
Entry points:
  - jarvis → ethan.cli:main
  - ethan-eval → ethan.evals.cli:main

Build command:
  uv build
  uv sync --extra server --extra inference-cloud
```

### 3.2 Frontend Build

```
Build system: Vite 6
TypeScript: 5.7
Node: >=20

Build command:
  npm run build        → Production build
  npm run dev          → Dev server (port 5173)
  npm run build:tauri  → Desktop build
```

### 3.3 Rust Build

```
Build system: Cargo
Rust: 1.88 minimum
Workspace: 16 crates
FFI: PyO3 0.23

Build command:
  cargo build --release
  maturin develop     → Python bindings
```

### 3.4 Docker Build

```
Backend:
  docker build -f deploy/docker/Dockerfile.backend -t ethan/backend .

Frontend:
  docker build -f deploy/docker/Dockerfile.frontend -t ethan/frontend .

Full stack:
  docker compose build
```

---

## 4. CI/CD Infrastructure

### 4.1 GitHub Actions

```
.github/workflows/
├── ci.yml              → Main CI pipeline
├── release.yml         → Release pipeline
└── docs.yml            → Documentation deploy
```

### 4.2 Pre-commit Hooks

```
.pre-commit-config.yaml
├── ruff (lint + format)
└── (autres hooks potentiels)
```

### 4.3 Makefile Targets

```
make help         → Aide
make install      → Installation dépendances
make build        → Build artefacts
make dev          → Dev environment
make prod         → Production
make test         → Tests
make lint         → Linting
make format       → Formatage
make clean        → Nettoyage
make docker-build → Build Docker
make docker-push  → Push Docker
make docs         → Documentation
```

---

## 5. Monitoring Infrastructure

### 5.1 Prometheus

```
Configuration: deploy/prometheus/prometheus.yml
Alertes: deploy/prometheus/alerts.yml (12 règles)
Retention: 30 jours / 10GB
Scrape interval: 10-15s

Targets:
├── backend:8000/metrics
├── traefik:8080/metrics
├── redis:6379/metrics
└── postgres:5432/metrics
```

### 5.2 Grafana

```
Configuration: deploy/grafana/
├── datasources/prometheus.yml  → Auto-provisioning
├── dashboards/dashboards.yml   → Auto-provisioning
└── dashboards/ethan-overview.json → Dashboard par défaut

Accès: http://localhost:3000 (admin / password)
```

### 5.3 Traefik

```
Configuration: deploy/traefik/
├── traefik.yml  → Configuration principale
└── dynamic.yml  → Routage dynamique

Dashboard: http://localhost:8080
SSL: Let's Encrypt (auto)
```

---

## 6. Dépendances Système

### 6.1 Packages Requis

```
Runtime:
├── Python 3.10+
├── Node.js 20+
├── Rust 1.88+
├── Docker 24+
└── Docker Compose 2+

Build:
├── uv (Python package manager)
├── npm (Node package manager)
├── cargo (Rust package manager)
└── make
```

### 6.2 GPU Support

```
NVIDIA:
├── nvidia-docker2
├── nvidia-container-toolkit
└── CUDA drivers

AMD:
├── rocm-docker
└── ROCm drivers

Apple Silicon:
├── MLX framework
└── Metal Performance Shaders
```

---

## 7. Sécurité Infrastructure

### 7.1 Secrets Management

```
Type            Stockage
────────────────────────────────────
API Keys        .env file (local)
JWT Secrets     .env file (local)
DB Passwords    .env file (local)
OAuth Tokens    Vault (via jarvis vault)
```

### 7.2 Network Security

```
Réseau: jarvis-network (bridge, isolé)
Exposition:
├── Traefik: 80/443 (public)
├── Backend: 8000 (interne)
├── Frontend: 80 (interne)
├── Prometheus: 9090 (interne)
├── Grafana: 3000 (interne)
└── Dashboard Traefik: 8080 (interne)
```

### 7.3 Container Security

```
Utilisateur: non-root (recommandé)
Read-only root: non configuré
Capabilities: non réduites
Security scanning: non configuré
```

---

## 8. Risques Infrastructure

| Risque | Impact | Probabilité | Mitigation |
|--------|--------|-------------|------------|
| Pas de K8s | Scalabilité | Haute | Manifests à créer |
| Pas de multi-arch | ARM exclus | Haute | Buildx à configurer |
| Secrets en .env | Exposition | Moyenne | Vault à intégrer |
| Pas de scanning | Vulnérabilités | Moyenne | Trivy/Docker Scout |
| Pas de backup volumes | Perte données | Haute | Backup strategy |
| Pas de rolling update | Downtime | Haute | K8s nécessaire |