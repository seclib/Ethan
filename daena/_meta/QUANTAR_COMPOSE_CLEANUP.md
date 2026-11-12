# QUANTAR_COMPOSE_CLEANUP

Date : 2026-11-03
Statut : conservé, composant canonique unique

## Action

- Source de conflits : `compose.yaml` et `docker-compose.yml` coexistaient.
- `docker-compose.yml` upstream et `docker-compose.security.yml` consolidés dans `compose.yaml`.
- Suppression contrôlée des fichiers concurrents.
- Validation `docker compose config` : exit 0, sans avertissement.

## Résultat

`examples/quantar/compose.yaml` est l'unique fichier Compose canonique.
