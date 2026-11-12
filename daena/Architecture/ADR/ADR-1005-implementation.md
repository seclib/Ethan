# ADR-1005 — Core Technology Independence — Implementation Report

## Date
2026-06-22

## Statut
✅ **Implémenté**

---

## Résumé

Le Core respecte maintenant l'indépendance technologique. Aucune dépendance directe vers des technologies externes (LLM providers, databases, docker, filesystem APIs, external tools).

---

## Modifications

### 1. Déplacement des backends technologiques

**Avant (violation ADR-1005):**
```
core/memory/
├── __init__.py              # Abstractions ✓
├── redis_backend.py         # ❌ Import direct redis.asyncio
└── sqlite_backend.py        # ❌ Import direct sqlite3
```

**Après (conforme ADR-1005):**
```
core/memory/
└── __init__.py              # Abstractions uniquement ✓

plugins/memory/
├── __init__.py
├── redis_backend.py         # ✓ Lazy import redis.asyncio
└── sqlite_backend.py        # ✓ Lazy import sqlite3
```

### 2. Lazy imports pour respecter ADR-1005

**Redis Backend (`plugins/memory/redis_backend.py`):**
```python
# Lazy import de redis pour respecter ADR-1005
def _get_redis():
    try:
        import redis.asyncio as aioredis
        return aioredis
    except ImportError:
        raise ImportError(
            "Redis package not installed. Install: pip install redis"
        )
```

**SQLite Backend (`plugins/memory/sqlite_backend.py`):**
```python
# Lazy import de sqlite3 pour respecter ADR-1005
def _get_sqlite():
    import sqlite3
    return sqlite3
```

### 3. Tests de conformité (`tests/core/test_technology_independence.py`)

**Ajouté:**
- Test AST-based qui scanne tous les fichiers Python du core
- Détecte les imports interdits (openai, anthropic, docker, sqlite3, redis, etc.)
- Vérifie que les abstractions sont bien définies (ABC, abstractmethod)
- Valide la documentation de l'indépendance technologique

**Résultat:** ✅ 4/4 tests passent

---

## Conformité ADR-1005

| Règle ADR | Status | Preuve |
|-----------|--------|--------|
| No LLM providers | ✅ | Aucun import openai/anthropic/cohere dans core/ |
| No databases | ✅ | sqlite3 déplacé vers plugins/memory/ avec lazy import |
| No docker | ✅ | Aucun import docker dans core/ |
| No filesystem APIs | ✅ | Aucun import direct filesystem dans core/ |
| No external tools | ✅ | Aucun import requests/httpx/playwright dans core/ |
| Use abstractions | ✅ | ReasoningProvider, MemoryBackend (ABC) définis |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Core Layer                            │
│  (core/)                                                    │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Providers   │  │   Memory     │  │ Capabilities │     │
│  │  (ABC)       │  │  (ABC)       │  │  (ABC)       │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  ✓ Aucune dépendance technologique                          │
│  ✓ Abstractions uniquement                                   │
└─────────────────────────────────────────────────────────────┘
                          ▲
                          │ utilise
                          │
┌─────────────────────────────────────────────────────────────┐
│                     Plugins Layer                            │
│  (plugins/)                                                 │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Memory     │  │  Providers   │  │   Tools      │     │
│  │  - Redis     │  │  - OpenAI    │  │  - Browser   │     │
│  │  - SQLite    │  │  - Anthropic │  │  - Terminal  │     │
│  │  - Qdrant    │  │  - Ollama    │  │  - ...       │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  ✓ Lazy imports pour les dépendances                        │
│  ✓ Technologies spécifiques isolées                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Exemples d'usage

### Core (abstractions)

```python
from core.memory import MemoryBackend, MemoryEntry

# Le core ne connaît que l'abstraction
class MyMemoryBackend(MemoryBackend):
    async def store(self, entry: MemoryEntry) -> None:
        # Implementation...
        pass
```

### Plugins (implémentations)

```python
from plugins.memory.redis_backend import RedisBackend
from plugins.memory.sqlite_backend import SQLiteBackend

# Redis (avec lazy import)
redis = RedisBackend(host="localhost", port=6379)

# SQLite (avec lazy import)
sqlite = SQLiteBackend(db_path="memory.db")
```

---

## Impact

- ✅ **Full portability** — Le core peut être utilisé avec n'importe quelle technologie
- ✅ **No vendor lock-in** — Pas de dépendance vers un provider/base de données spécifique
- ✅ **Long-term maintainability** — Les technologies peuvent être remplacées sans toucher au core
- ✅ **Testé** — 4 tests de conformité passent
- ✅ **Backward compatible** — Les APIs publiques sont préservées

---

## Références

- [ADR-1005](/engineering/adr/ADR-1005-core-technology-independence.md)
- [Constitution Architecturale](/engineering/architecture/constitution.md) — Principe 1 (Core Abstraction)
- [RFC-007](/engineering/rfc/rfc-007-architecture-constitution.md) — Règles C001-C002