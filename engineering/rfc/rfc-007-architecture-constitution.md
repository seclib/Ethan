# RFC-007 — Application de la Constitution Architecturale

## Statut

- **Statut**: Proposé
- **Date**: 2025-06-22
- **Auteur**: Principal Architect

---

## 1. Objectif

Traduire les 12 principes de la Constitution Architecturale en règles techniques vérifiables, patterns d'implémentation et contraintes de conception.

---

## 2. Règles techniques par principe

### Principe 2 — Core ne dépend jamais des technologies

**Règle**: Aucun module dans `core/` ne doit importer directement :
- `redis`, `aioredis`
- `asyncpg`, `psycopg2`, `sqlalchemy`
- `qdrant_client`
- `httpx`, `aiohttp`, `requests`
- `docker`, `kubernetes`

**Pattern**: Port & Adapter

```python
# ✅ Core — ne connaît que l'interface
from core.memory.provider import MemoryProvider

# ❌ Interdit
from qdrant_client import AsyncQdrantClient
```

**Vérification**: `grep -r "import redis\|import asyncpg\|import qdrant\|import httpx" core/`

---

### Principe 3 — Séparation stricte des responsabilités

**Règle**: Les domaines sont isolés. Les dépendances entre domaines sont unidirectionnelles :

```
Core → Memory (via MemoryManager)
Core → Knowledge (via KnowledgeBase)
Core → Capabilities (via CapabilityRegistry)
Core → Providers (via Provider interface)
```

**Interdit**:
- Memory → Core
- Capabilities → Memory (direct)
- Providers → Core

**Pattern**: Chaque domaine expose une interface publique dans `__init__.py`. Les autres domaines n'importent que depuis `__init__.py`.

---

### Principe 4 — Abstraction

**Règle**: Toute technologie externe doit avoir :
1. Une interface abstraite (Port) dans le domaine
2. Une ou plusieurs implémentations (Adapter) dans un sous-package `providers/` ou `adapters/`

**Structure**:
```
core/memory/
├── provider.py          # Port (ABC)
├── manager.py           # Orchestrateur
└── providers/
    ├── redis.py         # Adapter Redis
    ├── postgres.py      # Adapter PostgreSQL
    └── qdrant.py        # Adapter Qdrant
```

---

### Principe 5 — Orchestration

**Règle**: Tout flux suit le cycle :

```python
class OrchestrationStep(Enum):
    PERCEPTION = "perception"
    ANALYSIS = "analysis"
    PLANNING = "planning"
    EXECUTION = "execution"
    OBSERVATION = "observation"
    MEMORY = "memory"
```

Le Core ne doit contenir que des décisions. L'exécution est déléguée aux Capabilities.

---

### Principe 6 — Event-driven

**Règle**: Aucun composant ne doit appeler un autre composant directement. Toute communication passe par le bus d'événements.

**Pattern**:
```python
# ✅
await self.bus.publish("capability:execute", {"name": "search", "args": {...}})

# ❌ Interdit
result = await search_capability.execute(...)
```

**Contrat d'événements** — tous les événements du système :

| Domaine | Événement | Payload | Destinataire |
|---------|-----------|---------|--------------|
| Core | `user:input` | `{content, session_id}` | Planner |
| Core | `planner:decision` | `{plan, steps}` | Executor |
| Capabilities | `capability:execute` | `{name, args, context}` | CapabilityRegistry |
| Capabilities | `capability:result` | `{name, result, status}` | Observer |
| Memory | `memory:store` | `{content, memory_type}` | MemoryManager |
| Memory | `memory:retrieve` | `{query, memory_type}` | MemoryManager |
| Providers | `provider:reason` | `{prompt, model}` | Provider |
| Providers | `provider:response` | `{response, model}` | Core |

---

### Principe 7 — Capability Model

**Règle**: Toute action est une Capability. Interface :

```python
class Capability(ABC):
    name: str
    description: str
    version: str

    @abstractmethod
    async def validate(self, context: Context) -> bool:
        """Valide que la capability peut être exécutée dans ce contexte."""
        pass

    @abstractmethod
    async def execute(self, context: Context) -> Result:
        """Exécute l'action. Retourne un résultat."""
        pass

    @abstractmethod
    async def observe(self, result: Result) -> Observation:
        """Analyse le résultat et produit une observation."""
        pass
```

