# MASTER_IMPLEMENTATION_ROADMAP — ETHAN

Date : 2026-11-03
Statut : PROPOSAL

Ce document ne déclenche aucune implémentation sans validation explicite.

## Phase 0 — Validation CTO

- Objectif : valider les principes.
- Prérequis : idées architecturales déjà documentées.
- Tâches : choix des options.
- Risques : décision prématurée.
- Livrables : decision d'architecture.
- Condition : utilisateur approve.
- Statut : `PENDING_USER_DECISION`.

## Phase 1 — Stabilisation documentaire

- Objectif : définir la source officielle, les schémas et la migration.
- Tâches : ID footer, policy, registry, ADR officiels.
- Livrables : Obsidian docs officiels et préparation ADR.
- Statut : `IN_PROGRESS` à titre(document proof), sans release technique.
- Condition : approval.

## Phase 2 — Hardening backend

- Objectif : fiabilité auth, stockage et sécurité.
- Tâches : Permission final et endpoint tests; compression et charge; tests d'idem; WAL/outbox.
- Livrables : docs, tests, rapports.
- Statut : `PARTIALLY_IMPLEMENTED`.

## Phase 3 — Intégration ciblée

- Objectif : connecter Knowledge, Skills, agents, plugins.
- Tâches : auditer interface point; instrumenter sans blocage; test réel.
- Risques : couplage accidentel.
- Statut : `PARTIALLY_IMPLEMENTED`.

## Phase 4 — Observation et graphes

- Objectif : consolidation + graphe dérivé.
- Conditions : choix d'ADR et data ownership.
- Statut : `NOT_IMPLEMENTED`.

## Phase 5 — Publication et durabilité

- Objectif : pipeline d'export, allowlist, test restore.
- Statut : `PARTIALLY JObject speculative`.

## Artefact courant

Les rapports de delivery et prod readiness documentent des hypothèses.

Aucune action ne doit être démarrée sans approbation explicite.
