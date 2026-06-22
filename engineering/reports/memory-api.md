# Memory API — RFC-006

## 1. Overview

This document defines the unified public API for the **MemoryManager** service. All application components (agents, skills, plugins) interact with memory exclusively through this API. The API is backend-independent — callers never know whether the underlying storage is Redis, PostgreSQL, or Qdrant.

## 2. API Style

The MemoryManager exposes two interfaces:

| Interface | Protocol | Port | Use Case |
|-----------|----------|------|----------|
| **REST API** | HTTP/JSON | 8100 | Agent/Skill/Plugin integration |
| **Event Bus** | Async events | internal | Internal MemoryAgent integration |

## 3. REST API Reference

### 3.1 Store

Store a new memory item.

```
POST /api/v1/memory
```

**Request Body:**
```json
{
  "content": "User asked about deployment options",
  "content_type": "text",
  "memory_type": "episodic",
  "source": "agent:conversation",
  "session_id": "sess_abc123",
  "user_id": "user_456",
  "ttl": 86400,
  "metadata": {
    "model": "llama3.2",
    "tokens_used": 150,
    "language": "en"
  },
  "priority": 5
}
```

**Response (201):**
```json
{
  "status": "stored",
  "memory_id": "mem_7f8e2a1b",
  "memory_type": "episodic",
  "provider": "postgres",
  "stored_at": "2025-06-22T11:55:00Z",
  "ttl": 86400
}
```

**Response (400 - Validation Error):**
```json
{
  "error": "validation_error",
  "detail": "content is required",
  "fields": {
    "content": ["This field is required"]
  }
}
```

### 3.2 Retrieve

Retrieve a memory item by ID.

```
GET /api/v1/memory/{memory_id}
```

**Response (200):**
```json
{
  "status": "found",
  "item": {
    "id": "mem_7f8e2a1b",
    "content": "User asked about deployment options",
    "content_type": "text",
    "memory_type": "episodic",
    "source": "agent:conversation",
    "session_id": "sess_abc123",
    "user_id": "user_456",
    "timestamp": "2025-06-22T11:55:00Z",
    "ttl": 86400,
    "metadata": {
      "model": "llama3.2",
      "tokens_used": 150,
      "language": "en"
    },
    "priority": 5,
    "access_count": 3
  },
  "cache_hit": false,
  "latency_ms": 2.3
}
```

**Response (404):**
```json
{
  "error": "not_found",
  "detail": "Memory item 'mem_7f8e2a1b' not found"
}
```

### 3.3 Search

Search memory items by content, type, and filters.

```
POST /api/v1/memory/search
```

**Request Body:**
```json
{
  "query": "deployment options",
  "memory_type": "episodic",
  "limit": 10,
  "offset": 0,
  "filters": {
    "session_id": "sess_abc123",
    "source": "agent:conversation",
    "date_from": "2025-06-01T00:00:00Z",
    "date_to": "2025-06-22T23:59:59Z"
  },
  "sort": {
    "field": "timestamp",
    "order": "desc"
  }
}
```

**Response (200):**
```json
{
  "status": "success",
  "items": [
    {
      "id": "mem_7f8e2a1b",
      "content": "User asked about deployment options",
      "content_type": "text",
      "memory_type": "episodic",
      "source": "agent:conversation",
      "timestamp": "2025-06-22T11:55:00Z",
      "metadata": {},
      "priority": 5,
      "access_count": 3
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10,
  "query_time_ms": 4.1
}
```

### 3.4 Update

Update an existing memory item.

```
PUT /api/v1/memory/{memory_id}
```

**Request Body:**
```json
{
  "content": "Updated: User asked about Docker deployment options",
  "metadata": {
    "updated_by": "agent:summarizer",
    "reason": "clarification"
  },
  "ttl": 172800
}
```

**Response (200):**
```json
{
  "status": "updated",
  "memory_id": "mem_7f8e2a1b",
  "updated_at": "2025-06-22T12:00:00Z"
}
```

### 3.5 Delete

Delete a memory item (soft or hard depending on memory type).

```
DELETE /api/v1/memory/{memory_id}
```

**Response (200):**
```json
{
  "status": "deleted",
  "memory_id": "mem_7f8e2a1b",
  "strategy": "soft",
  "deleted_at": "2025-06-22T12:05:00Z"
}
```

### 3.6 Batch Operations

```
POST /api/v1/memory/batch/store
POST /api/v1/memory/batch/delete
```

**Batch Store Request:**
```json
{
  "items": [
    {
      "content": "Item 1",
      "content_type": "text",
      "memory_type": "working"
    },
    {
      "content": "Item 2",
      "content_type": "text",
      "memory_type": "working"
    }
  ]
}
```

**Batch Store Response (201):**
```json
{
  "status": "stored",
  "count": 2,
  "memory_ids": ["mem_001", "mem_002"]
}
```

### 3.7 Summarize

Request summarization of memory items.

```
POST /api/v1/memory/summarize
```

**Request Body:**
```json
{
  "memory_ids": ["mem_7f8e2a1b", "mem_9c3d4e5f"],
  "method": "llm",
  "max_tokens": 200
}
```

