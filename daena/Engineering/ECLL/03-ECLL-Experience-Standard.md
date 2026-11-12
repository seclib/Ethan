---
id: ECLL-003
title: ECLL — Experience Standard
type: standard
status: working
version: 1.0.0
tags:
  - standard
  - experience
---

# ECLL — Experience Standard

## 1. Champs obligatoires

| Champ | Description |
|---|---|
| ID | Identifiant stable et unique |
| Title | Nom explicite |
| Status | Statut de l'expérience |
| Date | Date de création |
| Objective | Objectif recherché |
| Context | Contexte technique |
| Hypothesis | Hypothèse testée |
| Previous attempts | Tentatives antérieures liées |
| Strategy | Approche alternative essayée |
| Actions | Actions réalisées |
| Files affected | Fichiers concernés |
| Environment | Versions, services |
| Expected result | Résultat attendu |
| Actual result | Résultat observé |
| Verification | Preuves et tests |
| Root cause | Cause ou hypothèse |
| Lessons learned | Enseignements |
| Next approach | Prochaine stratégie |
| Status | État de l'expérience |

## 2. Statuts

- `PROPOSED` — Tentative envisagée.
- `IN_PROGRESS` — En cours.
- `WORKING` — Opérationnel confirmé.
- `PARTIAL` — Résultat partiel.
- `FAILED` — Échec confirmé.
- `UNVERIFIED` — Non vérifié.
- `SUPERSEDED` — Remplacé.
- `BLOCKED` — Bloqué par dépendance/autorisation.

## 3. Règles

- `WORKING` exige des preuves.
- `FAILED` reste visible.
- Pas de conclusion présentée comme certaine si elle est non vérifiée.
- Les champs inconnus doivent être marqués `non vérifié`.

Voir [[ECLL-AI-Operating-Protocol]].
