# ADR-1002 — Planner / Executor Separation

> **Statut** : Accepted
> **Date** : 2026-06-22

---

## Context

Complex tasks require decomposition.

A monolithic executor mixes planning and execution, making the system:
- harder to debug
- harder to scale
- harder to test

---

## Decision

Ethan Core is split into two logical components:

### 1. Planner

* breaks down goals into steps
* defines strategy
* selects capabilities

### 2. Executor Controller

* sends tasks to Capability Router
* monitors execution
* handles failures

---

## Architecture

```
User Input
    │
    ▼
┌──────────────┐
│    Planner    │
│  - decompose  │
│  - strategize │
│  - select     │
└──────┬───────┘
       │ Plan
       ▼
┌──────────────────┐
│ Executor Controller│
│  - dispatch       │
│  - monitor        │
│  - handle failures│
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Capability Router │
│  (Registry)       │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│   Capabilities    │
│  (LLM, Memory,    │
│   Tools, etc.)    │
└──────────────────┘
```

---

## Implementation

### Planner (`core/orchestration/planner.py`)

```python
class Planner:
    def build(self, intent: str) -> Plan:
        """Décompose l'intention en étapes."""
        pass
```

### Executor (`core/orchestration/executor.py`)

```python
class Executor:
    async def run(self, capability_name, context, **kwargs):
        """Exécute une Capability via le Registry."""
        pass
```

### Observer (`core/orchestration/observer.py`)

```python
class Observer:
    def analyze(self, result) -> Observation:
        """Analyse le résultat et produit une observation."""
        pass
```

### Registry (`core/orchestration/registry.py`)

```python
class CapabilityRegistry:
    def get(self, name: str) -> Capability:
        """Route vers la Capability appropriée."""
        pass
```

---

## Consequences

### Positive

* **Better reasoning** — Planner can optimize strategy before execution
* **Scalable task execution** — Executor can parallelize, retry, queue
* **Easier debugging** — Separation of concerns, clear logs per phase

### Negative

* **More components** — additional complexity
* **Latency** — planning phase adds overhead

---

## Compliance

* Tout nouveau code doit utiliser `Planner` pour décomposer les tâches
* Tout exécution passe par `Executor`
* L'observation est systématique via `Observer`

## References

* [Constitution Architecturale](/engineering/architecture/constitution.md) — Principe 5 (Orchestration)
* [RFC-007](/engineering/rfc/rfc-007-architecture-constitution.md) — Règles C004, C005
* [ADR-1001](/engineering/adr/ADR-1001-core-is-not-an-executor.md) — Core is NOT an Executor