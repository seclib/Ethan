# Roadmap P2 — Améliorations (Moyen terme)

**Objectif** : Améliorer la qualité du code, ajouter les tests, moderniser les imports  
**Date de création** : 2026-07-19  
**Statut** : En attente d'implémentation  
**Propriétaire** : Équipe Core + DevOps

---

## P2-1 : Installer le package en mode éditable

**Fichier concerné** : `pyproject.toml`  
**Impact** : Toutes les commandes Python

### Problème

Les interfaces utilisent `sys.path.insert()` pour importer `core`, ce qui contredit le principe d'isolation.

### Solution

```bash
# Installer en mode éditable
cd /home/fatsio/AI/Ethan
pip install -e .

# Vérifier
python3 -c "import core.kernel; print('OK')"
```

### Actions

1. **Vérifier les dépendances**
   ```bash
   pip install -e ".[server,dev]"
   ```

2. **Supprimer `sys.path.insert()` dans `interfaces/api/main.py`**
   ```python
   # SUPPRIMER cette ligne
   # sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
   
   # Les imports devraient fonctionner directement
   from api.routers import message as message_router
   ```

3. **Mettre à jour `interfaces/api/Dockerfile`**
   ```dockerfile
   # SUPPRIMER cette ligne
   # ENV PYTHONPATH=/app/core:/app/interfaces/api:/app/sdk:/app
   ```

4. **Vérifier tous les imports**
   ```bash
   python3 -c "import core.kernel"
   python3 -c "import sdk.event"
   python3 -c "import plugins"
   ```

### Validation

```bash
# Tester tous les imports
python3 -c "import core"
python3 -c "import core.kernel"
python3 -c "import sdk"
python3 -c "import plugins"

# Tester l'API
./ethan api
curl -f http://localhost:8000/health
```

### Impact

- **Avant** : `sys.path.insert()` dans chaque fichier
- **Après** : Imports standards Python

### Statut

- [x] **Identifié** (2026-07-19)
- [ ] **Implémenté**
- [ ] **Testé**
- [ ] **Documenté**

---

## P2-2 : Ajouter des tests d'intégration

**Fichier concerné** : `tests/`, `core/tests/`

### Problème

Absence de tests d'intégration pour vérifier :
- Les healthchecks
- Les imports
- La connectivité entre services
- Le démarrage du système

### Actions

#### P2-2.1 : Créer `tests/test_healthchecks.py`

```python
import subprocess
import time

def test_docker_compose_up():
    """Test que docker compose up fonctionne."""
    result = subprocess.run(
        ["docker", "compose", "up", "-d"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Échec: {result.stderr}"

def test_services_healthy():
    """Test que tous les services sont healthy."""
    time.sleep(10)  # Attendre le démarrage
    result = subprocess.run(
        ["docker", "compose", "ps", "--services", "--filter", "health=healthy"],
        capture_output=True,
        text=True
    )
    services = result.stdout.strip().split("\n")
    assert len(services) == 7, f"Expected 7 services, got {len(services)}"

def test_api_health():
    """Test que l'API répond."""
    import requests
    response = requests.get("http://localhost:8000/health")
    assert response.status_code == 200
```

#### P2-2.2 : Créer `tests/test_imports.py`

```python
def test_core_import():
    import core
    assert hasattr(core, '__version__')

def test_core_kernel_import():
    from core.kernel import CognitiveKernel
    assert CognitiveKernel is not None

def test_sdk_import():
    import sdk
    from sdk.event import EventType
    from sdk.autonomy import AutonomySDK
    from sdk.learning import LearningSDK
    from sdk.module import ModuleSDK
    from sdk.goals import GoalsSDK
    from sdk.metacognition import MetacognitionSDK

def test_plugins_import():
    import plugins
    from plugins.loader import PluginLoader
```

#### P2-2.3 : Créer `tests/test_dependencies.py`

