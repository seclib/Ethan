# Guide d'Implémentation P3 — Optimisations

**Objectif** : Clarifier la stratégie technique et l'observabilité  
**Date** : 2026-07-19  
**Priorité** : P3 (Long terme)  
**Temps estimé** : 3-4 semaines  
**Responsable** : Équipe Architecture + DevOps

---

## Vue d'ensemble des actions P3

```
┌─────────────────────────────────────────────────────────────┐
│                  Actions P3 à implémenter                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ⏳ P3-1 : Clarifier la stratégie Go vs Python pour Core   │
│     ├─ Fichiers : core/main.go, core/go.mod, core/kernel.py│
│     ├─ Options : Tout Python, Tout Go, Cohabitation        │
│     └─ Deadline décision : 2026-08-02                      │
│                                                             │
│  ⏳ P3-2 : Décider du sort de jarvis-OS/                   │
│     ├─ Fichier : jarvis-OS/                                │
│     ├─ Options : Supprimer, Documenter, Intégrer           │
│     └─ Deadline décision : 2026-08-02                      │
│                                                             │
│  ⏳ P3-3 : Ajouter des traces OpenTelemetry                 │
│     ├─ Fichier : core/telemetry/, interfaces/api/          │
│     ├─ Action : Jaeger, traces distribuées                 │
│     └─ Deadline : 2026-08-16                               │
│                                                             │
│  ⏳ P3-4 : Améliorer l'observabilité avec Grafana           │
│     ├─ Fichier : infrastructure/grafana/                   │
│     ├─ Action : Dashboard, datasources                     │
│     └─ Deadline : 2026-08-16                               │
│                                                             │
│  ⏳ P3-5 : CI/CD avec vérification automatique              │
│     ├─ Fichier : .github/workflows/, Makefile              │
│     ├─ Action : Pipeline CI/CD complet                     │
│     └─ Deadline : 2026-08-16                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## P3-1 : Clarifier la stratégie Go vs Python pour Core

**Fichiers concernés** :
- `core/main.go`
- `core/go.mod`
- `core/kernel.py`
- `core/bootstrap.py`
- `core/main.py`

**Deadline décision** : 2026-08-02  
**Responsable** : Architecture Team + CTO  
**Temps estimé** : 1-2 semaines

---

### Problème

Core présente une dualité Go/Python qui crée de la confusion :

```
core/
├── main.go      # Entrypoint Go (théorique)
├── go.mod       # Module Go
├── kernel.py    # Kernel Python (réel)
├── bootstrap.py # Bootstrap Python (utilisé par Docker)
└── main.py      # Entrypoint Python
```

### Solution

Choisir une stratégie et la documenter.

---

### Analyse préalable

#### Étape 1 : Vérifier quel entrypoint est utilisé

```bash
# Vérifier docker-compose.yml
grep -n "command:" docker-compose.yml | grep -E "kernel|bootstrap|main"

# Vérifier infrastructure/systemd/
grep -n "ExecStart" infrastructure/systemd/ethan-core.service

# Vérifier les Dockerfiles
grep -n "CMD\|ENTRYPOINT" deploy/Dockerfile.kernel
```

#### Étape 2 : Vérifier les imports croisés

```bash
# Vérifier si kernel.py importe main.go (impossible, mais vérifier)
grep -r "main.go" core/ || echo "Aucun import"

# Vérifier si main.go existe et est compilable
go build -o /tmp/core-go ./core/main.go 2>&1 || echo "Build Go échoue"

# Vérifier la taille de main.go
wc -l core/main.go
```

#### Étape 3 : Mesurer les performances

```bash
# Mesurer le temps de démarrage de Python
time python core/bootstrap.py --help 2>/dev/null || echo "/bootstrap.py ne supporte pas --help"

