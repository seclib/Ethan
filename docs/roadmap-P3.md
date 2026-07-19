# Roadmap P3 — Optimisations (Long terme)

**Objectif** : Clarifier la stratégie technique et l'observabilité  
**Date de création** : 2026-07-19  
**Statut** : En attente d'implémentation  
**Propriétaire** : Équipe Architecture

---

## P3-1 : Clarifier la stratégie Go vs Python pour Core

**Fichiers concernés** :
- `core/main.go`
- `core/go.mod`
- `core/kernel.py`
- `core/bootstrap.py`
- `core/main.py`

### Problème

Core présente une dualité Go/Python qui crée de la confusion :

```
core/
├── main.go      # Entrypoint Go (théorique)
├── go.mod       # Module Go
├── kernel.py    # Kernel Python (réel)
├── bootstrap.py # Bootstrap Python (utilisé)
└── main.py      # Entrypoint Python
```

### Analyse

#### Usage actuel

```bash
# Vérifier quel entrypoint est utilisé
grep -r "core.main" docker-compose.yml infrastructure/systemd/
grep -r "core.bootstrap" docker-compose.yml infrastructure/systemd/
grep -r "python.*bootstrap" docker-compose.yml
```

**Constats** :
- `docker-compose.yml` utilise : `python kernel/bootstrap.py`
- `infrastructure/systemd/ethan-core.service` utilise : `/opt/ethan/bin/ethan-core` (compilé Go ?)
- Aucun lien évident entre `main.go` et les fichiers Python

### Options

#### Option A : Tout migrer vers Python

**Avantages** :
- Cohérence du codebase
- Pas de dualité
- Meilleure maintenabilité

**Inconvénients** :
- Perte des performances Go
- Migration importante

**Actions** :
1. Supprimer `core/main.go` et `core/go.mod`
2. Documenter que Core est en Python
3. Mettre à jour tous les Dockerfiles
4. Mettre à jour le README

#### Option B : Tout migrer vers Go

**Avantages** :
- Performance
- Compilation statique
- Meilleur pour un daemon systemd

**Inconvénients** :
- Migration très importante
- Perte de la flexibilité Python
nécessite de réécrire tous les modules

**Actions** :
1. Supprimer `core/kernel.py`, `core/bootstrap.py`, `core/main.py`
2. Réécrire les modules en Go (ou garder Python via gRPC)
3. Mettre à jour tous les Dockerfiles
4. Mettre à jour le README

#### Option C : Cohabitation (recommandé)

**Avantages** :
- Préserve le code existant
- Migration progressive possible
- Meilleur des deux mondes

**Inconvénients** :
- Dualité maintenue
- Complexité accrue

**Actions** :
1. **Clarifier** les rôles :
   - `core/main.go` → Kernel Go (performance, routing)
   - `core/kernel.py` → Cognitive Kernel (logique métier)
   - Documenter l'interface entre les deux
2. **Créer un contrat** :
   - gRPC entre Go et Python
   - Protobuf dans `proto/`
3. **Décommissionner** `core/main.py` (doublon de `bootstrap.py`)

### Décision requise

**À trancher par** : Architecture Team + CTO  
**Deadline** : 2026-08-02  
**Décision** : _En attente_

### Statut

- [x] **Identifié** (2026-07-19)
- [ ] **Analysé** (usage, performances, faisabilité)
- [ ] **Décidé** (A, B, ou C)
- [ ] **Implémenté**
- [ ] **Documenté**

---

## P3-2 : Décider du sort de `jarvis-OS/`

**Fichier concerné** : `jarvis-OS/` (racine)

### Problème

Dossier `jarvis-OS/` présent à la racine du projet ETHAN. Nature inconnue.

### Actions d'investigation

```bash
# Vérifier le contenu
ls -la jarvis-OS/

# Vérifier les imports
grep -r "jarvis" core/ plugins/ interfaces/ || echo "Aucun import"

# Vérifier l'historique git
git log --oneline -- jarvis-OS/ | head -20

# Vérifier la documentation
find jarvis-OS/ -name "*.md" -o -name "README*"
```

