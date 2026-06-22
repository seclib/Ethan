# Memory Providers — RFC-006

## 1. Overview

This document defines the **MemoryProvider** interface and its concrete implementations for Redis, PostgreSQL, and Qdrant. Every provider implements the same abstract interface, ensuring provider independence and future extensibility.

## 2. Abstract Interface

```python
"""core/memory/provider.py — Abstract MemoryProvider Interface"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional, List


class MemoryType(str, Enum):
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


class ContentType(str, Enum):
    TEXT = "text"
    JSON = "json"
    EMBEDDING = "embedding"
    BINARY = "binary"


@dataclass
class MemoryItem:
    id: str
    content: Any
    content_type: ContentType
    memory_type: MemoryType
    source: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    ttl: int = 0
    metadata: dict = field(default_factory=dict)
    priority: int = 5
    access_count: int = 0


@dataclass
class SearchResult:
    items: List[MemoryItem]
    total: int
    page: int
    page_size: int
    query_time_ms: float


class MemoryProvider(ABC):
    """Abstract base class for all memory providers.
    
    Every storage backend (Redis, PostgreSQL, Qdrant, etc.) must
    implement this interface to be compatible with MemoryManager.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider (create tables, connections, indices)."""
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Gracefully shut down the provider (close connections)."""
        pass

    @abstractmethod
    async def store(self, item: MemoryItem) -> bool:
        """Store a memory item. Returns True if successful."""
        pass

    @abstractmethod
    async def store_batch(self, items: List[MemoryItem]) -> int:
        """Store multiple items atomically. Returns count of stored items."""
        pass

    @abstractmethod
    async def retrieve(self, memory_id: str) -> Optional[MemoryItem]:
        """Retrieve a memory item by ID. Returns None if not found."""
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        memory_type: Optional[MemoryType] = None,
        limit: int = 10,
        offset: int = 0,
        filters: Optional[dict] = None,
    ) -> SearchResult:
        """Search memory items by content/query with optional filters."""
        pass

    @abstractmethod
    async def update(
        self,
        memory_id: str,
        content: Optional[Any] = None,
        metadata: Optional[dict] = None,
        ttl: Optional[int] = None,
    ) -> bool:
        """Update a memory item. Returns True if updated."""
        pass

    @abstractmethod
    async def delete(self, memory_id: str) -> bool:
        """Delete a memory item by ID. Returns True if deleted."""
        pass

    @abstractmethod
    async def delete_batch(self, memory_ids: List[str]) -> int:
        """Delete multiple items. Returns count of deleted items."""
        pass

    @abstractmethod
    async def count(
        self,
        memory_type: Optional[MemoryType] = None,
        filters: Optional[dict] = None,
    ) -> int:
        """Count memory items matching criteria."""
        pass

    @abstractmethod
    async def health_check(self) -> dict:
        """Return provider health status."""
        pass

    @abstractmethod
    async def ping(self) -> bool:
        """Simple connectivity check. Returns True if reachable."""
        pass
```

## 3. Redis Provider (Working Memory)

**Characteristics**:
- Volatile storage with TTL-based expiration
- Sub-millisecond latency for store/retrieve
- No persistence (unless REDIS_PERSISTENCE enabled)
- Limited size per session

**Key design decisions**:
- Uses Redis hashes for structured storage per memory item
- TTL-based auto-expiration (default: 5 minutes)
- Session-scoped tracking via Redis sets
- LRU eviction when session exceeds max items
- Pattern-based search via SCAN (no full-text)

**Configuration**:
```yaml
redis:
  enabled: true
  host: redis
  port: 6379
  db: 0
  prefix: "memory:working:"
  default_ttl: 300
  max_session_items: 100
```

## 4. PostgreSQL Provider (Episodic & Procedural Memory)

**Characteristics**:
- Persistent, structured storage
- Full SQL query capabilities
- Temporal and pattern search
- Versioning for procedural memory

**Key design decisions**:
- Single `memory_items` table with JSONB metadata
- Full-text search via `to_tsvector`/`plainto_tsquery`
- Soft delete with grace period (30 days)
- GIN index on metadata for flexible filtering
- Separate `procedural_versions` table for versioning

