# ADR-1003 — Single Entry Intent Model

> **Statut** : Accepted
> **Date** : 2026-06-22

---

## Context

Multiple input types exist (text, voice, API, automation).

Without normalization, each input type requires different handling logic, leading to:
- scattered parsing code
- inconsistent context
- harder memory integration

---

## Decision

All inputs MUST be normalized into a single structure:

> **Intent Object**

---

## Intent Schema

```json
{
  "source": "voice|text|api|automation",
  "user_input": "...",
  "context": {...},
  "timestamp": "..."
}
```

---

## Architecture

```
[Voice] ──┐
[Text] ──┼──► IntentParser ──► Intent ──► Planner
[API] ──┤
[Auto] ──┘
```

---

## Implementation

### Intent (`core/context/intent.py`)

```python
@dataclass
class Intent:
    source: str
    user_input: str
    context: dict
    timestamp: datetime
```

### IntentParser

```python
class IntentParser(ABC):
    @abstractmethod
    async def parse(self, raw_input: Any) -> Intent:
        pass
```

---

## Consequences

* **Unified processing pipeline** — Planner always receives an Intent
* **Easier memory integration** — Intent is stored as a single memory item
* **Consistent reasoning flow** — same pipeline regardless of input type

---

## Compliance

* Toute entrée utilisateur doit être convertie en Intent avant traitement
* Le Planner ne reçoit que des Intent objects
* Les parsers spécifiques (voice, text, API) implémentent IntentParser

## References

* [Constitution Architecturale](/engineering/architecture/constitution.md) — Principe 5 (Orchestration)
* [RFC-007](/engineering/rfc/rfc-007-architecture-constitution.md) — Règles C004
* [ADR-1002](/engineering/adr/ADR-1002-planner-executor-separation.md) — Planner/Executor Separation