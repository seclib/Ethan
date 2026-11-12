# ADR-1015 — Modèle d'embeddings et compatibilité index

- Statut : Proposed
- Contexte : Qdrant exige une dimension ; ChromaDB/HNSW comme cos.
- Décision : embeddings liés au modèle actif; changement déclenche reindexation contrôlée.
- Risques : incompatibilités dimension ; coût de reconstruction.
- Tests : tests embedding/reindex futurs.
