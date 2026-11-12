# MEM_014_IMPLEMENTATION_ROADMAP

Date : 2026-11-03

## Phase 0 — Validation documentaire et gouvernance

Objectif : geler les concepts MEM-014.
Composants : Obsidian, docs, registry, audits.
Tâches : examiner les ADR/ESR/ASR, réconcilier les documents, valider les statuts.
Tests : cohérence documentaire, liens internes.
Critères : pas de contradictions, pas de nouvelle fonction non validée.
Risques : documentation concurrente.
Décisions : arbitrage des formats et contrats.
Conditions de passage : accord humain.

## Phase 1 — Modèle et registry (IMPLÉMENTÉ — socle Phase 1 disponible)

Objectif : stabiliser schema et routes.
Composants : `core/engineering_memory`, `Metadata/REGISTRY.md`, services.
Tâches : instancier IDs, schémas versionnés, registre unique.
Tests : unitaires, intégration locale.
Critères : validation réelle de format, refs et permissions.
Risques : compatibilité rétroactive, champs non définis.
Conditions : validation des modèles.

## Phase 2 — Validation et sécurité

Objectif : applications conformes et autorisée.
Composants : auth, permissions, extensions, applications.
Tâches : tests routage et permission ; HROT application.
Tests : négatifs et positifs de permissions, conformance.
Critères : réussite de la suite.
Risques : accès privilégié et absence de preuves.

## Phase 3 — Intégration des applications

Objectif : Odin, Frame et TradingAgents.
Composants : contrôleurs, API, UI, ressources.
Tâches : adapter et tester chacun.
Tests : integration end-to-end et contraintes.
Critères : pas d'intégration sans preuve.
Risques : latence, dépendances, incompatibilité.

## Phase 4 — Résilience et observabilité

Objectif : persistance, integrity, diagnostics.
Composants : write atomic, manifestes, logs, permissions.
Tâches : backup et restore, index et métriques.
Tests : tests de charge et d'intégrité.
Critères : pas de perte, traçabilité et preuves.
Risques : degradations et pas de vérification réelle.

## Phase 5 — Documentation et conformité finale

Objectif : documentation cohérente et export sélectif.
Composants : ADR/ESR/ASR, manifests, docs et Obsidian.
Tâches : officialisation, procédures, publication sélective.
Tests : conformance et nettoyage.
Critères : pas de document faux, pas de données sensibles.
Risques : divergences de version.

## Ordre recommandé

1. Documents et modèles.
2. Registry et identités.
3. Validation et permissions.
4. Intégration applicative.
5. Résilience et tests.
6. Publication par allowlist.

Aucune phase ne démarre sans approbation humaine.
