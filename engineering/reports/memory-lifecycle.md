# Memory Lifecycle — RFC-006

## 1. Overview

This document defines the lifecycle stages of memory items within Ethan OS. Every memory item passes through stages from capture to expiration. The lifecycle is managed by the **MemoryManager** and is independent of the underlying storage provider.

## 2. Lifecycle Diagram

```
        ┌─────────────┐
        │   Capture    │
        └──────┬──────┘
               │
               ▼
        ┌─────────────┐
        │Classification│
        └──────┬──────┘
               │
               ▼
        ┌─────────────┐
        │   Storage    │◄──────────────┐
        └──────┬──────┘                │
               │                       │
        ┌──────┴──────┐                │
        │              │               │
        ▼              ▼               │
  ┌──────────┐  ┌──────────┐          │
  │ Retrieval│  │ Retention│          │
  └────┬─────┘  │  Check   │          │
       │        └────┬─────┘          │
       ▼             │                │
  ┌──────────┐       │                │
  │Summariz. │       │   still valid  │
  └────┬─────┘       ├────────────────┘
       │             │
       ▼             ▼
  ┌──────────┐  ┌──────────┐
  │ Promotion│  │Expiration│
  │(type→type)│  │ (delete) │
  └──────────┘  └──────────┘
```

## 3. Stage 1: Capture

**Description**: Raw data enters the memory system from any application component.

**Sources**:
- User messages (conversations, commands)
- Agent outputs (tool results, completions, reasoning steps)
- Skill results (search results, analysis, automation outputs)
- Plugin events (external integrations)
- System events (errors, warnings, state changes)

**Capture Modes**:
| Mode | Description | Use Case |
|------|-------------|----------|
| Synchronous | Captured immediately, caller waits | Critical context (current conversation) |
| Asynchronous | Captured via event bus, no blocking | Analytics, logs, non-critical events |
| Batch | Aggregated before storage | High-volume events, metrics |

**Data Shape**:
```python
@dataclass
class MemoryItem:
    id: str                    # unique identifier
    content: Any               # the actual data
    content_type: str          # "text", "json", "embedding", "binary"
    memory_type: MemoryType    # WORKING, EPISODIC, SEMANTIC, PROCEDURAL
    source: str                # "agent", "skill", "plugin", "user", "system"
    session_id: str            # optional, for working memory
    user_id: str               # optional, for episodic memory
    timestamp: datetime        # when captured
    ttl: int                   # seconds, 0 = no expiration
    metadata: dict             # flexible metadata
    priority: int              # 0 (low) to 10 (high)
    access_count: int          # incremented on each retrieval
```

## 4. Stage 2: Classification

**Description**: The MemoryManager determines which memory type the captured data belongs to.

**Classification Rules**:
| Input Characteristic | Memory Type | Example |
|---------------------|-------------|---------|
| Session-scoped, temporary, conversational | Working | Current chat messages, active tool state |
| Past interactions, completed tasks, user history | Episodic | Yesterday's conversation, completed code review |
| Knowledge, documentation, facts, indexed data | Semantic | PDF content, repository index, manuals |
| How-to, workflows, automation steps, capabilities | Procedural | Plugin definitions, agent workflows, automation rules |

**Ambiguity Resolution**:
1. If source explicitly specifies `memory_type` → use it
2. If `ttl` is very short (< 5 min) → classify as Working
3. If content contains embeddings or vectors → classify as Semantic
4. If content includes workflow/action definitions → classify as Procedural
5. Default → Episodic

## 5. Stage 3: Storage

**Description**: Data is stored in the appropriate provider through the MemoryManager.

**Storage Flow**:
1. MemoryManager receives classified memory item
2. Selects provider based on routing config (memory type → provider)
3. Serializes content to JSON (structured) or binary (vectors)
4. Attaches metadata (timestamp, source, priority, TTL)
5. Stores via provider's `store()` method
6. Adds to local LRU cache if frequently accessed

**Serialization**:
```python
# JSON for structured data (Redis, PostgreSQL)
serialized = {
    "id": item.id,
    "content": json.dumps(item.content),
    "content_type": item.content_type,
    "memory_type": item.memory_type.value,
    "source": item.source,
    "timestamp": item.timestamp.isoformat(),
    "ttl": item.ttl,
    "metadata": item.metadata,
    "priority": item.priority,
    "access_count": 0
}

# Binary for vectors (Qdrant)
serialized = {
    "id": item.id,
    "vector": item.content,
    "payload": {
        "content_type": item.content_type,
        "memory_type": item.memory_type.value,
        "source": item.source,
        "timestamp": item.timestamp.isoformat(),
        "metadata": item.metadata
    }
}
```

## 6. Stage 4: Retrieval

**Description**: Application components request stored memory items through the MemoryManager.

**Retrieval Modes**:
| Mode | Description | Provider | Use Case |
|------|-------------|----------|----------|
| **Direct lookup** | Fetch by memory_id | All | Get specific item |
| **Semantic search** | Query by content similarity | Qdrant | Find related knowledge |
| **Temporal search** | Query by time range | PostgreSQL | "What happened yesterday?" |
| **Pattern search** | Query by metadata tags | PostgreSQL | "Find all errors from plugin X" |
| **Full-text search** | Query by text content | PostgreSQL | "Find documents about deployment" |