### Options

#### Option A : Ancien projet (legacy)

**Actions** :
- Supprimer le dossier
- Nettoyer les références dans la documentation

#### Option B : Projet lié (évolution)

**Actions** :
- Documenter la relation ETHAN ↔ Jarvis OS
- Déplacer vers `examples/` ou `legacy/`
- Ajouter un README explicatif

#### Option C : Projet séparé (monorepo)

**Actions** :
- Documenter la séparation
- Ajouter un README dans `jarvis-OS/`
- Clarifier les dépendances

### Décision requise

**À trancher par** : Architecture Team  
**Deadline** : 2026-08-02  
**Décision** : _En attente_

### Statut

- [x] **Identifié** (2026-07-19)
- [ ] **Analysé** (contenu, historique, usage)
- [ ] **Décidé** (A, B, ou C)
- [ ] **Implémenté**
- [ ] **Documenté**

---

## P3-3 : Ajouter des traces OpenTelemetry

**Fichier concerné** : `core/telemetry/`, `interfaces/api/`

### Problème

Pas de tracing distribué pour suivre les événements à travers les modules.

### Solution

#### P3-3.1 : Ajouter OpenTelemetry dans `core/`

```python
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Initialiser le tracing
trace.set_tracer_provider(TracerProvider(resource=Resource.create({
    "service.name": "ethan-core"
})))

# Exporter vers Jaeger
jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=14268,
)
trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(jaeger_exporter))

# Utilisation dans les modules
tracer = trace.get_tracer(__name__)

async def process_event(event):
    with tracer.start_as_current_span("process_event") as span:
        span.set_attribute("event.type", event.type)
        span.set_attribute("event.source", event.source)
        # Traiter l'événement
```

#### P3-3.2 : Ajouter OpenTelemetry dans `interfaces/api/main.py`

```python
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

app = FastAPI()
FastAPIInstrumentor.instrument_app(app)
```

#### P3-3.3 : Ajouter Jaeger dans `docker-compose.yml`

```yaml
jaeger:
  image: jaegertracing/all-in-one:latest
  ports:
    - "16686:16686"  # UI
    - "14268:14268"  # Collector
  networks:
    - ethan-core
```

#### P3-3.4 : Créer `infrastructure/jaeger/jaeger.yml`

```yaml
# Configuration Jaeger
```

### Validation

```bash
# Vérifier les traces
curl -f http://localhost:16686/api/traces

# Ouvrir Jaeger UI
open http://localhost:16686
```

### Impact

- **Avant** : Pas de visibilité sur les flux
- **Après** : Traces complètes, debugging facilité

### Statut

- [x] **Identifié** (2026-07-19)
- [ ] **Implémenté**
- [ ] **Testé**
- [ ] **Documenté**

---

## P3-4 : Améliorer l'observabilité avec Grafana

**Fichier concerné** : `infrastructure/grafana/`

### Problème

Pas de dashboard visuel pour monitorer le système.

### Solution

#### P3-4.1 : Créer un dashboard Grafana

**Fichier** : `infrastructure/grafana/dashboards/ethan-dashboard.json`

```json
{
  "dashboard": {
    "title": "ETHAN System",
    "panels": [
      {
        "title": "Events processed/sec",
        "targets": [
          {
            "expr": "rate(ethan_events_total[1m])"
          }
        ]
      },
      {
        "title": "Active modules",
        "targets": [
          {
            "expr": "ethan_modules_active"
          }
        ]
      },
      {
        "title": "NATS queue size",
        "targets": [
          {
            "expr": "ethan_nats_queue_size"
          }
        ]
      }
    ]
  }
}
```

#### P3-4.2 : Ajouter Grafana dans `docker-compose.yml`