# Mesurer le temps de compilation Go
time go build -o /tmp/core-go ./core/main.go 2>&1 || echo "Build Go échoue"
```

---

### Options de décision

#### Option A : Tout migrer vers Python

**Quand l'appliquer** : Si la performance Go n'est pas critique

**Avantages** :
- Cohérence du codebase
- Pas de dualité
- Meilleure maintenabilité
- Écosystème Python riche

**Inconvénients** :
- Perte des performances Go
- Migration importante

**Procédure** :

```bash
# 1. Sauvegarder main.go et go.mod
mkdir -p legacy/go
mv core/main.go legacy/go/
mv core/go.mod legacy/go/

# 2. Supprimer les fichiers Go de core/
rm -f core/main.go core/go.sum

# 3. Mettre à jour les Dockerfiles
# Dans deploy/Dockerfile.kernel, vérifier que c'est bien Python

# 4. Mettre à jour README.md
sed -i 's/Core Kernel.*Go + Python/Core Kernel : Python/g' README.md

# 5. Commit
git add -A
git commit -m "refactor: migrate Core to Python only"
```

**Validation** :

```bash
# Tester le démarrage
./ethan up
./ethan status

# Vérifier les performances
time curl -f http://localhost:8000/health
```

---

#### Option B : Tout migrer vers Go

**Quand l'appliquer** : Si la performance est critique

**Avantages** :
- Performance
- Compilation statique
- Meilleur pour un daemon systemd

**Inconvénients** :
- Migration très importante
- Perte de la flexibilité Python
- Nécessite de réécrire tous les modules

**Procédure** :

```bash
# 1. Sauvegarder les fichiers Python
mkdir -p legacy/python
mv core/kernel.py legacy/python/
mv core/bootstrap.py legacy/python/
mv core/main.py legacy/python/

# 2. Réécrire kernel.py en Go (TRÈS important)
# ... nécessite un développement important

# 3. Commit (progressif)
git add -A
git commit -m "feat: start Go migration for Core kernel"
```

**Note** : Cette option demande des semaines de développement.

---

#### Option C : Cohabitation (recommandé)

**Quand l'appliquer** : Si on veut préserver les deux

**Avantages** :
- Préserve le code existant
- Migration progressive possible
- Meilleur des deux mondes

**Inconvénients** :
- Dualité maintenue
- Complexité accrue

**Procédure** :

```bash
# 1. Clarifier les rôles

# Déplacer main.go vers kernel-go/
mkdir -p core/kernel-go
mv core/main.go core/kernel-go/
mv core/go.mod core/kernel-go/

# 2. Créer un README explicatif
cat > core/kernel-go/README.md << 'EOF'
# Kernel Go (Performance Layer)

## Role

This is the high-performance Go kernel responsible for:
- Event routing
- Request/Reply patterns
- High-throughput event processing

## Interface with Python

The Go kernel communicates with the Python cognitive kernel via:
- gRPC (protobuf in proto/)
- Shared NATS bus

## Status

⚠️ Not yet production-ready. Python kernel is still primary.
EOF

# 3. Documenter l'interface
cat > docs/kernel-interface.md << 'EOF'
# Interface entre Go et Python

## Architecture

Go Kernel (performance) ←→ NATS ←→ Python Kernel (cognitive)

## Communication

- Go écoute sur : ethan.kernel.*
- Python écoute sur : ethan.module.*
- Partage : Redis + PostgreSQL
EOF

# 4. Commit
git add -A
git commit -m "docs: clarify Go/Python kernel cohabitation strategy"
```

**Validation** :

```bash
# Vérifier que les deux kernels fonctionnent
./ethan up
./ethan status
```

---

### Checklist P3-1

- [ ] Vérifier quel entrypoint est utilisé (Étape 1)
- [ ] Vérifier les imports croisés (Étape 2)
- [ ] Mesurer les performances (Étape 3)
- [ ] Décider de l'option (A, B, ou C)
- [ ] Implémenter la décision
- [ ] Documenter la stratégie
- [ ] Mettre à jour README.md
- [ ] Tester le démarrage
- [ ] Commiter

---

## P3-2 : Décider du sort de `jarvis-OS/`

**Fichier concerné** : `jarvis-OS/` (racine)  
**Deadline décision** : 2026-08-02  
**Responsable** : Architecture Team  
**Temps estimé** : 1-2 jours

---

### Problème

Dossier `jarvis-OS/` présent à la racine du projet ETHAN. Nature inconnue.

### Solution

Analyser et décider du sort de ce dossier.

---

### Analyse préalable

#### Étape 1 : Examiner le contenu

```bash
# Lister les fichiers
ls -la jarvis-OS/