**Response (202 - Accepted for async processing):**
```json
{
  "status": "accepted",
  "job_id": "sum_job_001",
  "estimated_items": 2,
  "estimated_time_seconds": 30
}
```

**Status Polling:**
```
GET /api/v1/jobs/sum_job_001
```

**Response (200):**
```json
{
  "status": "completed",
  "job_id": "sum_job_001",
  "results": {
    "summarized": 2,
    "failed": 0,
    "total_bytes_saved": 12500
  }
}
```

### 3.8 Promote

Request promotion of memory items to a different memory type.

```
POST /api/v1/memory/promote
```

**Request Body:**
```json
{
  "memory_ids": ["mem_7f8e2a1b", "mem_9c3d4e5f"],
  "target_type": "semantic",
  "summarize_before": true
}
```

**Response (202 - Accepted):**
```json
{
  "status": "accepted",
  "job_id": "prom_job_001",
  "from_type": "episodic",
  "to_type": "semantic",
  "estimated_items": 2
}
```

### 3.9 Forget (Bulk Delete with Filter)

Delete multiple memory items matching criteria.

```
POST /api/v1/memory/forget
```

**Request Body:**
```json
{
  "memory_type": "working",
  "filters": {
    "session_id": "sess_abc123",
    "older_than": "2025-06-22T10:00:00Z"
  },
  "strategy": "hard"
}
```

**Response (200):**
```json
{
  "status": "deleted",
  "count": 15,
  "strategy": "hard",
  "deleted_at": "2025-06-22T12:10:00Z"
}
```

### 3.10 Health Check

```
GET /api/v1/memory/health
```

**Response (200):**
```json
{
  "status": "healthy",
  "providers": {
    "redis": {
      "status": "healthy",
      "latency_ms": 0.5,
      "items_count": 42
    },
    "postgres": {
      "status": "healthy",
      "latency_ms": 2.1,
      "items_count": 1523
    },
    "qdrant": {
      "status": "healthy",
      "latency_ms": 3.2,
      "items_count": 89
    }
  },
  "cache": {
    "hits": 452,
    "misses": 123,
    "hit_ratio": 0.79,
    "size": 87
  },
  "uptime_seconds": 3600
}
```

### 3.11 Count

```
GET /api/v1/memory/count?memory_type=episodic
```

**Response (200):**
```json
{
  "status": "success",
  "memory_type": "episodic",
  "count": 1523,
  "provider": "postgres"
}
```

### 3.12 Configuration

```
GET /api/v1/memory/config
```

**Response (200):**
```json
{
  "providers": {
    "redis": {"enabled": true, "priority": 1},
    "postgres": {"enabled": true, "priority": 2},
    "qdrant": {"enabled": true, "priority": 3}
  },
  "routing": {
    "working": {"provider": "redis", "fallback": "postgres"},
    "episodic": {"provider": "postgres"},
    "semantic": {"provider": "qdrant"},
    "procedural": {"provider": "postgres"}
  },
  "lifecycle": {
    "working": {"ttl": 300, "max_items": 100, "promotion": true},
    "episodic": {"ttl": 7776000, "retention_days": 90, "promotion": true},
    "semantic": {"ttl": 0},
    "procedural": {"ttl": 0}
  }
}
```

## 4. Event Bus API

The MemoryManager also subscribes to the existing event bus events (backward compatible with `MemoryAgent`).

| Event | Direction | Payload | Response Event |
|-------|-----------|---------|----------------|
| `memory:store` | inbound | `{content, memory_type, source, ...}` | `memory:stored` |
| `memory:retrieve` | inbound | `{memory_id}` | `memory:retrieved` |
| `memory:search` | inbound | `{query, memory_type, filters}` | `memory:searched` |
| `memory:update` | inbound | `{memory_id, content, metadata}` | `memory:updated` |
| `memory:delete` | inbound | `{memory_id}` | `memory:deleted` |
| `memory:forget` | inbound | `{memory_type, filters}` | `memory:forgotten` |
| `memory:summarize` | inbound | `{memory_ids, method}` | `memory:summarized` |
| `memory:promote` | inbound | `{memory_ids, target_type}` | `memory:promoted` |
| `memory:health` | inbound | `{}` | `memory:health_result` |

## 5. Python SDK