**Cache Strategy**:
- LRU cache with configurable max size (default: 1000 items)
- Cache hit: return immediately (sub-millisecond latency)
- Cache miss: fetch from provider, cache for TTL/10 duration
- Cache invalidation: on update/delete of cached item

## 7. Stage 5: Summarization

**Description**: Memory items can be summarized to extract key information, reduce storage, and improve retrieval speed.

**When Summarization Occurs**:
- When memory size exceeds configurable threshold (e.g., > 100KB)
- Before promotion to a different memory type
- Periodically as maintenance (configurable interval)
- On explicit request via `memory:summarize` event

**Summarization Approaches**:
| Approach | Method | Quality | Speed | Use Case |
|----------|--------|---------|-------|----------|
| Truncation | Keep first N characters | Low | Instant | Large text blocks |
| Extraction | Extract key-value pairs from metadata | Medium | Fast | Structured data |
| LLM-based | Use local/cloud LLM for summarization | High | Slow | Important episodic memories |

**LLM Summarization Trigger**:
```yaml
summarization:
  enabled: true
  max_size_bytes: 100000
  method: "llm"
  llm:
    model: "llama3.2"
    prompt: "Summarize the following memory item in 2-3 sentences..."
    max_tokens: 200
  batch_size: 10
  schedule: "*/30 * * * *"
```

## 8. Stage 6: Promotion

**Description**: Information moves between memory types as it becomes more or less relevant. Promotion is automatic based on configurable policies.

**Promotion Paths**:
```
     Working ──────────────────► Episodic ────────────────► Semantic
        │                             │                         │
        │  (TTL expired but           │  (accessed > N times    │  (no promotion,
        │   important)                │   or explicitly saved)  │   persistent)
        │                             │                         │
        ▼                             ▼                         ▼
   Expiration                    Expiration                 (persistent)

Procedural ───── (manual updates only, no automatic promotion) ────► (versioned)
```

**Promotion Triggers**:
| From | To | Trigger | Condition |
|------|----|---------|-----------|
| Working → Episodic | TTL expiration | TTL expired + accessed ≥ 1 time |
| Working → Expiration | TTL expiration | TTL expired + accessed = 0 (unimportant) |
| Episodic → Semantic | Frequency threshold | Accessed ≥ N times (default: 10) |
| Episodic → Expiration | Retention policy | Age > retention_days (default: 90) |
| Semantic | N/A | Persistent, never auto-expires |

**Promotion Pipeline**:
1. **Promoter worker** scans memory types periodically (configurable interval)
2. For each item, evaluates promotion rules (age, access count, priority)
3. If promotion required:
   - Summarize content (optional, configurable)
   - Delete from source provider
   - Store in target provider with updated memory type
4. Logs all promotions for audit

## 9. Stage 7: Expiration

**Description**: Memory items are permanently deleted when their TTL or retention policy expires.

**Expiration Policies**:
| Memory Type | Default TTL | Deletion Strategy | Grace Period |
|-------------|-------------|-------------------|-------------|
| Working | 5 minutes | Hard delete | None |
| Episodic | 90 days | Soft delete → hard delete | 30 days |
| Semantic | No expiration | Manual only | N/A |
| Procedural | No expiration | Manual only | N/A |

**Deletion Strategies**:
```yaml
deletion:
  hard:
    description: "Immediately remove from provider"
    applies_to: [working]
    action: "DELETE FROM provider WHERE id = ?"
  soft:
    description: "Mark as deleted, hide from queries"
    applies_to: [episodic]
    action: "UPDATE SET deleted_at = NOW(), is_deleted = TRUE"
    cleanup_after_days: 30
  archive:
    description: "Move to cold storage before hard delete"
    applies_to: [episodic]
    export: "JSON → S3/disk"
    cleanup_after_days: 30
```

**Expirer Worker**:
```yaml
expirer:
  enabled: true
  interval: 15  # minutes between scans
  batch_size: 100
  schedules:
    working:
      scan_interval: 5
      cleanup_immediately: true
    episodic:
      scan_interval: 60
      cleanup_after_days: 30
```

## 10. Workers Summary

| Worker | Schedule | Responsibility | Configurable |
|--------|----------|----------------|-------------|
| **Promoter** | Every 5 min | Scan Working → promote to Episodic | interval, thresholds |
| **Summarizer** | Every 30 min | Summarize large items | method, size threshold |
| **Expirer** | Every 15 min | Remove expired items | TTLs per type, grace periods |
| **Archiver** | Daily | Move soft-deleted to cold storage | enabled, storage path |

Workers run asynchronously inside the MemoryManager using a background task scheduler.

## 11. Observability

Each lifecycle stage emits metrics:

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `memory.capture.count` | Counter | memory_type, source | Items captured |
| `memory.capture.latency` | Histogram | memory_type | Time to capture |
| `memory.classification.time` | Histogram | - | Time to classify |
| `memory.storage.latency` | Histogram | provider, memory_type | Storage provider latency |
| `memory.retrieval.cache_hit` | Counter | memory_type | Cache hits |
| `memory.retrieval.cache_miss` | Counter | memory_type | Cache misses |
| `memory.retrieval.latency` | Histogram | provider, memory_type | Retrieval latency |
| `memory.summarization.count` | Counter | method | Items summarized |
| `memory.promotion.count` | Counter | from_type, to_type | Items promoted |
| `memory.expiration.count` | Counter | memory_type, strategy | Items expired |

All metrics exposed via Prometheus endpoint at `/metrics`.