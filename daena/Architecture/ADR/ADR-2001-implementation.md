# ADR-2001 — Memory is a Cognitive Layer — Implementation Report

## Date
2026-06-22

## Statut
✅ **Implémenté**

---

## Résumé

La mémoire est maintenant architecturée comme un **sous-système cognitif**, pas une couche de persistance.

**Responsabilités cognitives:**
- Context retention (rétention de contexte)
- User modeling (modélisation utilisateur)
- Knowledge accumulation (accumulation de connaissances)
- Behavior adaptation (adaptation comportementale)

**Interdiction:**
> All direct database access is forbidden from Core.

---

## Modifications

### 1. Architecture cible

```
┌─────────────────────────────────────────────────────────────┐
│                    Cognitive Memory Layer                    │
│  (core/memory/)                                             │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  MemoryBackend (ABC)                                 │  │
│  │  - store()         → Stocker une entrée cognitive    │  │
│  │  - retrieve()      → Récupérer par clé              │  │
│  │  - search()        → Recherche sémantique           │  │
│  │  - delete()        → Supprimer                      │  │
│  │  - list_namespaces() → Lister les espaces           │  │
│  │  - clear()         → Nettoyer                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ✓ Aucune dépendance technologique                          │
│  ✓ Aucun code SQL/NoSQL                                     │
│  ✓ Aucun accès fichier direct                               │
│  ✓ Abstractions cognitives uniquement                        │
└─────────────────────────────────────────────────────────────┘
                          ▲
                          │ implémenté par
                          │
┌─────────────────────────────────────────────────────────────┐
│                    Memory Plugin Layer                       │
│  (plugins/memory/)                                          │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Redis      │  │   SQLite     │  │   Qdrant     │     │
│  │   Backend    │  │   Backend    │  │   Backend    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                             │
│  ✓ Lazy imports pour les dépendances                        │
│  ✓ Technologies spécifiques isolées                          │
│  ✓ Remplaçables sans toucher au core                         │
└─────────────────────────────────────────────────────────────┘
```

### 2. Déplacements effectués

**De `core/memory/` vers `plugins/memory/`:**

| Fichier | Avant | Après | Raison |
|---------|-------|-------|--------|
| `redis_backend.py` | `core/memory/` | `plugins/memory/` | Import direct `redis.asyncio` |
| `sqlite_backend.py` | `core/memory/` | `plugins/memory/` | Import direct `sqlite3` |

**Lazy imports ajoutés:**

```python
# plugins/memory/redis_backend.py
def _get_redis():
    try:
        import redis.asyncio as aioredis
        return aioredis
    except ImportError:
        raise ImportError("Redis package not installed...")

# plugins/memory/sqlite_backend.py
def _get_sqlite():
    import sqlite3
    return sqlite3
```

### 3. Tests de conformité (`tests/core/test_cognitive_memory.py`)

**Ajouté:**
- 6 tests unitaires vérifiant l'architecture cognitive:
  1. `test_memory_backend_is_abstract` — MemoryBackend hérite de ABC
  2. `test_no_database_imports_in_core_memory` — Aucun import DB dans core/memory/
  3. `test_memory_entry_is_cognitive` — MemoryEntry = entrée cognitive, pas ligne DB
  4. `test_memory_system_is_cognitive_not_persistence` — MemorySystem = système cognitif, pas ORM
  5. `test_no_filesystem_operations_in_core_memory` — Aucune opération fichier directe
  6. `test_memory_backends_are_in_plugins` — Backends technologiques dans plugins/

**Résultat:** ✅ 6/6 tests passent

---

## Conformité ADR-2001

