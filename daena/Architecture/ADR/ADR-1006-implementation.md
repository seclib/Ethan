# ADR-1006 — Capability Composition Pattern — Implementation Report

## Date
2026-06-23

## Statut
✅ **Implémenté**

---

## Résumé

Les capabilities peuvent maintenant être composées en workflows réutilisables via le **Capability Pipeline Pattern**.

**Fonctionnalités:**
- Pipelines séquentiels (`.then()`)
- Exécution parallèle (`.parallel()`)
- Branchements conditionnels (`.branch()`)
- Retry logic (`.retry()`)

---

## Modifications

### 1. Core Model (`core/orchestration/pipeline.py`)

**Ajouté:**
- `PipelineStep` (ABC) — Étape abstraite de pipeline
- `SequentialStep` — Exécution séquentielle
- `ParallelStep` — Exécution parallèle
- `ConditionalStep` — Branchement conditionnel
- `RetryStep` — Retry avec max_attempts
- `CapabilityPipeline` — Orchestrateur de pipeline

### 2. Tests (`tests/core/test_pipeline.py`)

**Ajouté:**
- 18 tests unitaires couvrant:
  - Création de pipeline
  - Ajout d'étapes (then, parallel, branch, retry)
  - Exécution séquentielle
  - Exécution parallèle
  - Branchements conditionnels (true/false)
  - Retry logic (succès, échec, exhausted)
  - Workflows complexes
  - API fluent chaining

**Résultat:** ✅ 18/18 tests passent

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CapabilityPipeline                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  .then("cap1")          → SequentialStep                    │
│  .then("cap2")          → SequentialStep                    │
│  .parallel("cap3", "cap4") → ParallelStep                   │
│  .branch("cond", true, false) → ConditionalStep             │
│  .retry(3)              → RetryStep                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ utilise
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      Executor                                │
│  (existant, réutilisé)                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Exemples d'usage

### Pipeline simple (séquentiel)

```python
from core.orchestration.pipeline import CapabilityPipeline

pipeline = CapabilityPipeline(executor)
pipeline.then("validate", data=input_data)
       .then("process", model="gpt-4")
       .then("save")

results = await pipeline.execute(context)
```

### Pipeline avec parallélisme

```python
pipeline = CapabilityPipeline(executor)
pipeline.then("validate")
       .parallel("notify_email", "notify_slack", "log_audit")
       .then("finalize")

results = await pipeline.execute(context)
# Exécute notify_email, notify_slack, log_audit en parallèle
```

### Pipeline avec condition

```python
pipeline = CapabilityPipeline(executor)

# Branches
premium_branch = CapabilityPipeline(executor)
premium_branch.then("process_premium").then("send_vip_support")

standard_branch = CapabilityPipeline(executor)
standard_branch.then("process_standard")

# Condition
pipeline.then("validate")
       .branch("is_premium", premium_branch, standard_branch)
       .then("finalize")

results = await pipeline.execute(context)
```

### Pipeline avec retry

```python
pipeline = CapabilityPipeline(executor)
pipeline.then("external_api_call").retry(max_attempts=3)
       .then("process_result")

results = await pipeline.execute(context)
# Retry jusqu'à 3 fois en cas d'échec
```

### Workflow complexe

```python
pipeline = CapabilityPipeline(executor)

# Build complex workflow
pipeline.then("authenticate", token=token)
       .parallel("check_quota", "check_permissions")
       .branch(
           "has_quota",
           CapabilityPipeline(executor).then("process"),
           CapabilityPipeline(executor).then("reject_quota_exceeded")
       )
       .retry(max_attempts=2)
       .then("notify_success")

results = await pipeline.execute(context)
```

---

## API Reference

### CapabilityPipeline

```python
class CapabilityPipeline:
    def __init__(self, executor: Executor)
    
    # Builder methods (fluent API)
    def then(self, capability: str, **kwargs) -> CapabilityPipeline
    def parallel(self, *capabilities: str) -> CapabilityPipeline
    def branch(self, condition: str, true_branch: CapabilityPipeline, 
               false_branch: CapabilityPipeline | None = None) -> CapabilityPipeline
    def retry(self, max_attempts: int = 3) -> CapabilityPipeline
    
    # Execution
    async def execute(self, context: CapabilityContext) -> List[CapabilityResult]
    
    # Factory
    @staticmethod
    def create(executor: Executor) -> CapabilityPipeline
```

### Step Types

```python
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
    true_branch: CapabilityPipeline
    false_branch: CapabilityPipeline

@dataclass
class RetryStep(PipelineStep):
    max_attempts: int
    step: PipelineStep
```

---

## Conformité ADR-1006

| Règle ADR | Status | Preuve |
|-----------|--------|--------|
| Pipelines séquentiels | ✅ | `.then()` + SequentialStep |
| Exécution parallèle | ✅ | `.parallel()` + ParallelStep + asyncio.gather |
| Branchements conditionnels | ✅ | `.branch()` + ConditionalStep |
| Retry logic | ✅ | `.retry()` + RetryStep |
| Réutilisabilité | ✅ | Workflows définis une fois, réutilisables |
| Composabilité | ✅ | Combinaison de pipelines simples |
| Testabilité | ✅ | 18 tests unitaires |
| Lisibilité | ✅ | API déclarative fluent |

---

## Impact

- ✅ **Reusability** — Workflows réutilisables
- ✅ **Composabilité** — Combinaison de pipelines simples
- ✅ **Testabilité** — Chaque step testable indépendamment
- ✅ **Lisibilité** — Code déclaratif, fluent API
- ✅ **Backward compatible** — Capabilities individuelles toujours disponibles
- ✅ **Testé** — 18 tests passent

---

## Références

- [ADR-1006](/engineering/adr/ADR-1006-capability-composition-pattern.md)
- [Constitution Architecturale](/engineering/architecture/constitution.md) — Principe 3 (Composabilité)
- [ADR-1002](/engineering/adr/ADR-1002-planner-executor-separation.md) — Planner/Executor Separation
- [ADR-1004](/engineering/adr/ADR-1004-cognitive-loop-architecture.md) — Cognitive Loop