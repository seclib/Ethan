# ADR-1014 — Recherche et permissions

- Statut : Proposed
- Contexte : `KnowledgeCollectionManager` expose `require_read`, `require_write`, `check_access`, grants.
- Décision : filtrer le retrieval côté Core avant exposition.
- Alternatives : filtrage client/UI — rejeté.
- Risques : régressions si grants évoluent pendant requête.
- Tests : `tests/test_agent_knowledge_scoping.py`
