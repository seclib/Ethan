# ADR-1007 — Event-Driven Architecture

> **Statut** : Proposed
> **Date** : 2026-06-23

---

## Context

Le système actuel utilise un modèle synchrone et direct. Pour un système scalable et observable, nous avons besoin de:

- **Découplage** — Composants indépendants
- **Scalabilité** — Traitement asynchrone
- **Observabilité** — Traçabilité des événements
- **Extensibilité** — Ajout de handlers sans modifier le core

Sans events, le système est:
- fortement couplé
- difficile à monitorer
- peu flexible

---

## Decision

Le système doit utiliser une **Event-Driven Architecture**:

> **Event Bus + Event Handlers**

---

## Event Schema

```python
class Event:
    """Événement métier."""
    id: str
    type: str
    source: str
    timestamp: datetime
    data: dict
    metadata: dict

class EventBus:
    """Bus d'événements central."""
    
    async def publish(self, event: Event)
    async def subscribe(self, event_type: str, handler: EventHandler)
    async def unsubscribe(self, event_type: str, handler: EventHandler)

class EventHandler(ABC):
    """Interface pour les handlers d'événements."""
    
    @abstractmethod
    async def handle(self, event: Event) -> None
```

---

## Implementation

### Event Types

```python
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

class EventType(str, Enum):
    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    
    # Capability events
    CAPABILITY_STARTED = "capability.started"
    CAPABILITY_COMPLETED = "capability.completed"
    CAPABILITY_FAILED = "capability.failed"
    
    # Memory events
    MEMORY_STORED = "memory.stored"
    MEMORY_RETRIEVED = "memory.retrieved"
    
    # Agent events
    AGENT_CREATED = "agent.created"
    AGENT_DESTROYED = "agent.destroyed"
    
    # User events
    USER_INPUT_RECEIVED = "user.input.received"
    USER_RESPONSE_GENERATED = "user.response.generated"

@dataclass
class Event:
    id: str
    type: EventType
    source: str
    timestamp: datetime
    data: dict
    metadata: dict
```

### Event Bus

```python
class EventBus:
    """Central event bus for async communication."""
    
    def __init__(self):
        self._handlers: Dict[EventType, List[EventHandler]] = {}
        self._history: List[Event] = []
    
    async def publish(self, event: Event):
        """Publish event to all subscribers."""
        self._history.append(event)
        
        handlers = self._handlers.get(event.type, [])
        tasks = [handler.handle(event) for handler in handlers]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def subscribe(self, event_type: EventType, handler: EventHandler):
        """Subscribe handler to event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    async def unsubscribe(self, event_type: EventType, handler: EventHandler):
        """Unsubscribe handler from event type."""
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)
```

### Event Handlers

```python
class EventHandler(ABC):
    """Abstract event handler."""
    
    @abstractmethod
    async def handle(self, event: Event) -> None:
        pass

class LoggingEventHandler(EventHandler):
    """Log all events."""
    async def handle(self, event: Event):
        logger.info(f"Event: {event.type} from {event.source}")

class MetricsEventHandler(EventHandler):
    """Collect metrics from events."""
    async def handle(self, event: Event):
        metrics.increment(f"events.{event.type}")

class AuditEventHandler(EventHandler):
    """Audit trail for compliance."""
    async def handle(self, event: Event):
        audit_log.store(event)
```

---

## Consequences

* **Decoupling** — Composants communiquent via events, pas directement
* **Scalability** — Traitement asynchrone, non-bloquant
* **Observability** — Tous les événements sont tracés
* **Extensibility** — Nouveaux handlers sans modifier le core
* **Testability** — Handlers testables indépendamment

---

## Compliance

* Toute communication inter-composants utilise EventBus
* Les events sont immutables et tracés
* Les handlers sont des plugins (dans plugins/)

## References

* [Constitution Architecturale](/engineering/architecture/constitution.md) — Principe 4 (Event-Driven)
* [ADR-1004](/engineering/adr/ADR-1004-cognitive-loop-architecture.md) — Cognitive Loop
* [ADR-1006](/engineering/adr/ADR-1006-capability-composition-pattern.md) — Capability Composition