**Règles**:
- Une Capability ne connaît pas le Core
- Une Capability ne connaît pas les autres Capabilities
- Une Capability est testable isolément
- Une Capability peut être remplacée sans modifier le Core

---

### Principe 8 — Provider Model

**Règle**: Les modèles IA sont interchangeables via une interface unique :

```python
class ReasoningProvider(ABC):
    @abstractmethod
    async def reason(self, prompt: str, context: Context) -> Response:
        """Capacité de raisonnement. Peut être Ollama, OpenAI, Anthropic, etc."""
        pass

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Capacité d'embedding."""
        pass
```

Le Core ne connaît que `ReasoningProvider`. Il ne connaît pas Ollama, OpenAI ou Anthropic.

---

### Principe 9 — Memory Principle

**Règle**: La mémoire est un système de cognition, pas un stockage. Déjà formalisé dans RFC-006.

**Vérification**:
- Aucun composant hors de `core/memory/` n'importe `redis`, `asyncpg` ou `qdrant_client`
- Toute opération mémoire passe par `MemoryManager`
- Les MemoryProviders sont interchangeables via configuration

---

### Principe 10 — Evolution

**Règle**: Le système doit être extensible sans modification du Core.

**Mécanismes**:
- Plugin system (existant dans `core/plugins.py`)
- Provider Registry (RFC-006)
- Capability Registry (à implémenter)
- Event bus (existant dans `core/events/`)

---

### Principe 11 — Safety

**Règle**: Aucune action sans validation, contexte et traçabilité.

```python
@dataclass
class SafetyContext:
    validated: bool
    user_id: str
    session_id: str
    trace_id: str
    permissions: List[str]
    risk_level: RiskLevel

class SafeCapability(Capability):
    async def execute(self, context: Context) -> Result:
        if not context.safety.validated:
            raise SafetyViolation("Action non validée")
        # ... exécution
```

---

## 3. Architecture cible

```
┌─────────────────────────────────────────────────────────┐
│                        Core                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ Planner  │ │ Executor │ │ Observer │ │ Memory   │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘  │
│       │            │            │            │         │
│       └────────────┴────────────┴────────────┘         │
│                        │                                │
│              ┌─────────┴─────────┐                      │
│              │    Event Bus      │                      │
│              └─────────┬─────────┘                      │
└────────────────────────┼────────────────────────────────┘
                         │
    ┌────────────────────┼────────────────────┐
    │                    │                    │
    ▼                    ▼                    ▼
┌──────────┐     ┌──────────────┐     ┌──────────────┐
│Capability│     │MemoryManager │     │   Provider   │
│ Registry │     │  (RFC-006)   │     │   Registry   │
└────┬─────┘     └──────┬───────┘     └──────┬───────┘
     │                  │                    │
     ▼                  ▼                    ▼
┌──────────┐     ┌──────────────┐     ┌──────────────┐
│ Cap. 1   │     │  Redis Prov. │     │  Ollama      │
│ Cap. 2   │     │  PG Prov.    │     │  OpenAI      │
│ Cap. 3   │     │  Qdrant Prov.│     │  Anthropic   │
└──────────┘     └──────────────┘     └──────────────┘
```

---

## 4. Règles de linting à implémenter

```python
# Règles à vérifier dans CI/CD
RULES = {
    "C001": "core/ ne doit pas importer de technologies externes",
    "C002": "Les domaines ne doivent pas s'importer directement",
    "C003": "Toute technologie externe doit avoir un Port et un Adapter",
    "C004": "Les composants communiquent uniquement via le bus d'événements",
    "C005": "Toute action est une Capability",
    "C006": "Les providers IA sont interchangeables",
    "C007": "La mémoire est gérée uniquement par MemoryManager",
    "C008": "Aucune action sans validation Safety",
}
```

---

## 5. Plan d'implémentation

| Phase | Description | Dépend de |
|-------|-------------|-----------|
| 1 | Audit des violations actuelles | — |
| 2 | Refactoring Core → Ports & Adapters | Phase 1 |
| 3 | Implémentation Capability Registry | Phase 2 |
| 4 | Migration vers event-driven pur | Phase 2 |
| 5 | Implémentation Safety | Phase 3 |
| 6 | CI/CD linting rules | Phase 1 |