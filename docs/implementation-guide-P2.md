# Guide d'Implémentation P2 — Améliorations

**Objectif** : Améliorer la qualité du code, ajouter les tests, moderniser les imports  
**Date** : 2026-07-19  
**Priorité** : P2 (Moyen terme)  
**Temps estimé** : 2-3 jours  
**Responsable** : Équipe Core + DevOps

---

## Vue d'ensemble des actions P2

```
┌─────────────────────────────────────────────────────────────┐
│                  Actions P2 à implémenter                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ⏳ P2-1 : Installer le package en mode éditable           │
│     ├─ Fichier : pyproject.toml                            │
│     ├─ Action : pip install -e .                           │
│     └─ Impact : Supprimer sys.path hacking                 │
│                                                             │
│  ⏳ P2-2 : Ajouter des tests d'intégration                 │
│     ├─ Fichier : tests/                                    │
│     ├─ Action : Créer test_healthchecks.py, test_imports.py│
│     └─ Impact : Qualité et fiabilité                       │
│                                                             │
│  ⏳ P2-3 : Ajouter des métriques Prometheus                 │
│     ├─ Fichier : infrastructure/prometheus/                │
│     ├─ Action : Endpoint /metrics, dashboard               │
│     └─ Impact : Observabilité                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## P2-1 : Installer le package en mode éditable

**Fichier concerné** : `pyproject.toml`  
**Deadline** : 2026-08-02  
**Responsable** : Équipe DevOps  
**Temps estimé** : 1-2h

---

### Problème

Les interfaces utilisent `sys.path.insert()` pour importer `core`, ce qui contredit le principe d'isolation.

```python
# interfaces/api/main.py (ligne 13)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

### Solution

Installer le package en mode éditable pour que les imports fonctionnent naturellement.

---

### Procédure

#### Étape 1 : Vérifier pyproject.toml

```bash
# Vérifier que le fichier existe
ls -la pyproject.toml

# Vérifier les dépendances
grep -A 10 "dependencies" pyproject.toml
```

#### Étape 2 : Installer en mode éditable

```bash
# Installer avec les dépendances serveur et dev
pip install -e ".[server,dev]"

# Vérifier l'installation
pip show ethan
```

#### Étape 3 : Tester les imports

```bash
# Tester core
./ethan python3 -c "import core; print('✓ core OK')"

# Tester core.kernel
./ethan python3 -c "from core.kernel import CognitiveKernel; print('✓ kernel OK')"

# Tester sdk
./ethan python3 -c "import sdk.event; print('✓ sdk OK')"

# Tester plugins
./ethan python3 -c "import plugins; print('✓ plugins OK')"
```

#### Étape 4 : Supprimer sys.path.insert() dans interfaces/api/main.py

```bash
# Éditer interfaces/api/main.py
# SUPPRIMER la ligne 13 :
# sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Les imports devraient fonctionner directement
```

#### Étape 5 : Mettre à jour interfaces/api/Dockerfile

```bash
# Éditer deploy/Dockerfile.api
# SUPPRIMER la ligne :
# ENV PYTHONPATH=/app/core:/app/interfaces/api:/app/sdk:/app
```

#### Étape 6 : Tester l'API

```bash
# Démarrer l'API
./ethan api

# Tester dans un autre terminal
curl -f http://localhost:8000/health
curl -f http://localhost:8000/version
```

#### Étape 7 : Commit

```bash
git add -A
git commit -m "feat: install package in editable mode, remove sys.path hacking"
```

---

### Checklist P2-1

- [ ] Vérifier pyproject.toml
- [ ] Installer `pip install -e .[server,dev]`
- [ ] Tester les imports (core, sdk, plugins)
- [ ] Supprimer `sys.path.insert()` dans `interfaces/api/main.py`
- [ ] Mettre à jour `deploy/Dockerfile.api`
- [ ] Tester l'API
- [ ] Commiter

---

## P2-2 : Ajouter des tests d'intégration

**Fichier concerné** : `tests/`  
**Deadline** : 2026-08-02  
**Responsable** : Équipe Core  
**Temps estimé** : 1-2j

---

### Problème

Absence de tests d'intégration pour vérifier :
- Les healthchecks
- Les imports
- La connectivité entre services
- Le démarrage du système

### Solution

