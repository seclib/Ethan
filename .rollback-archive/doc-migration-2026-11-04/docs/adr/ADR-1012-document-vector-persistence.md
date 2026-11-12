# ADR-1012 — Persistance documentaire et vectorielle

- Statut : Proposed
- Contexte : PostgreSQL `core_domain_records` + RAGPipeline.
- Décision : CoreRecordStore reste source de vérité ; vector store persistant optionnel par config.
- Backends : memory, chromadb, qdrant.
- Alternatives : nouvelle base vectorielle dédiée — sans démonstration de besoin.
- Risques : index mémoire volatile; reconstruction O(n).
- Tests : `tests/test_knowledge_collections.py`, `tests/test_rag_strategies.py`

## Optional Capability Correction
- `memory` native is primary fallback.
- Qdrant and ChromaDB are optional integrations only.
- ETHAN must not enable, start, install, or request them by default.
- User explicitly authorizes lifecycle.
- WebUI cannot provision or manage infrastructure.
- Uninstall preserves persisted data by default.