# Vérifier la taille
du -sh jarvis-OS/

# Vérifier les types de fichiers
find jarvis-OS/ -type f | head -20
```

#### Étape 2 : Vérifier les imports

```bash
# Chercher des imports de jarvis-OS
grep -r "jarvis" core/ plugins/ interfaces/ || echo "Aucun import"

# Chercher des imports relatifs
grep -r "from jarvis" . || echo "Aucun import"
```

#### Étape 3 : Vérifier l'historique git

```bash
# Voir quand jarvis-OS/ a été ajouté
git log --oneline --all -- jarvis-OS/ | head -20

# Voir le dernier commit qui le mentionne
git log --oneline --all --since="2024-01-01" -- jarvis-OS/
```

#### Étape 4 : Vérifier la documentation

```bash
# Chercher des mentions de jarvis-OS
grep -r "jarvis" docs/ engineering/ README.md || echo "Aucune mention"
```

---

### Options de décision

#### Option A : Ancien projet (legacy)

**Quand l'appliquer** : Si c'est un projet précédent intégré par erreur

**Procédure** :

```bash
# 1. Sauvegarder dans un tag git
git tag -a legacy-jarvis-$(date +%Y%m%d) -m "Legacy jarvis-OS before removal"

# 2. Supprimer le dossier
rm -rf jarvis-OS/

# 3. Nettoyer .gitignore (optionnel)
echo "jarvis-OS/" >> .gitignore

# 4. Commit
git add -A
git commit -m "chore: remove legacy jarvis-OS directory"
```

---

#### Option B : Projet lié (évolution)

**Quand l'appliquer** : Si c'est une branche d'évolution d'ETHAN

**Procédure** :

```bash
# 1. Documenter la relation
cat > jarvis-OS/README.md << 'EOF'
# Jarvis OS

## Relation with ETHAN

Jarvis OS is the predecessor/evolution of ETHAN.

## Key differences

- ...
- ...

## Migration path

- ...
EOF

# 2. Déplacer vers examples/
mv jarvis-OS/ examples/jarvis-os-legacy/

# 3. Commit
git add -A
git commit -m "docs: document Jarvis OS as ETHAN predecessor"
```

---

#### Option C : Projet séparé (monorepo)

**Quand l'appliquer** : Si c'est un projet distinct mais lié

**Procédure** :

```bash
# 1. Ajouter un README dans jarvis-OS/
cat > jarvis-OS/README.md << 'EOF'
# Jarvis OS

## Status

⚠️ This is a separate project maintained in the same repository.

## Relationship with ETHAN

- Shares some components
- Separate release cycle
- Independent deployment

## Documentation

See README.md in this directory.
EOF

# 2. Documenter dans le README principal
echo "## Related Projects" >> README.md
echo "- [Jarvis OS](jarvis-OS/) — Separate project" >> README.md