```python
"""core/memory/client.py — High-level Python SDK for MemoryManager"""

from typing import Any, Optional, List
import httpx
from core.memory.provider import MemoryType


class MemoryManagerClient:
    """Python client for the MemoryManager HTTP API."""

    def __init__(self, base_url: str = "http://memory:8100", timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)

    async def store(
        self,
        content: Any,
        memory_type: MemoryType = MemoryType.EPISODIC,
        content_type: str = "text",
        source: str = "unknown",
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        ttl: Optional[int] = None,
        metadata: Optional[dict] = None,
        priority: int = 5,
    ) -> dict:
        payload = {
            "content": content,
            "content_type": content_type,
            "memory_type": memory_type.value,
            "source": source,
            "priority": priority,
        }
        if session_id:
            payload["session_id"] = session_id
        if user_id:
            payload["user_id"] = user_id
        if ttl is not None:
            payload["ttl"] = ttl
        if metadata:
            payload["metadata"] = metadata

        response = await self._client.post(
            f"{self.base_url}/api/v1/memory", json=payload
        )
        response.raise_for_status()
        return response.json()

    async def retrieve(self, memory_id: str) -> dict:
        response = await self._client.get(
            f"{self.base_url}/api/v1/memory/{memory_id}"
        )
        response.raise_for_status()
        return response.json()

    async def search(
        self,
        query: str,
        memory_type: Optional[MemoryType] = None,
        limit: int = 10,
        offset: int = 0,
        filters: Optional[dict] = None,
    ) -> dict:
        payload = {"query": query, "limit": limit, "offset": offset}
        if memory_type:
            payload["memory_type"] = memory_type.value
        if filters:
            payload["filters"] = filters

        response = await self._client.post(
            f"{self.base_url}/api/v1/memory/search", json=payload
        )
        response.raise_for_status()
        return response.json()

    async def update(
        self,
        memory_id: str,
        content: Optional[Any] = None,
        metadata: Optional[dict] = None,
        ttl: Optional[int] = None,
    ) -> dict:
        payload = {}
        if content is not None:
            payload["content"] = content
        if metadata is not None:
            payload["metadata"] = metadata
        if ttl is not None:
            payload["ttl"] = ttl

        response = await self._client.put(
            f"{self.base_url}/api/v1/memory/{memory_id}", json=payload
        )
        response.raise_for_status()
        return response.json()

    async def delete(self, memory_id: str) -> dict:
        response = await self._client.delete(
            f"{self.base_url}/api/v1/memory/{memory_id}"
        )
        response.raise_for_status()
        return response.json()

    async def store_batch(self, items: List[dict]) -> dict:
        response = await self._client.post(
            f"{self.base_url}/api/v1/memory/batch/store",
            json={"items": items},
        )
        response.raise_for_status()
        return response.json()

    async def delete_batch(self, memory_ids: List[str]) -> dict:
        response = await self._client.post(
            f"{self.base_url}/api/v1/memory/batch/delete",
            json={"memory_ids": memory_ids},
        )
        response.raise_for_status()
        return response.json()

    async def summarize(
        self, memory_ids: List[str], method: str = "llm", max_tokens: int = 200
    ) -> dict:
        response = await self._client.post(
            f"{self.base_url}/api/v1/memory/summarize",
            json={"memory_ids": memory_ids, "method": method, "max_tokens": max_tokens},
        )
        response.raise_for_status()
        return response.json()

    async def promote(
        self,
        memory_ids: List[str],
        target_type: MemoryType,
        summarize_before: bool = True,
    ) -> dict:
        response = await self._client.post(
            f"{self.base_url}/api/v1/memory/promote",
            json={
                "memory_ids": memory_ids,
                "target_type": target_type.value,
                "summarize_before": summarize_before,
            },
        )
        response.raise_for_status()
        return response.json()

    async def forget(
        self, memory_type: MemoryType, filters: dict, strategy: str = "soft"
    ) -> dict:
        response = await self._client.post(
            f"{self.base_url}/api/v1/memory/forget",
            json={
                "memory_type": memory_type.value,
                "filters": filters,
                "strategy": strategy,
            },
        )
        response.raise_for_status()
        return response.json()

    async def health(self) -> dict:
        response = await self._client.get(f"{self.base_url}/api/v1/memory/health")
        response.raise_for_status()
        return response.json()

    async def count(self, memory_type: Optional[MemoryType] = None) -> dict:
        params = {}
        if memory_type:
            params["memory_type"] = memory_type.value
        response = await self._client.get(
            f"{self.base_url}/api/v1/memory/count", params=params
        )
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        await self._client.aclose()
```

## 6. Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `validation_error` | 400 | Invalid request body/parameters |
| `not_found` | 404 | Memory item not found |
| `provider_unavailable` | 503 | Storage provider is down |
| `rate_limited` | 429 | Too many requests |
| `internal_error` | 500 | Unexpected error |
| `timeout` | 504 | Provider operation timed out |
| `forbidden` | 403 | Operation not allowed on this memory type |

## 7. Rate Limiting

| Endpoint | Rate Limit (per minute) |
|----------|------------------------|
| `POST /store` | 1000 |
| `GET /retrieve` | 5000 |
| `POST /search` | 500 |
| `DELETE /delete` | 500 |
| `GET /health` | 60 |

## 8. Privacy & Security

- **Memory Isolation**: Memory items are scoped by `user_id` and `session_id`
- **Access Control**: All endpoints require API key authentication (header `X-API-Key`)
- **Data Sanitization**: Content is sanitized before storage (PII detection optional)
- **Audit Log**: All CRUD operations are logged with `source` and `user_id`
- **Encryption at Rest**: Provider-level (PostgreSQL TDE, Redis RDB encryption)
- **Retention Compliance**: Configurable retention policies per memory type