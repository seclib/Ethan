# Docker Image Final Normalization — Rapport

Date : 2026-11-04

## Suppressions effectuées

- Untag `ethan-api:test-rebuild` (digest `41895ba3c1b2`) — image `ethan-api:latest` conservée.
- Suppression du dangling image `e2dbb9ab7cc1a482d...` (1.96 GB).
- Suppression du dangling image `75bed746e1c149725...` (522MB).

## Images conservées et protégées

- `ethan-api:latest`
- `ethan-api:rollback-20261104`
- `ethan-ui:latest`
- `quantar-runtime:latest`
- `frame-frame:latest`
- `odin-odin:latest`
- `ethan-python-base:latest`
- `ethan-modules:latest`
- `ethan-kernel:latest`
- images PostgreSQL, Redis, NATS, Prometheus
- conteneurs et volumes

## Espace récupéré

Environ 1.96 GB + 522 MB (images réellement supprimées) ; le tag test-rebuild ne libérait aucun espace.

## Inventaire final et preuves

- Aucun conteneur affiché comme référent des images supprimées.
- Aucun fichier source, composant ou service n'a été impacté.
- Aucune commande destructive de type prune n'a été lancée.

## Risque résiduel et blocage

`ethan-api:rollback-20261104` reste conservé car `ethan-odin-controller-1` la référence activement.
Aucune autre incohérence majeure n'a été observée.