# 3. Commit
git add -A
git commit -m "docs: clarify Jarvis OS as separate project"
```

---

### Checklist P3-2

- [ ] Examiner le contenu (Étape 1)
- [ ] Vérifier les imports (Étape 2)
- [ ] Vérifier l'historique git (Étape 3)
- [ ] Vérifier la documentation (Étape 4)
- [ ] Décider de l'option (A, B, ou C)
- [ ] Implémenter la décision
- [ ] Documenter la relation
- [ ] Commiter

---

## P3-3 : Ajouter des traces OpenTelemetry

**Fichier concerné** : `core/telemetry/`, `interfaces/api/`  
**Deadline** : 2026-08-16  
**Responsable** : Équipe DevOps  
**Temps estimé** : 3-5 jours

---

### Problème

Pas de tracing distribué pour suivre les événements à travers les modules.

### Solution

Ajouter OpenTelemetry avec Jaeger comme backend.

---

### Procédure

#### Étape 1 : Installer les dépendances

```bash
pip install opentelemetry-api opentelemetry-sdk
pip install opentelemetry-exporter-jaeger
pip install opentelemetry-instrumentation-fastapi
```

#### Étape 2 : Créer infrastructure/jaeger/jaeger.yml

```bash
mkdir -p infrastructure/jaeger

cat > infrastructure/jaeger/jaeger.yml << 'EOF'
# Configuration Jaeger
jaeger:
  storage:
    type: memory
    options:
      memory:
        max-traces: 100000
  collector:
    heartbeat-count: 10000
    heartbeat-interval: 5s
EOF
```

#### Étape 3 : Ajouter OpenTelemetry dans core/telemetry/__init__.py

```python
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

def init_telemetry(service_name: str = "ethan-core"):
    """Initialiser le tracing OpenTelemetry."""
    # Créer le provider
    provider = TracerProvider(
        resource=Resource.create({
            "service.name": service_name,
            "service.version": "1.0.0",
        })
    )
    
    # Ajouter l'exporter Jaeger
    jaeger_exporter = JaegerExporter(
        agent_host_name="localhost",
        agent_port=14268,
    )
    provider.add_span_processor(
        BatchSpanProcessor(jaeger_exporter)
    )
    
    # Définir le provider global
    trace.set_tracer_provider(provider)
    
    return trace.get_tracer(__name__)
```

#### Étape 4 : Instrumenter interfaces/api/main.py

```python
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from core.telemetry import init_telemetry

# Dans startup()
tracer = init_telemetry("ethan-api")
FastAPIInstrumentor.instrument_app(app)
```

#### Étape 5 : Ajouter Jaeger dans docker-compose.yml

```yaml
jaeger:
  image: jaegertracing/all-in-one:1.50
  ports:
    - "16686:16686"  # UI
    - "14268:14268"  # Collector
    - "14250:14250"  # gRPC
  networks:
    - ethan-core
  environment:
    - COLLECTOR_OTLP_ENABLED=true
```

#### Étape 6 : Tester les traces

```bash
# Démarrer les services
./ethan up

# Générer du trafic
curl -f http://localhost:8000/health
curl -f http://localhost:8000/version

# Ouvrir Jaeger UI
open http://localhost:16686

# Rechercher des traces
# Service: ethan-api
# Operation: GET /health
```

#### Étape 7 : Commit

```bash
git add -A
git commit -m "feat: add OpenTelemetry tracing with Jaeger"
```

---

### Checklist P3-3

- [ ] Installer dépendances OpenTelemetry
- [ ] Créer `infrastructure/jaeger/jaeger.yml`
- [ ] Créer `core/telemetry/__init__.py`
- [ ] Instrumenter `interfaces/api/main.py`
- [ ] Ajouter Jaeger dans `docker-compose.yml`
- [ ] Tester les traces
- [ ] Tester Jaeger UI
- [ ] Commiter

---

## P3-4 : Améliorer l'observabilité avec Grafana

**Fichier concerné** : `infrastructure/grafana/`  
**Deadline** : 2026-08-16  
**Responsable** : Équipe DevOps  
**Temps estimé** : 3-5 jours

---

### Problème

Pas de dashboard visuel pour monitorer le système.

### Solution

Ajouter Grafana avec un dashboard pré-configuré.

---

### Procédure

#### Étape 1 : Créer la structure

```bash
mkdir -p infrastructure/grafana/dashboards
mkdir -p infrastructure/grafana/datasources
mkdir -p infrastructure/grafana/provisioning
```

#### Étape 2 : Créer infrastructure/grafana/datasources/prometheus.yml

```bash
cat > infrastructure/grafana/datasources/prometheus.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF
```

#### Étape 3 : Créer infrastructure/grafana/dashboards/ethan-dashboard.json

```bash
cat > infrastructure/grafana/dashboards/ethan-dashboard.json << 'EOF'
{
  "dashboard": {
    "title": "ETHAN System Monitoring",
    "tags": ["ethan"],
    "timezone": "UTC",
    "panels": [
      {
        "title": "Events processed/sec",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(ethan_events_total[1m])",
            "legendFormat": "{{module}} - {{status}}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      },
      {
        "title": "Active modules",
        "type": "gauge",
        "targets": [
          {
            "expr": "ethan_modules_active"
          }
        ],
        "gridPos": {"h": 8, "w": 6, "x": 12, "y": 0}
      },
      {
        "title": "Event latency (p95)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(ethan_event_latency_seconds_bucket[5m]))"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 18, "y": 0}
      }
    ]
  }
}
EOF
```

#### Étape 4 : Créer infrastructure/grafana/provisioning/dashboards.yml

```bash
cat > infrastructure/grafana/provisioning/dashboards.yml << 'EOF'
apiVersion: 1

