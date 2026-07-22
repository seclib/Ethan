# Audit Architecture — Kernel & Core d'ETHAN

**Type** : Audit architecture approfondi  
**Auteur** : Distinguished Software Architect  
**Date** : 21/07/2026  
**Version** : 1.0  
**Destinataire** : Revue CTO

---

## 1. Vue d'ensemble

Le noyau d'ETHAN (`core/` et `core/kernel.py`) constitue le **cœur du système**. Il orchestre la communication inter-modules via un event bus et gère l'état persistant.

---

## 2. Responsabilités du Kernel

### 2.1 CognitiveKernel (`core/kernel.py`)

| Responsabilité | Implémentation | Score |
|--------------|------------|-------|
| Orchestration d'événements | `dispatch_event()` lignes 125-152 | ✓ |
| Gestion des modules | `register_module()` lignes 109-123 | ⚠️ |
| Cycle de vie | `start()`/`stop()` lignes 49-107 | ⚠️ |
| Sync état événements | `_sync_state()` lignes 207-218 | ❌ |
| Gestion des objectifs | `_on_goal_event()` lignes 173-189 | ⚠️ |

**Verdict** : Le Kernel agit comme **orchestrateur mais avec des fuites de logique métier**.

---

## 3. Responsabilités du Core

### 3.1 Sous-systèmes

```
core/
├── bootstrap.py          # Point d'entrée - compose tout le système
├── kernel.py             # Orchestration centrale
├── bus/                  # Event bus abstrait (ABC + NATS)
├── state/                # RedisLiveState + PostgresPersistentState
├── modules/              # Modules cognitifs (ABC)
├── scheduler/            # Planification des tâches
├── registry/             # Registry des modules
├── learning/             # Moteur d'apprentissage
├── metacognition/        # Moteur de métacognition
├── autonomy/             # Boucle d'autonomie
├── goals/                # Gestion des objectifs
└── safety/               # RBAC + sécurité
```

---

## 4. Violations de Clean Architecture

### 4.1 Violation #1 : Kernel connaît les implémentations

**Fichier** : `core/kernel.py` (lignes 9-18)

```python
from core.autonomy.controller import AutonomyLoopController
from core.bus.interface import EventBus
from core.goals.manager import GoalManager
from core.learning.engine import LearningEngine
from core.metacognition.engine import MetaCognitionEngine
from core.registry.module import ModuleRegistry
from core.scheduler.scheduler import Scheduler
from core.state.postgres_state import PostgresPersistentState
from core.state.redis_state import RedisLiveState
```

**Problème** : Le Kernel importe `PostgresPersistentState` et `RedisLiveState` au lieu d'une interface `StateBackend`.

### 4.2 Violation #2 : Bootstrap compose tout

**Fichier** : `core/bootstrap.py` (lignes 18-40)

Le bootstrap connaît l'ensemble des classes concrètes, créant un **God Object compositionnel**.

### 4.3 Violation #3 : Modules built-in hardcodés

**Fichier** : `core/kernel.py` (lignes 157-168)

```python
builtins = [
    ("module-executive", ["handle.intent"]),
    ("module-planner", ["handle.task"]),
    ("module-memory", ["store.event"]),
    ("module-reflective", ["handle.completion"]),
]
```

---

## 5. Dépendances et Couplage

### 5.1 Imports directs Kernel

| Import | Direction | Problème |
|--------|----------|--------|
| `PostgresPersistentState` | Core → Kernel | ❌ Implémentation connue |
| `RedisLiveState` | Core → Kernel | ❌ Implémentation connue |
| `LearningEngine` | Core → Kernel | ⚠️ Optionnel mais chargé |

### 5.2 Points de couplage critiques

1. **State sync dans Kernel** (lignes 217-218) :
```python
await self.redis.set(f"event:{event.id}", payload, ttl=3600)
await self.pg.insert("events", payload)
```

2. **Pattern hardcodé pour modules** :
```python
builtins = [("module-executive", ["handle.intent"]), ...]
```

3. **Bus interface bien conçu** (correct) :
```python
class EventBus(ABC):
    async def publish(self, subject: str, event: Event) -> None:
    async def subscribe(self, pattern: str, handler: EventHandler) -> Subscription:
```

---

## 6. Interfaces publiques

