# ADR-1001 — Core is NOT an Executor

> **Statut** : Accepted
> **Date** : 2026-06-22

---

## Context

Ethan OS needs a central component (Core).

A critical design decision is whether the Core should execute actions directly.

The initial architecture (`core/agents/base.py`) mixes reasoning and execution — agents call LLMs directly (`self.think()`) and can invoke tools without orchestration. This violates the Constitution principle that "Ethan décide, il ne fait pas."

---

## Decision

The Core must NEVER execute external actions directly.

It must only:

* interpret intent
* build plans
* select capabilities
* coordinate execution
* observe results

Execution is delegated entirely to **Capabilities**. The Core orchestrates, never executes.

### Formal Rule

```python
# ✅ Core orchestrates
class Core:
    async def process(self, input: UserInput) -> None:
        intent = await self.interpret(input)
        plan = await self.planner.build(intent)
        for step in plan.steps:
            capability = self.registry.get(step.capability)
            result = await self.executor.run(capability, step.args)
            observation = await self.observer.analyze(result)
            await self.memory.store(observation)

# ❌ Core must NOT do this
class Core:
    async def process(self, input: UserInput) -> None:
        result = await some_tool.execute(input)  # INTERDIT
        await self.llm.think(result)              # INTERDIT
```

### Architecture Impact

```
Avant (violation)              Après (conforme)
┌──────────────┐              ┌──────────────┐
│    Agent     │              │    Core      │
│  self.think()│              │  Planner     │
│  execute()   │              │  Executor    │
└──────┬───────┘              │  Observer    │
       │                      └──────┬───────┘
       ▼                             │
┌──────────────┐                     ▼
│    LLM/Outils│              ┌──────────────┐
│  (direct)    │              │  Capability  │
└──────────────┘              │  Registry    │
                               └──────┬───────┘
                                      │
                               ┌──────┴───────┐
                               │  LLM / Outils│
                               │  (via Cap.)  │
                               └──────────────┘
```

---

## Consequences

### Positive

* **Strong separation of concerns** — Core = décision, Capabilities = exécution
* **Safer system** — toute action passe par une validation (Safety)
* **Replaceable execution layer** — swap capabilities without touching Core
* **Easier testing** — mock capabilities, test Core logic in isolation
* **Modular architecture** — new capabilities = new class, no Core changes

### Negative

* **More indirection** — extra abstraction layer adds complexity
* **Need for orchestration layer** — Planner + Executor + Observer required
* **Performance overhead** — event bus routing adds latency

---

## Implementation Checklist

- [ ] Create `core/capabilities/` with abstract `Capability` class
- [ ] Move tool execution from agents to Capabilities
- [ ] Implement `CapabilityRegistry` for dynamic discovery
- [ ] Add `Executor` service to run capabilities safely
- [ ] Add `Observer` service to analyze results
- [ ] Remove direct `self.think()` calls from agents (migrate to Provider model)

---

## Rule

> **The Core decides. It never acts directly.**

---

## Compliance

* Tout nouveau code dans `core/` ne doit pas exécuter d'action directement
* Les Capabilities sont le seul point d'exécution autorisé
* Le Core orchestre via `Planner → Executor → Observer`

## References

* [Constitution Architecturale](/engineering/architecture/constitution.md) — Principe 5 (Orchestration), Principe 7 (Capability Model)
* [RFC-007](/engineering/rfc/rfc-007-architecture-constitution.md) — Règles C004, C005, C008
* [ADR-001](/engineering/adr/ADR-001-initial-architecture.md) — Processus de décision