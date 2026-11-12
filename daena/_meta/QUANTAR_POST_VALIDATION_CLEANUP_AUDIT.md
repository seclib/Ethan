# QUANTAR — Audit de consolidation post-validation

Date : 2026-11-04
Statut : audit exclusif, aucune modification effectuée

## 1. État constaté

- Image active : `quantar-runtime:latest` (`dc8f2c77c463`)
- Volume persistant : `quantar_quantar_task_data` (task data bind indirect)
- Volume ancien Compose : `quantar_quantar_data`
- Réseau : `quantar_ethan_quantar_isolated` (bridge isolé)
- Conteneur restant : `quantar-task` (Exited (1))

## 2. Mécanismes actifs

- `run_task_in_container()` via `docker compose run --rm`
- `QuantarTaskService` et persistance task JSON
- `QuantarProviderBridge` et gateway simulé
- HROT one-shot workflow
- `QuantarCreateContainer` ne contient pas de daemon long-running

Mécanismes anciens :
- wrappers `quantar_docker_task.py`, `quantar_task_manager.py`, `quantar_runtime.py`, `quantar_task.py` (alias only)
- Compose one-shot avec pas de contrôleur persistant

## 3. Conflits potentiels

- plusieurs alias pointent vers le même service, ce qui peut masquer l'origine ;
- Compose `quantar-task` avec volume `quantar_quantar_task_data` while service workspace is `.quantar-tasks` ;
- double démarrage possible si WebUI et terminal partent ensemble ;
- état `installed_stopped` est heuristique, pas une preuve de service ;
- accumulation de volumes unused et d'un conteneur Exited.

## 4. Classification

| Artefact | Emplacement / ID | Fonction | Références | Risque | Décision |
|---|---|---|---|---|---|
| `run_task_in_container` | core/applications/quantar_service.py | lancement one-shot officiel | service, API | moyen | KEEP |
| `quantar_quantar_task_data` volume | Docker | données tâches compose one-shot | possible | moyen | KEEP / INVESTIGATE |
| `quantar_quantar_data` volume | Docker | protocole ancien composant Compose | probablement inutilisé | élevé | INVESTIGATE |
| `quantar_ethan_quantar_isolated` network | Docker | isolation conteneur | compose | moyen | KEEP |
| `examples/quantar/compose.yaml` | repo | déploiement canonique | service | faible | KEEP |
| `docker-compose.security.yml` | repo | ancienne config sécurité | tests/documentation | moyen | CONSOLIDATE |
| aliases `quantar_docker_task.py` etc | repo | compatibilité | code/tests | faible | CONSOLIDATE |
| Provider Gateway | repo | expérience et gate | unit tests | moyen | PRESERVE_ARCHIVE |
| rapports Phase Quantar /meta | repo | audit | vivant | faible | PRESERVE_ARCHIVE |

## 5. Plan proposé de nettoyage à venir

Phase future possible (pas exécutée ici) :
1. vérifier avec un grep par artefact;
2. déplacer les doublons de documentation vers Obsidian ;
3. unifier les alias vers `quantar_service.py` via deprecation progressive ;
4. décider du volume `quantar_quantar_data` après inspection de ses fichiers via `docker volume` ;
5. ne supprimer l'aucun volume tant qu'une vérification n'a pas été faite.

Ordre recommandé :
1. Vérifier logs et état du conteneur restant.
2. inspecter le volume ancien (mount ro).
3. supprimer l'alias unique une fois validé.
4. documenter explicitement la transition.

## 6. Stratégie de rollback

Toute proposition future peut être réversible :
- code aliases restent en place jusqu'à décision;
- anciens documents sont préservés;
- images supprimées peuvent être reconstruites avec leur Dockerfile;
- volumes ne sont pas touchés pendant cet audit;
- conteneur `quantar-task` Exited n'est pas supprimé dans cette phase.

## 7. validations nécessaires après nettoyage

- commands de configuration Quantar;
- tests unitaires Quantar;
- runtime état API;
- logs ;
- contrôle absence de secret;
- preuve HROT et task path.

## Principe

Aucun nettoyage n'est légitime sans ses preuves et sans conservation de la sauvegarde initiale.

Statut : PARTIALLY_VALIDATED (audit uniquement)
