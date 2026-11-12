# ETHAN — Image Docker `ethan-api` : inventaire & consolidation (Mission 15)

Date : 2026-11-04
Statut : `NON DESTRUCTIF — ANALYSE ET PROPOSITION`

## Inventaire vérifié

| Image | Utilisation | Id | Création | Taille |
|---|---|---|---|---|
| `ethan-api:latest` | Production locale (`ethan-api` Up, healthy) | `2e592a884d38` | 2026-11-04 12:04:01 | 1.96 GB |
| `ethan-api:rollback-detect-20261104` | Retag du même ID | `2e592a884d38` | idem | idem |
| `ethan-api:rollback-cap-detect` | Ancien rollback, non utilisé | `e7a1800de953` | 2026-11-04 11:40:56 | 1.96 GB |
| `ethan-api:rollback-capabilities` | Ancien rollback, non utilisé | `41895ba3c1b2` | 2026-11-04 10:19:26 | 1.96 GB |
| `ethan-api:rollback-20261104` | Rollback plus ancien | `a6742f066ea4` | 2026-11-01 07:56:58 | 1.96 GB |

Tags digest : aucun registry, aucun digest promotionnel.

Conteneur :
- `ethan-api` : image `ethan-api`, state `running healthy`.
- `ethan-odin-controller-1` : utilise l'image `ethan-api` en tant qu'image de base non taguée? Image colonne says ethan-api. Container running.

## Références Docker

- `docker-compose.yml` utilise `image: ethan-api` (tags par défaut => `latest`).
- `deploy/Dockerfile.api` est la source canonique présente.
- Compose aliases images multi-services avec `image: ethan-api`.

## Décisions

- Conserver `ethan-api:latest` (`2e592a884d38`) comme référent actuel.
- Conservateur `rollback-20261104` comme rollback formateur? Le tag `rollback-detect-20261104` est redondant (same ID), à réexaminer.
- Les trois autres images n'ont pas de conteneur actif selon les résultats, mais ni leur historique ni leurs capacités n'ont été prouvés.
- Aucune suppression proposée ici sans autorisation explicite.

## Stratégie recommandée (non destructive)

1. Tag stable version à partir de la référence active (ex. `ethan-api:v-YYYYMMDD-shortsha`) — uniquement via décision humaine.
2. Conserver au minimum : actif + un rollback vérifié.
3. Rester en mode "latest" jusqu'à ce que la version soit étiquetée explicitement.
4. Nettoyage futur seulement après vérification de l'historique et des scripts.

## Commandes déjà exécutées (read-only)

```bash
docker images --no-trunc --format '{{...}}' | grep ethan-api
docker ps -a ... | grep -i ethan-api
grep -R ethan-api {deploy,docker-compose.yml,scripts,Makefile}
```

## Plan de nettoyage proposé (non exécuté)

Candidate IDs (à valider) :
- `e7a1800de953` (rollback-cap-detect)
- `41895ba3eb` (rollback-capabilities)
- `a6742f066ea4` (rollback-20261104 plus ancienne)
- `36fc075ff40b` (dangling 211 MB)

Ne pas exécuter avant accord explicite et validation des conteneurs.

## Statut final

- Image active supposée : `2e592a884d38` (latest et rollback-detect-...).
- Statut :
  - `VALIDATED` pour l'existence et les conteneurs
  - `PARTIALLY_VALIDATED` pour l'identification historique
  - `BLOCKED` pour toute suppression (aucune autorisation)
