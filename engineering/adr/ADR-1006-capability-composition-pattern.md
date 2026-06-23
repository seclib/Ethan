# ADR-1006 — Capability Composition Pattern

> **Statut** : Proposed
> **Date** : 2026-06-23

---

## Context

Les capabilities sont actuellement exécutées individuellement. Pour des workflows complexes, nous avons besoin de:

- **Pipelines** — séquence d'étapes
- **Parallélisme** — exécution concurrente
- **Conditionnels** — branchements logiques
- **Boucles** — itérations et retry

Sans composition, chaque workflow nécessite du code custom, menant à:

- duplication de logique
- workflows non-réutilisables
- difficulté de maintenance

---

## Decision

Les capabilities doivent être composables via un **pattern de composition**:

> **Capability Pipeline**

---

## Capability Pipeline Schema

```python
class CapabilityPipeline:
    """Compose capabilities into workflows."""
    
    def __init__(self):
        self.steps: List[PipelineStep] = []
    
    def then(self, capability: str, **kwargs) -> 'CapabilityPipeline':
        """Add sequential step."""
        self.steps.append(SequentialStep(capability, kwargs))
        return self
    
    def parallel(self, *capabilities: str) -> 'CapabilityPipeline':
        """Add parallel steps."""
        self.steps.append(ParallelStep(capabilities))
        return self
    
    def branch(self, condition: str, true_branch: 'CapabilityPipeline', false_branch: 'CapabilityPipeline'):
        """Add conditional branching."""
        self.steps.append(ConditionalStep(condition, true_branch, false_branch))
        return self
    
    def retry(self, max_attempts: int = 3) -> 'CapabilityPipeline':
        """Add retry logic."""
        self.steps.append(RetryStep(max_attempts))
        return self
```

---

## Implementation

### Step Types

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

@dataclass
class PipelineStep(ABC):
    """Abstract pipeline step."""
    pass

@dataclass
class SequentialStep(PipelineStep):
    capability: str
    args: dict

@dataclass
class ParallelStep(PipelineStep):
    capabilities: List[str]

@dataclass
class ConditionalStep(PipelineStep):
    condition: str
    true_branch: 'CapabilityPipeline'
    false_branch: 'CapabilityPipeline'

@dataclass
class RetryStep(PipelineStep):
    max_attempts: int
    step: PipelineStep
```

### Pipeline Executor

```python
class CapabilityPipeline:
    def __init__(self, executor: Executor):
        self.executor = executor
        self.steps: List[PipelineStep] = []
    
    async def execute(self, context: CapabilityContext) -> List[CapabilityResult]:
        results = []
        for step in self.steps:
            if isinstance(step, SequentialStep):
                result = await self.executor.run(step.capability, context, **step.args)
                results.append(result)
            elif isinstance(step, ParallelStep):
                tasks = [
                    self.executor.run(cap, context) 
                    for cap in step.capabilities
                ]
                results.extend(await asyncio.gather(*tasks))
        return results
```

---

## Consequences

* **Reusability** — Workflows définis une fois, réutilisables
* **Composabilité** — Combinaison de pipelines simples pour créer des workflows complexes
* **Testabilité** — Chaque step testable indépendamment
* **Lisibilité** — Code déclaratif, facile à comprendre

---

## Compliance

* Tous les workflows doivent utiliser CapabilityPipeline
* Les capabilities individuelles restent disponibles pour usage direct
* Le PipelineExecutor utilise Executor existant

## References

* [Constitution Architecturale](/engineering/architecture/constitution.md) — Principe 3 (Composabilité)
* [ADR-1002](/engineering/adr/ADR-1002-planner-executor-separation.md) — Planner/Executor Separation
* [ADR-1004](/engineering/adr/ADR-1004-cognitive-loop-architecture.md) — Cognitive Loop