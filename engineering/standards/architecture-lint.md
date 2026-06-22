# Architecture Lint Rules — Ethan OS

Règles de linting pour vérifier le respect de la Constitution Architecturale.

---

## Règles

### C001 — Core ne dépend pas de technologies externes

**Interdit dans `core/`** :
```python
import redis
import asyncpg
import qdrant_client
import httpx
import aiohttp
import requests
import sqlalchemy
import docker
import kubernetes
```

**Vérification** :
```bash
grep -rn "import redis\|import asyncpg\|import qdrant\|import httpx\|import aiohttp\|import requests\|import sqlalchemy\|import docker\|import kubernetes" core/ --include="*.py"
```

---

### C002 — Domaines ne s'importent pas directement

**Règle** : Les domaines ne doivent pas s'importer directement. Toute communication passe par le bus d'événements ou les interfaces publiques.

**Interdit** :
```python
# core/memory/ ne doit pas importer core/agents/
from core.agents import ...
```

**Autorisé** :
```python
# core/agents/ peut importer core/memory/ via l'interface publique
from core.memory import MemoryManager
```

---

### C003 — Toute technologie externe a un Port et un Adapter

**Règle** : Aucune technologie externe ne doit être utilisée directement sans interface abstraite.

**Structure requise** :
```
core/domain/
├── provider.py      # Port (ABC)
└── providers/
    ├── redis.py     # Adapter
    ├── pg.py        # Adapter
    └── ...
```

---

### C004 — Communication via Event Bus

**Règle** : Les composants ne s'appellent jamais directement. Toute communication passe par le bus d'événements.

**Interdit** :
```python
result = await other_component.do_something()
```

**Autorisé** :
```python
await self.bus.publish("event:name", payload)
await self.bus.subscribe("event:name", handler)
```

---

### C005 — Toute action est une Capability

**Règle** : Aucune action ne doit être exécutée directement. Toute action est une `Capability`.

**Interdit** :
```python
class Agent:
    async def execute_tool(self, ...):
        result = await tool.run(...)  # INTERDIT
```

**Autorisé** :
```python
class Agent:
    async def execute_tool(self, ...):
        result = await self.executor.run("tool_name", context, ...)
```

---

### C006 — Providers IA sont interchangeables

**Règle** : Le Core ne doit pas contenir de références à des providers concrets (Ollama, OpenAI, Anthropic).

**Interdit dans `core/`** :
```python
from providers.ollama import OllamaProvider
from providers.openai import OpenAIProvider
```

**Autorisé** :
```python
from core.providers import ReasoningProvider
```

---

### C007 — Memory via MemoryManager uniquement

**Règle** : Aucun composant hors de `core/memory/` ne doit importer `redis`, `asyncpg` ou `qdrant_client`.

**Vérification** :
```bash
grep -rn "import redis\|import asyncpg\|import qdrant" core/ --include="*.py" | grep -v "core/memory/"
```

---

### C008 — Safety avant toute action

**Règle** : Aucune action ne peut être exécutée sans validation Safety.

**Requis** :
```python
from core.safety import SafetyContext, SafetyValidator

validator = SafetyValidator()
context = SafetyContext(user_id=..., session_id=..., trace_id=...)
if not validator.validate(context):
    raise SafetyViolation("Action non validée")
```

---

## Script de vérification

**Fichier** : `scripts/arch-lint.py`

**Usage** :
```bash
python scripts/arch-lint.py core/
python scripts/arch-lint.py --check C001,C006,C007
```

**Sortie** :
```
[PASS] C001: No external tech imports in core/
[FAIL] C006: core/llm/__init__.py references 'ollama'
[PASS] C007: No direct DB access outside core/memory/
```

---

## Intégration CI/CD

**GitHub Actions** (`.github/workflows/arch-lint.yml`) :
```yaml
- name: Architecture Lint
  run: python scripts/arch-lint.py core/
```

**Pre-commit** (`.pre-commit-config.yaml`) :
```yaml
- repo: local
  hooks:
    - id: arch-lint
      name: Architecture Lint
      entry: python scripts/arch-lint.py
      language: python