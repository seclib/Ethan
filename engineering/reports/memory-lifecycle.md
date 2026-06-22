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
