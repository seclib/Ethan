# ASR — Knowledge Document Pipeline (hypothèse)

## Domain chain
Source -> Document -> Version -> Extracted Content -> Chunks -> Embeddings -> Index -> Retrieval -> RAG

## Ownership
- Core owns state
- RAGPipeline owns storage/RAG
- KnowledgeCollectionManager owns collections/acl
- WebUI is client

## Backends
- memory
- ChromaDB
- Qdrant

## Persistencereconstruction
- `_ensure_loaded`
- `_load_vector_store`
