# ADR-3004 — Back-end de vecteurs unique

**Statut** : Proposition (brouillon)
**Date** : 2026-09-07
**Contexte** : Deux chemins de persistance vectorielle coexistent : `core/memory`
(`chromadb_backend`, `qdrant_backend`) et `core/rag/vector_store`. Risque de double écriture
et de divergences d'index entre la mémoire et le RAG.

**Décision** :

1. **Un seul back-end de vecteurs** par déploiement, choisi par configuration (par défaut **Qdrant**
quand disponible, Chroma en fallback standalone).
2. `core/rag/vector_store` reste l'unique façade publique ; `core/memory` consomme cette façade
(et non l'inverse) — la mémoire utilise le même index « embeddings » que le RAG.
3. L'ensemble des embeddings (knowledge, facts, memory) partage le même pool d'index.

**Conséquences** :

- Migration des index Chroma → Qdrant (outil de ré-indexation, ou ré-import).
- Le WebUI expose éventuellement le choix du back-end dans les réglages RAG (depuis le Core uniquement).

**Alternatives écartées** :

- Conserver deux backends (dette actuelle — divergence).