Créer une suite de tests d'intégration.

---

### Procédure

#### Étape 1 : Créer tests/test_healthchecks.py

```bash
cat > tests/test_healthchecks.py << 'EOF'
"""Tests de healthchecks pour les services Docker."""
import subprocess
import time
import pytest


def test_docker_compose_running():
    """Test que docker compose est disponible."""
    result = subprocess.run(
        ["docker", "compose", "version"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, "docker compose n'est pas disponible"


def test_services_healthy():
    """Test que tous les services sont healthy."""
    # Attendre le démarrage
    time.sleep(10)
    
    result = subprocess.run(
        ["docker", "compose", "ps", "--services", "--filter", "health=healthy"],
        capture_output=True,
        text=True,
        cwd="/home/fatsio/AI/Ethan"
    )
    
    assert result.returncode == 0, f"Échec: {result.stderr}"
    services = result.stdout.strip().split("\n")
    assert len(services) >= 6, f"Expected at least 6 services, got {len(services)}"


def test_api_health():
    """Test que l'API répond."""
    import requests
    response = requests.get("http://localhost:8000/health", timeout=5)
    assert response.status_code == 200
EOF
```

#### Étape 2 : Créer tests/test_imports.py

```bash
cat > tests/test_imports.py << 'EOF'
"""Tests des imports Python."""
import subprocess


def test_core_import():
    """Test que core peut être importé."""
    result = subprocess.run(
        ["python3", "-c", "import core"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Échec: {result.stderr}"


def test_core_kernel_import():
    """Test que core.kernel peut être importé."""
    result = subprocess.run(
        ["python3", "-c", "from core.kernel import CognitiveKernel"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Échec: {result.stderr}"


def test_sdk_imports():
    """Test que tous les modules SDK peuvent être importés."""
    modules = [
        "import sdk",
        "from sdk.event import EventType",
        "from sdk.autonomy import AutonomySDK",
        "from sdk.learning import LearningSDK",
        "from sdk.module import ModuleSDK",
        "from sdk.goals import GoalsSDK",
        "from sdk.metacognition import MetacognitionSDK",
    ]
    
    for module_import in modules:
        result = subprocess.run(
            ["python3", "-c", module_import],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Échec de '{module_import}': {result.stderr}"


def test_plugins_import():
    """Test que plugins peut être importé."""
    result = subprocess.run(
        ["python3", "-c", "import plugins"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Échec: {result.stderr}"
EOF
```

#### Étape 3 : Créer tests/test_dependencies.py

```bash
cat > tests/test_dependencies.py << 'EOF'
"""Tests des dépendances entre modules."""
import os
import ast


def test_no_circular_dependencies():
    """Détecte les dépendances circulaires dans core/."""
    # TODO: Implémenter avec importlinter
    pass


def test_no_interface_imports_in_core():
    """Vérifie que core/ n'importe pas interfaces/."""
    forbidden = ["from interfaces", "import interfaces"]
    
    for root, dirs, files in os.walk("core"):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                with open(filepath) as f:
                    content = f.read()
                    for forbidden_import in forbidden:
                        assert forbidden_import not in content, \
                            f"Import interdit dans {filepath}: {forbidden_import}"
EOF
```

#### Étape 4 : Créer .github/workflows/tests.yml

```bash
mkdir -p .github/workflows

cat > .github/workflows/tests.yml << 'EOF'
name: Tests

on: [push, pull_request]

jobs:
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
        run: pytest tests/ -v
      - name: Stop services
        run: ./ethan down
EOF
```

#### Étape 5 : Tester les tests

```bash
# Installer pytest si nécessaire
pip install pytest

# Lancer les tests d'imports
pytest tests/test_imports.py -v

# Lancer les tests de healthchecks
pytest tests/test_healthchecks.py -v
```

---

### Checklist P2-2

- [ ] Créer `tests/test_healthchecks.py`
- [ ] Créer `tests/test_imports.py`
- [ ] Créer `tests/test_dependencies.py`
- [ ] Créer `.github/workflows/tests.yml`
- [ ] Installer pytest
- [ ] Tester les imports
- [ ] Tester les healthchecks
- [ ] Commiter

---

## P2-3 : Ajouter des métriques Prometheus