```yaml
grafana:
  image: grafana/grafana:latest
  ports:
    - "3001:3000"
  volumes:
    - grafana_data:/var/lib/grafana
    - ./infrastructure/grafana/dashboards:/etc/grafana/provisioning/dashboards
    - ./infrastructure/grafana/datasources:/etc/grafana/provisioning/datasources
  networks:
    - ethan-core
  depends_on:
    - prometheus
```

#### P3-4.3 : Créer les datasources

**Fichier** : `infrastructure/grafana/datasources/prometheus.yml`

```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
```

### Validation

```bash
# Ouvrir Grafana
open http://localhost:3001

# Login par défaut : admin/admin
```

### Impact

- **Avant** : Pas de visualisation
- **Après** : Dashboard temps réel

### Statut

- [x] **Identifié** (2026-07-19)
- [ ] **Implémenté**
- [ ] **Testé**
- [ ] **Documenté**

---

## P3-5 : CI/CD avec vérification automatique

**Fichier concerné** : `.github/workflows/`, `Makefile`

### Problème

Pas de pipeline CI/CD pour :
- Vérifier les imports
- Exécuter les tests
- Vérifier le linting
- Détecter les dépendances circulaires

### Solution

#### P3-5.1 : Créer `.github/workflows/ci.yml`

```yaml
name: CI
on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install Ruff
        run: pip install ruff
      - name: Lint
        run: ruff check core/ interfaces/ plugins/

  test-imports:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start services
        run: ./ethan up
      - name: Test imports
        run: pytest tests/test_imports.py -v
      - name: Stop services
        run: ./ethan down

  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start services
        run: ./ethan up
      - name: Run tests
        run: pytest tests/ -v --cov=core
      - name: Upload coverage
        uses: codecov/codecov-action@v3
      - name: Stop services
        run: ./ethan down

  docker-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build API
        run: docker compose build api
      - name: Build Kernel
        run: docker compose build kernel
      - name: Build UI
        run: docker compose build ui
```

#### P3-5.2 : Ajouter des cibles Makefile

```makefile
.PHONY: ci
ci: lint test-integration docker-build
	@echo "✅ CI passed"

.PHONY: lint
lint:
	ruff check core/ interfaces/ plugins/

.PHONY: test-imports
test-imports:
	pytest tests/test_imports.py -v

.PHONY: test-integration
test-integration:
	./ethan up
	pytest tests/ -v
	./ethan down
```

### Validation

```bash
# Lancer la CI localement
make ci

# Ou étape par étape
make lint
make test-imports
make test-integration
```

### Impact

- **Avant** : Pas de vérification automatique
- **Après** : CI complète

### Statut

- [x] **Identifié** (2026-07-19)
- [ ] **Implémenté**
- [ ] **Testé**
- [ ] **Documenté**

---

## Résumé P3

| ID | Action | Priorité | Fichier | Statut |
|----|--------|----------|---------|--------|
| P3-1 | Clarifier Go vs Python | **P3** | `core/` | ⏳ En attente de décision |
| P3-2 | Décider du sort de `jarvis-OS/` | **P3** | `jarvis-OS/` | ⏳ En attente d'analyse |
| P3-3 | Ajouter OpenTelemetry | **P3** | `core/telemetry/` | ⏳ En attente |
| P3-4 | Ajouter Grafana | **P3** | `infrastructure/grafana/` | ⏳ En attente |
| P3-5 | CI/CD complet | **P3** | `.github/workflows/` | ⏳ En attente |

### Actions immédiates

1. **Analyser** la dualité Go/Python dans Core
2. **Décider** de la stratégie (A, B, ou C)
3. **Analyser** `jarvis-OS/`
4. **Ajouter** OpenTelemetry et Jaeger
5. **Créer** le dashboard Grafana
6. **Mettre en place** la CI/CD

---

## Notes

- P3 est à long terme (3-6 mois)
- Nécessite des décisions architecturales importantes
- Requiert des ressources supplémentaires (Jaeger, Grafana, Prometheus)
- Impacte l'ensemble de l'équipe

**Dernière mise à jour** : 2026-07-19