| Règle ADR | Status | Preuve |
|-----------|--------|--------|
| Memory is not a database layer | ✅ | core/memory/ ne contient que des abstractions |
| Context retention | ✅ | MemoryEntry avec timestamp, namespace, metadata |
| User modeling | ✅ | MemorySystem avec namespaces pour isolation |
| Knowledge accumulation | ✅ | Méthodes store/retrieve/search cognitives |
| Behavior adaptation | ✅ | TTL, metadata pour adaptation comportementale |
| No direct database access from Core | ✅ | 0 imports DB dans core/memory/ |
| All interactions through abstractions | ✅ | MemoryBackend (ABC) |

---

## Comparaison: Before vs After

### ❌ Avant (violation ADR-2001)

```python
# core/memory/redis_backend.py
import redis.asyncio  # ❌ Dépendance technologique dans core

class RedisBackend(MemoryBackend):
    def __init__(self, ...):
        self._client = redis.asyncio.Redis(...)  # ❌ Connexion DB directe
```

```python
# core/memory/sqlite_backend.py
import sqlite3  # ❌ Dépendance technologique dans core

class SQLiteBackend(MemoryBackend):
    def __init__(self, db_path: str):
        self._conn = sqlite3.connect(db_path)  # ❌ Accès DB direct
```

### ✅ Après (conforme ADR-2001)

```python
# core/memory/__init__.py
from abc import ABC, abstractmethod

class MemoryBackend(ABC):
    """Abstraction cognitive de la mémoire."""
    
    @abstractmethod
    async def store(self, entry: MemoryEntry) -> None:
        """Stocker une entrée cognitive."""
        pass
    
    @abstractmethod
    async def retrieve(self, key: str, namespace: str = "default") -> MemoryEntry | None:
        """Récupérer une entrée par clé."""
        pass
```

```python
# plugins/memory/redis_backend.py
def _get_redis():
    import redis.asyncio as aioredis  # ✓ Lazy import hors core
    return aioredis

class RedisBackend(MemoryBackend):
    async def _ensure_client(self):
        aioredis = _get_redis()  # ✓ Import au moment de l'usage
        self._client = aioredis.Redis(...)
```

---

## Exemples d'usage

### Core (abstractions cognitives)

```python
from core.memory import MemoryBackend, MemoryEntry, MemorySystem

# Le core ne connaît que des concepts cognitifs
memory = MemorySystem()

# Stocker une connaissance
await memory.store(MemoryEntry(
    key="user_preference",
    value={"theme": "dark", "language": "fr"},
    namespace="user_123",
    metadata={"type": "preference"}
))

# Rechercher par contexte
results = await memory.search(
    query="user preferences",
    namespace="user_123",
    limit=5
)
```

### Plugins (implémentations technologiques)

```python
from plugins.memory.redis_backend import RedisBackend
from plugins.memory.sqlite_backend import SQLiteBackend

# Redis pour cache court-terme
redis = RedisBackend(host="localhost", port=6379)
memory.register_backend("cache", redis)

# SQLite pour persistance développement
sqlite = SQLiteBackend(db_path="memory.db")
memory.register_backend("persistent", sqlite)
```

---

## Impact

- ✅ **Memory is cognitive** — La mémoire est un sous-système cognitif, pas une DB
- ✅ **Context retention** — Rétention de contexte via MemoryEntry
- ✅ **User modeling** — Namespaces pour isolation utilisateur
- ✅ **Knowledge accumulation** — Accumulation via store/search
- ✅ **Behavior adaptation** — TTL, metadata pour adaptation
- ✅ **No vendor lock-in** — Backends remplaçables sans toucher au core
- ✅ **Full portability** — Core indépendant de toute technologie
- ✅ **Testé** — 6 tests de conformité passent

---

## Références

- [ADR-2001](/engineering/adr/ADR-2001-memory-is-a-cognitive-layer.md)
- [ADR-1005](/engineering/adr/ADR-1005-core-technology-independence.md) — Core Technology Independence
- [Constitution Architecturale](/engineering/architecture/constitution.md) — Principe 1 (Core Abstraction)
- [RFC-007](/engineering/rfc/rfc-007-architecture-constitution.md) — Règles C001-C002