providers:
  - name: 'ethan'
    orgId: 1
    folder: 'ETHAN'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/dashboards
EOF
```

#### Étape 5 : Ajouter Grafana dans docker-compose.yml

```yaml
grafana:
  image: grafana/grafana:latest
  ports:
    - "3001:3000"
  volumes:
    - grafana_data:/var/lib/grafana
    - ./infrastructure/grafana/provisioning:/etc/grafana/provisioning
    - ./infrastructure/grafana/dashboards:/etc/grafana/dashboards
  networks:
    - ethan-core
  depends_on:
    - prometheus
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=admin
    - GF_SERVER_ROOT_URL=http://localhost:3001
```

#### Étape 6 : Tester Grafana

```bash
# Démarrer les services
./ethan up

# Ouvrir Grafana
open http://localhost:3001

# Login: admin / admin

# Vérifier le dashboard
# Aller dans Dashboards → ETHAN System Monitoring
```

#### Étape 7 : Commit

```bash
git add -A
git commit -m "feat: add Grafana dashboard for ETHAN monitoring"
```

---

### Checklist P3-4

- [ ] Créer la structure de dossiers
- [ ] Créer `datasources/prometheus.yml`
- [ ] Créer `dashboards/ethan-dashboard.json`
- [ ] Créer `provisioning/dashboards.yml`
- [ ] Ajouter Grafana dans `docker-compose.yml`
- [ ] Tester Grafana UI
- [ ] Vérifier le dashboard
- [ ] Commiter

---

## P3-5 : CI/CD avec vérification automatique

**Fichier concerné** : `.github/workflows/`, `Makefile`  
**Deadline** : 2026-08-16  
**Responsable** : Équipe DevOps  
**Temps estimé** : 3-5 jours

---

### Problème

Pas de pipeline CI/CD pour :
- Vérifier les imports
- Exécuter les tests
- Vérifier le linting
- Détecter les dépendances circulaires

### Solution

Mettre en place une CI/CD complète avec GitHub Actions.

---

### Procédure

#### Étape 1 : Créer .github/workflows/ci.yml

```bash
cat > .github/workflows/ci.yml << 'EOF'
name: CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  lint:
    name: Linting
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install ruff
        run: pip install ruff
      - name: Lint Python
        run: ruff check core/ interfaces/ plugins/
      - name: Lint bash
        run: shellcheck scripts/*.sh

  test-imports:
    name: Test Imports
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v3
      - name: Start services
        run: ./ethan up
      - name: Test imports
        run: pytest tests/test_imports.py -v
      - name: Stop services
        run: ./ethan down

  integration-tests:
    name: Integration Tests
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v3
      - name: Start services
        run: ./ethan up
      - name: Run tests
        run: pytest tests/ -v --cov=core --cov=interfaces
      - name: Upload coverage
        uses: codecov/codecov-action@v3
      - name: Stop services
        run: ./ethan down

  docker-build:
    name: Docker Build
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v3
      - name: Build API
        run: docker compose build api
      - name: Build Kernel
        run: docker compose build kernel
      - name: Build UI
        run: docker compose build ui

  deploy:
    name: Deploy
    runs-on: ubuntu-latest
    needs: [test-imports, integration-tests, docker-build]
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to production
        run: |
          echo "Add deployment steps here"
EOF
```

#### Étape 2 : Ajouter des cibles Makefile

```bash
cat >> Makefile << 'EOF'

.PHONY: help
help: ## Afficher l'aide
	@echo "Commandes disponibles :"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

.PHONY: ci
ci: lint test-integration docker-build ## Lancer la CI complète
	@echo "✓ CI passed"

.PHONY: lint
lint: ## Linter le code
	ruff check core/ interfaces/ plugins/
	shellcheck scripts/*.sh

.PHONY: test-imports
test-imports: ## Tester les imports
	./ethan up
	pytest tests/test_imports.py -v
	./ethan down

.PHONY: test-integration
test-integration: ## Tests d'intégration
	./ethan up
	pytest tests/ -v
	./ethan down

.PHONY: docker-build
docker-build: ## Builder les images Docker
	docker compose build

.PHONY: clean
clean: ## Nettoyer
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
EOF
```

#### Étape 3 : Tester la CI localement

```bash
# Installer act (CLI GitHub Actions)
curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Lancer la CI localement
act -j lint
```

#### Étape 4 : Commit

```bash
git add -A
git commit -m "feat: add CI/CD pipeline with GitHub Actions"
```

---

### Checklist P3-5

- [ ] Créer `.github/workflows/ci.yml`
- [ ] Ajouter cibles Makefile
- [ ] Tester la CI localement (optionnel)
- [ ] Pusher et vérifier sur GitHub
- [ ] Vérifier les workflows
- [ ] Ajouter badges dans README.md
- [ ] Commiter

---

## Tests de validation P3

### Test 1 : Go vs Python

```bash
# Vérifier que le kernel fonctionne
./ethan up
./ethan status

# Vérifier les logs
./ethan logs kernel
```

### Test 2 : OpenTelemetry

```bash
# Vérifier les traces
curl -f http://localhost:8000/metrics

# Ouvrir Jaeger
open http://localhost:16686
```

### Test 3 : Grafana

```bash
# Vérifier Grafana
curl -f http://localhost:3001/api/health

# Ouvrir le dashboard
open http://localhost:3001
```

### Test 4 : CI/CD

```bash
# Vérifier les workflows
gh workflow list

# Tester un workflow
gh workflow run ci.yml
```

---

## Commandes rapides

### Initialiser OpenTelemetry

```bash
pip install opentelemetry-api opentelemetry-sdk
pip install opentelemetry-exporter-jaeger
```

### Tester Jaeger

```bash
./ethan up
curl -f http://localhost:16686/api/traces
open http://localhost:16686
```

### Tester Grafana

```bash
./ethan up
open http://localhost:3001
```

### Lancer la CI

```bash
make ci
```

---

## Support

- **Roadmap P3** : `docs/roadmap-P3.md`
- **Roadmap globale** : `docs/roadmap-global.md`
- **Guide P0** : `docs/implementation-guide-P0.md`
- **Guide P1** : `docs/implementation-guide-P1.md`
- **Guide P2** : `docs/implementation-guide-P2.md`

---

## Prochaines étapes

1. **Architecture Team** : Décider P3-1 et P3-2 (deadline 2026-08-02)
2. **Équipe DevOps** : Ajouter OpenTelemetry (P3-3)
3. **Équipe DevOps** : Ajouter Grafana (P3-4)
4. **Équipe DevOps** : Mettre en place CI/CD (P3-5)

**Dernière mise à jour** : 2026-07-19