```python
import ast
import os

def test_no_circular_dependencies():
    """Détecte les dépendances circulaires dans core/."""
    # Utiliser importlinter ou un outil similaire
    pass

def test_no_interface_imports_in_core():
    """Vérifie que core/ n'importe pas interfaces/."""
    for root, dirs, files in os.walk("core"):
        for file in files:
            if file.endswith(".py"):
                with open(os.path.join(root, file)) as f:
                    content = f.read()
                    assert "from interfaces" not in content
                    assert "import interfaces" not in content
```

### Intégration CI/CD

```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start Docker Compose
        run: ./ethan up
      - name: Run tests
        run: pytest tests/ -v
      - name: Stop Docker Compose
        run: ./ethan down
```

### Validation

```bash
# Exécuter les tests
pytest tests/ -v

# Vérifier la couverture
pytest tests/ --cov=core --cov=interfaces --cov=plugins
```

### Impact

- **Avant** : Aucun test automatisé
- **Après** : Tests d'intégration complets

### Statut

- [x] **Identifié** (2026-07-19)
- [ ] **Implémenté**
- [ ] **Testé**
- [ ] **Intégré dans CI/CD**

---

## P2-3 : Ajouter des métriques Prometheus

**Fichier concerné** : `core/telemetry/`, `infrastructure/prometheus/`

### Problème

Pas de métriques système pour monitorer :
- Nombre d'événements traités
- Latence des modules
- État de la queue NATS
- Utilisation Redis/PostgreSQL

### Solution

#### P2-3.1 : Ajouter le endpoint Prometheus dans `interfaces/api/main.py`

```python
from prometheus_client import Counter, Histogram, Gauge
from fastapi import Response

# Métriques
events_processed = Counter('ethan_events_total', 'Total events processed', ['module', 'status'])
event_latency = Histogram('ethan_event_latency_seconds', 'Event processing latency', ['module'])
modules_active = Gauge('ethan_modules_active', 'Active modules')
nats_queue_size = Gauge('ethan_nats_queue_size', 'NATS queue size')

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")
```

#### P2-3.2 : Créer `infrastructure/prometheus/prometheus.yml`

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ethan-api'
    static_configs:
      - targets: ['localhost:8000']
  - job_name: 'ethan-kernel'
    static_configs:
      - targets: ['localhost:8080']
```

#### P2-3.3 : Ajouter Prometheus dans `docker-compose.yml`

```yaml
prometheus:
  image: prom/prometheus:latest
  ports:
    - "9090:9090"
  volumes:
    - ./infrastructure/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
    - prometheus_data:/prometheus
  networks:
    - ethan-core
```

### Validation

```bash
# Vérifier les métriques
curl -f http://localhost:9090/metrics

# Ouvrir Prometheus UI
open http://localhost:9090
```

### Impact

- **Avant** : Pas de monitoring
- **Après** : Métriques complètes, dashboarding possible

### Statut

- [x] **Identifié** (2026-07-19)
- [ ] **Implémenté**
- [ ] **Testé**
- [ ] **Documenté**

---

## Résumé P2

| ID | Action | Priorité | Fichier | Statut |
|----|--------|----------|---------|--------|
| P2-1 | Installer package en mode éditable | **P2** | `pyproject.toml` | ⏳ En attente |
| P2-2 | Ajouter tests d'intégration | **P2** | `tests/` | ⏳ En attente |
| P2-3 | Ajouter métriques Prometheus | **P2** | `core/telemetry/` | ⏳ En attente |

### Actions immédiates

1. **Installer** le package en mode éditable
2. **Créer** les tests d'intégration de base
3. **Ajouter** Prometheus au stack
4. **Intégrer** les tests dans CI/CD

---

## Notes

- P2 améliore la qualité et la maintenabilité
- Nécessite l'accord de l'équipe pour les tests
- Prometheus nécessite des ressources supplémentaires

**Dernière mise à jour** : 2026-07-19