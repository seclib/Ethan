# QUANTAR — Consolidation configurations et points d'entrée (Phase 2)

Date : 2026-11-04
Statut : analyse terminée, aucune suppression effectuée

## 1. Configurations Compose

- `examples/quantar/compose.yaml` : configuration active utilisée par ComposeService.
- `examples/quantar/docker-compose.security.yml` : ancienne configuration équivalente orientée sécurité, référencée dans la documentation et les preuves historiques.
- protections communes : utilisateur non-root, cap_drop ALL, no-new-privileges, read-only, tmpfs, volume dédié, réseau interne.
- risks si suppression : historiques peuvent pointer vers ce fichier et certaines preuves se réfèrent à celui-ci.

Recommandation : conserver `docker-compose.security.yml` comme référence de sécurité et réutiliser le même contenu dans `compose.yaml` plutôt que supprimer.

## 2. Alias Python historiques

- `quantar_docker_task.py`, `quantar_task_manager.py`, `quantar_task_runtime.py`, `quantar_task.py`, `quantar_docker_task.py` sont des alias de compatibilité (`from ... import *`).
- Ils sont importés par tests `test_quantar_real_task_runtime.py`.
- Le point d'entrée officiel reste `run_task_in_container` dans `quantar_service.py`.
- Suppression immédiate risque de casser les tests legacy et certaines applications consommatrices.

Recommandation : conserver les alias jusqu’à une migration explicite, puis signature de dépréciation et tests mis à jour.

## 3. Unification proposée

- `QuantarTaskService` orchestre les tâches et la persistance.
- `run_task_in_container()` est le chemin officiel pour l'exécution Docker.
- `ComposeService` sert à supervision et démarrage contrôlé.
- éviter de lancer `docker run` et `compose up` en parallèle pour la même tâche.

## 4. Sécurité

- HROT, gateway, persistance et annulation restent inchangés ;
- aucune autorisation ni permissions élargies ;
- aucune clé ni credential introduit.

## 5. Tests

- imports historiques présents ;
- aucune migration de code effectuée lors de cette phase.

## 6. Résultat

Aucune modification effectuée. La consolidation doit être faite progressivement avec tests de compatibilité.
