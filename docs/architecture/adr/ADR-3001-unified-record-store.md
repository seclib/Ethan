# ADR-3001 — Unified Record Store

**Statut** : Proposition (brouillon)
**Date** : 2026-09-07
**Contexte** : Trois mécanismes de persistance coexistent dans le Core —
`core/config/store.py` (ConfigStore, table `ethan_config`), `core/state/webui_store.py`
(WebUIStore, records settings/providers), et `core/state/record_store.py` (CoreRecordStore,
PG JSONB `core_domain_records`). Résultat : la configuration peut être écrite à deux endroits
et lire des valeurs divergentes entre les onglets Settings et les managers Core.

**Décision** :

1. `core/state/record_store.py` (CoreRecordStore) devient le **store de records unique** pour
tous les domaines persistants (agents, skills, missions, knowledge, rag docs, settings,
providers…).
2. `ConfigStore` et `WebUIStore` deviennent des **façades** par-dessus ce store : mêmes méthodes,
plus aucun schéma SQL dédié (`ethan_config` migré vers `core_domain_records`).
3. La couche reste **document-oriented** (JSONB) — pas de nouveau schéma relationnel.
4. Le fallback in-memory est conservé pour le mode standalone (infrastructure optionnelle).

**Conséquences** :

- Suppression de `ethan_config` (migration de données une fois).
- Tous les tests de config/settings/providers doivent rester verts (compat).
- Le WebUI ne change pas : l'API `/v1/settings` garde le même contrat.

**Alternatives écartées** :

- Garder 3 stores (dette actuelle — contradictoire).
- Tout mettre dans ConfigStore (perte de la sémantique records par domaine).