**Schema**:
```sql
CREATE TABLE IF NOT EXISTS memory_items (
    id VARCHAR(255) PRIMARY KEY,
    content TEXT NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    memory_type VARCHAR(50) NOT NULL,
    source VARCHAR(255) NOT NULL,
    session_id VARCHAR(255),
    user_id VARCHAR(255),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    ttl INTEGER NOT NULL DEFAULT 0,
    metadata JSONB NOT NULL DEFAULT '{}',
    priority INTEGER NOT NULL DEFAULT 5,
    access_count INTEGER NOT NULL DEFAULT 0,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_memory_type ON memory_items(memory_type);
CREATE INDEX IF NOT EXISTS idx_source ON memory_items(source);
CREATE INDEX IF NOT EXISTS idx_timestamp ON memory_items(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_user_id ON memory_items(user_id);
CREATE INDEX IF NOT EXISTS idx_session_id ON memory_items(session_id);
CREATE INDEX IF NOT EXISTS idx_metadata ON memory_items USING gin(metadata);
CREATE INDEX IF NOT EXISTS idx_fulltext ON memory_items USING gin(to_tsvector('english', content));
```

**Configuration**:
```yaml
postgres:
  enabled: true
  host: postgres
  port: 5432
  database: ethan
  user: ethan
  password: ${POSTGRES_PASSWORD}
  min_pool: 2
  max_pool: 10
```

## 5. Qdrant Provider (Semantic Memory)

**Characteristics**:
- Vector-based storage and similarity search
- Persistent, schema-less storage
- Optimized for embeddings (vectors)
- Payload supports structured metadata

**Key design decisions**:
- Collection per memory type (default: `semantic_memory`)
- Cosine distance for vector similarity
- Payload stores all metadata alongside vectors
- Scroll-based retrieval for non-vector queries
- Auto-creates collection on initialization

**Configuration**:
```yaml
qdrant:
  enabled: true
  url: http://qdrant:6333
  collection_name: semantic_memory
  vector_size: 1536
  distance: COSINE
  grpc_port: 6334
  prefer_grpc: false
```

## 6. Provider Registry

```python
class ProviderRegistry:
    """Registry of available memory providers.
    
    New providers register themselves here. Configuration
    determines which are active and their routing priorities.
    """

    def __init__(self, config: MemoryConfig):
        self.config = config
        self._providers: Dict[str, MemoryProvider] = {}
        self._initialized: bool = False

    async def initialize_all(self) -> None:
        for name, provider_config in self.config.providers.items():
            if not provider_config.get("enabled", True):
                continue
            provider = self._create_provider(name, provider_config)
            if provider:
                try:
                    await provider.initialize()
                    self._providers[name] = provider
                except Exception as e:
                    logger.error(f"Failed to initialize provider {name}: {e}")
        self._initialized = True

    def _create_provider(self, name: str, config: dict) -> Optional[MemoryProvider]:
        providers = {
            "redis": lambda: RedisProvider(
                host=config.get("host", "redis"),
                port=config.get("port", 6379),
                default_ttl=self.config.routing.get("working", {}).get("ttl", 300),
            ),
            "postgres": lambda: PostgresProvider(
                host=config.get("host", "postgres"),
                port=config.get("port", 5432),
                database=config.get("db", "ethan"),
                user=config.get("user", "ethan"),
                password=config.get("password", ""),
            ),
            "qdrant": lambda: QdrantProvider(
                url=config.get("url", "http://qdrant:6333"),
                vector_size=config.get("vector_size", 1536),
            ),
        }
        factory = providers.get(name)
        return factory() if factory else None

    def get_provider(self, name: str) -> Optional[MemoryProvider]:
        return self._providers.get(name)

    def get_all_providers(self) -> Dict[str, MemoryProvider]:
        return dict(self._providers)

    async def shutdown_all(self) -> None:
        for name, provider in self._providers.items():
            try:
                await provider.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down provider {name}: {e}")
```

## 7. Adding a New Provider

To add a new provider (e.g., ChromaDB, Pinecone, SQLite):

1. Create a new class inheriting from `MemoryProvider`
2. Implement all abstract methods
3. Register the provider in `ProviderRegistry._create_provider()`
4. Add configuration to `memory.yaml`

No application code changes needed — the MemoryManager routes to the new provider based on configuration.

## 8. Provider Selection Matrix

| Memory Type | Preferred Provider | Fallback Provider | Reason |
|-------------|-------------------|-------------------|--------|
| Working | Redis | PostgreSQL | Redis is fastest for volatile, TTL-based storage |
| Episodic | PostgreSQL | None (must persist) | PostgreSQL provides structured querying |
| Semantic | Qdrant | None (vector-only) | Qdrant is optimized for vector similarity |
| Procedural | PostgreSQL | None (versioned) | PostgreSQL supports versioning via separate table |