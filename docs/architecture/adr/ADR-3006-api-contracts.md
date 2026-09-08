# ADR-3006 — Contrats API versionnés (OpenAPI + tests de contrat)

**Statut** : Proposition (brouillon)
**Date** : 2026-09-07
**Contexte** : La consolidation active du dépôt a déjà cassé des contrats (ex. providers/models),
et le WebUI consomme une surface `/v1/*` large sans garde-fou formel. Le risque de régression
silencieuse entre Core et WebUI est élevé.

**Décision** :

1. L'API FastAPI génère son **OpenAPI** (déjà natif) ; ajouter un **snapshot versionné** du schéma
par version (`docs/api/openapi.<version>.json`).
2. **Tests de contrat** : pour chaque route consommée par le WebUI, un test API vérifie la réponse
(statut + forme minimale du corps). Fichier de référence : `interfaces/api/tests/test_contracts.py`.
3. Les clients WebUI (`lib/api/*.ts`) typent leurs réponses contre le contrat ; toute modification
Core incompatible doit passer par un bump de version + mise à jour du snapshot.

**Conséquences** :

- Un peu de fiabilité supplémentaire lors des refontes ; migration douce.
- Le WebUI garde un contrat stable pendant les phases B→E (cf. §15 de l'évaluation).

**Alternatives écartées** :

- Pas de contrat (statut quo — risque élevé).
- Génération automatique TS depuis OpenAPI (lourd, encore optionnel).
