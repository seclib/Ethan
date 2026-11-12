# Docker Image Cleanup — Rapport final

Date : 2026-11-04
Statut : suppression ciblée exécutée avec succès (aucune image active supprimée)

## Vérifications avant suppression

- `ethan-ui:rollback-20261104` (sha256:8ce554...) : aucun conteneur actif/arrêté associé — supprimé.
- `quantar-runtime:phase39` (sha256:4999dad937e9...) : aucune référence applicative — supprimé.
- `quantar-runtime:real-task` (sha256:8c3fb2a42299...) : aucune référence applicative — supprimé.
- image orpheline `dc7bee4d7a27` (ancienne instance UI) : aucun conteneur référencé — supprimée.
- `ethan-api:rollback-20261104` (sha256:a6742f066ea4...) : BLOQUÉE car référencée par le conteneur `ethan-odin-controller-1` (`Up`, healthy). Conservée.

## Images conservées

- `ethan-ui:latest` (sha256:36fc075ff40b...)
- `ethan-api:latest` (sha256:41895ba... )
- `ethan-api:rollback-20261104` (sha256:a6742f066ea4...) — blocage documenté
- `quantar-runtime:latest` (sha256:dc8f2c...)
- `frame-frame:latest`
- `odin-odin:latest`
- `ethan-python-base:latest`
- `ethan-modules:latest`
- `ethan-kernel:latest`
- infrastructures PostgreSQL, Redis, NATS, Prometheus
- conteneurs et volumes existants

## Espace récupéré

- image `ethan-ui` rollback : 211 MB
- image `quantar-runtime:phase39` : 522 MB
- image `quantar-runtime:real-task` : 522 MB
- image `dc7bee4d7a27` : 211 MB
- **Total approximatif supprimé : 1.46 GB**

## Incidents

- `ethan-api:rollback-20261104` n'a pas pu être supprimée à cause du conteneur `ethan-odin-controller-1`, ce qui constitue un blocage de rollback à examiner sans urgence.

## Résultat

Aucune image active supprimée. Aucun service interrompu. Le nettoyage Docker reste possible ultérieurement sous décision humaine pour le rollback API.
