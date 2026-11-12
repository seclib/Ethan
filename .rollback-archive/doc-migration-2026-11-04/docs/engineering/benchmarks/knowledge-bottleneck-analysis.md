# Knowledge Bottleneck Analysis

## Source of evidence
- `core/rag/pipeline.py`
- `core/rag/ingestion.py`
- `core/rag/retrieval.py`
- `core/rag/vector_store.py`
- `core/knowledge/collections.py`
- `tests/benchmarks/knowledge/scenarios.py`
- `baseline-rag-100.json`

## Findings

### 1. Ingestion cost (confirmed)
- RAG ingestion iterates every document.
- Chunking cost grows with document size and configured strategy.
- Embeddings calls occur per `ingest()` via `embed_texts`, not per chunk in the deterministic provider.
- Stored embeddings enable reconstruction.

### 2. Retrieval cost (confirmed)
- `_ensure_loaded()` and `retrieve()` execute embed_text for query.
- Retrieval passed document_id scope avoids full scan externally; backend memory still scans all records.
- Complexity is O(number chunks) for memory vector store.

### 3. Reconstruction cost (confirmed)
- Reload persisted docs via `store.list("rag-documents")`.
- Rebuilds memory index with O(number chunks).
- Native memory vector store loses index at restart, so required rebuild.
- Qdrant/ChromaDB persistent backends may reduce this but are optional.

### 4. Embeddings counter confusion (confirmed)
- Our benchmark dummy counts one call per document, not one per chunk.
- `101` and `1001` are ingestion + retrieval, not only reconstruction.
- No evidence shows 1000 extra embedding generation during reconstruction.

### 5. Collections / storage (probable)
- CoreRecordStore scans domain records.
- SQL uses index `(domain, updated_at)`.
- Document payload JSONB can be large.
- Potential N+1 if collection membership document details call separately.

## Classification
- confirmed: O(N*chunks) memory retrieval & reconstruction.
- probable: large JSONB payload impacts latency but not enough data due sandbox.
- not demonstrated: migration need or external worker need.

## Priority
1. paginated document store.
2. scoped document access (projection)
3. optional persistent vector backend.
4. measured ACL/reindex dedicated tests.