### 6.1 EventBus (bonne abstraction)

```python
class EventBus(ABC):
    """Bus d'événements abstrait - interchangeability garantie."""
    
    @abstractmethod
    async def publish(self, subject: str, event: Event) -> None:
    @abstractmethod
    async def subscribe(self, pattern: str, handler: EventHandler) -> Subscription:
    @abstractmethod
    async def close(self) -> None:
```

### 6.2 State (à améliorer)

```python
# Redis
def set(self, key: str, value: Any, ttl: int | None = None) -> None
def get(self, key: str) -> Any

# PostgreSQL
async def insert(self, table: str, payload: dict) -> None
```

**Manque** : Interface `StateBackend` unifiée.

---

## 7. Gestion des erreurs

### 7.1 Actuelle

```python
# core/kernel.py (lignes 146-152)
except Exception as e:
    logger.error("Dispatch failed for %s: %s", event.id, e, exc_info=True)
    await self.bus.publish("system.error", Event(...))
```

### 7.2 Points faibles

- Pas de retry explicite sur les opérations DB
- Pas de dead letter queue pour les événements échoués
- Pas de fallback ou circuit breaker

---

## 8. Cycle de vie

### 8.1 Initialisation

```python
# core/bootstrap.py
async def main():
    bus = NatsEventBus()
    redis = RedisLiveState(redis_url)
    pg = PostgresPersistentState(database_url)
    
    await bus.connect(nats_url)   # Retry intégré (lignes 71-80)
    await redis.connect()
    await pg.connect()
    
    kernel = CognitiveKernel(...)
    await kernel.start()
```

### 8.2 Arrêt

```python
# core/kernel.py (lignes 83-107)
async def stop(self):
    self._running = False
    # Arrêt des sous-systèmes optionnels
    for sub in [self.learning, self.metacognition, self.autonomy]:
        if sub: await sub.stop()
    await self.scheduler.stop()
    await self.bus.close()
    await self.redis.close()
    await self.pg.close()
```

---

## 9. Concurrence et Performance

### 9.1 Modèle actuel

- **asyncio** pour la concurrence
- **Pas de pool de workers** explicite
- **Dispatch sérielisé** dans `_sync_state()`

### 9.2 Métriques d'observabilité

- `time.monotonic()` pour le timing (ligne 130)
- Logs structurés via `logger`
- Manque : métriques Prometheus intégrées

---

## 10. Robustesse

### 10.1 Points forts

| Composant | Robustesse |
|-----------|----------|
| NATS connection | ✅ Retry 10x avec backoff 2-10s |
| Docker restart | ✅ `restart: unless-stopped` |
| Healthchecks | ✅ NATS, Redis, PostgreSQL, API |

### 10.2 Points faibles

| Composant | Problème |
|-----------|----------|
| LLM providers | ❌ Pas de circuit breaker |
| DB operations | ❌ Pas de retry automatique |
| Event dispatch | ❌ Pas de DLQ |

---

## 11. Verdict

### Score global : **7/10**

| Critère | Score | Commentaire |
|--------|-------|-------------|
| Séparation responsabilités | 6/10 | Kernel avec logique métier intégrée |
| Clean Architecture | 5/10 | Violations de dépendances |
| Extensibilité | 8/10 | Modules ABC bien conçus |
| Testabilité | 5/10 | Couplage fort |
| Observabilité | 6/10 | Logs OK, métriques basiques |
| Résilience | 6/10 | Retry OK, manque circuit breaker |

---

## 12. Recommandations CTO

### 12.1 Priorité immédiate

1. **Créer `StateBackend` interface** - Unifier Redis/PostgreSQL
2. **Externaliser l'injection** - Conteneur DI au lieu de bootstrap hardcodé
3. **Circuit breaker** - Implémenter dans `core/safety/circuit_breaker.py`

### 12.2 Priorité moyenne

4. **Event store séparé** - Sortir `_sync_state` du Kernel
5. **Configuration dynamique** - Modules via config YAML
6. **Métriques Prometheus** - Intégrer dans EventBus

### 12.3 Priorité long terme

7. **Multi-worker dispatch** - Paralléliser les événements
8. **Dead letter queue** - Pour les événements échoués
9. **Healthcheck state** - Endpoint `/health/state`