**Fichier concerné** : `infrastructure/prometheus/`  
**Deadline** : 2026-08-02  
**Responsable** : Équipe DevOps  
**Temps estimé** : 1j

---

### Problème

Pas de métriques système pour monitorer :
- Nombre d'événements traités
- Latence des modules
- État de la queue NATS
- Utilisation Redis/PostgreSQL

### Solution

Ajouter Prometheus pour collecter des métriques.

---

### Procédure

#### Étape 1 : Installer prometheus-client

```bash
pip install prometheus-client
```

#### Étape 2 : Créer infrastructure/prometheus/prometheus.yml

```bash
mkdir -p infrastructure/prometheus

cat > infrastructure/prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'ethan-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'ethan-kernel'
    static_configs:
      - targets: ['localhost:8080']
    metrics_path: '/metrics'
    scrape_interval: 5s
EOF
```

#### Étape 3 : Ajouter l'endpoint /metrics dans interfaces/api/main.py

```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Response

# Métriques
events_processed = Counter(
    'ethan_events_total',
    'Total events processed',
    ['module', 'status']
)
event_latency = Histogram(
    'ethan_event_latency_seconds',
    'Event processing latency',
    ['module']
)
modules_active = Gauge(
    'ethan_modules_active',
    'Active modules'
)

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")
```

#### Étape 4 : Ajouter Prometheus dans docker-compose.yml

```yaml
# Ajouter dans docker-compose.yml
prometheus:
  image: prom/prometheus:latest
  ports:
    - "9090:9090"
  volumes:
    - ./infrastructure/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
    - prometheus_data:/prometheus
  networks:
    - ethan-core
  command:
    - '--config.file=/etc/prometheus/prometheus.yml'
    - '--storage.tsdb.path=/prometheus'
```

#### Étape 5 : Tester Prometheus

```bash
# Démarrer les services
./ethan up

# Tester l'endpoint /metrics
curl -f http://localhost:8000/metrics

# Ouvrir Prometheus UI
open http://localhost:9090
```

#### Étape 6 : Commit

```bash
git add -A
git commit -m "feat: add Prometheus metrics for observability"
```

---

### Checklist P2-3

- [ ] Installer `prometheus-client`
- [ ] Créer `infrastructure/prometheus/prometheus.yml`
- [ ] Ajouter endpoint `/metrics` dans `interfaces/api/main.py`
- [ ] Ajouter Prometheus dans `docker-compose.yml`
- [ ] Tester l'endpoint `/metrics`
- [ ] Tester Prometheus UI
- [ ] Commiter

---

## Tests de validation P2

### Test 1 : Package éditable

```bash
# Vérifier que core peut être importé sans sys.path
./ethan python3 -c "import core.kernel; print('✓ OK')"

# Vérifier que l'API fonctionne
./ethan api &
sleep 5
curl -f http://localhost:8000/health
pkill -f "uvicorn api.main"
```

### Test 2 : Tests d'intégration

```bash
# Installer pytest
pip install pytest

# Lancer les tests
pytest tests/ -v
```

### Test 3 : Métriques Prometheus

```bash
# Démarrer les services
./ethan up

# Tester les métriques
curl -f http://localhost:8000/metrics

# Vérifier Prometheus
curl -f http://localhost:9090/metrics
```

---

## Commandes rapides

### Installer le package éditable

```bash
pip install -e ".[server,dev]"
./ethan python3 -c "import core; print('OK')"
```

### Lancer les tests

```bash
pytest tests/ -v
pytest tests/test_imports.py -v
```

### Tester Prometheus

```bash
curl -f http://localhost:8000/metrics
open http://localhost:9090
```

---

## Support

- **Roadmap P2** : `docs/roadmap-P2.md`
- **Roadmap globale** : `docs/roadmap-global.md`
- **Guide P0** : `docs/implementation-guide-P0.md`
- **Guide P1** : `docs/implementation-guide-P1.md`

---

## Prochaines étapes

1. **Équipe DevOps** : Installer package éditable (P2-1)
2. **Équipe Core** : Créer tests d'intégration (P2-2)
3. **Équipe DevOps** : Ajouter Prometheus (P2-3)
4. **Passer à P3** : Optimisations (OpenTelemetry, Grafana, CI/CD)

**Dernière mise à jour** : 2026-07-19