# ADR-1011 — Stratégie RAG Knowledge

- Statut : Proposed
- Contexte : RAGPipeline expose auto, keyword, semantic, hybrid; `normalize_strategy`/`validate_strategy`.
- Décision : conserver les stratégies actuelles et valider côté serveur.
- Alternatives : moteur reranking externe — rejeté sans mesure.
- Justification : réutilisation maximale, moins de dépendances.
- Risques : absence de reranking confirmé ; qualité à mesurer.
- Tests : `tests/test_rag_strategies.py`
