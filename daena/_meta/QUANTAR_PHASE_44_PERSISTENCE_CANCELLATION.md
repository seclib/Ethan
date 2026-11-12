# QUANTAR — Persistance durable, récupération et annulation (Phase 44)

Date : 2026-11-04
Statut : implémenté et testé avec tests contrôlés — PARTIALLY_VALIDATED

## 1. Architecture de persistance

- Sérialisation JSON des tâches dans `{workspace_root}/{task_id}/state.json`.
- Écritures atomiques via fichier `.tmp` puis `replace`.
- Références `result_reference` et `log_reference` associées à la tâche.
- Pas de stockage de secrets dans les métadonnées.

## 2. Machine à états

États actuels :

`PREPARED`, `QUEUED`, `STARTING`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`, `CANCEL_REQUESTED`, `INTERRUPTED`, `RECONCILING`.

Règles appliquées :
- une tâche inachevée chargée après redémarrage devient `INTERRUPTED`, jamais `COMPLETED`.
- `COMPLETED` n'est défini qu'après écriture du résultat.
- l'annulation ne déclare `CANCELLED` qu'après confirmation.

## 3. Récupération après redémarrage

- au chargement, les états persistants sont relus ;
- les états non terminaux sont convertis en `INTERRUPTED`;
- aucune relance automatique n'est déclenchée ;
- la réconciliation formelle est disponible via `reconcile_tasks()`.

## 4. Annulation réelle

- demande d'annulation → `CANCEL_REQUESTED` ;
- nettoyage du conteneur via `cleanup_container` ;
- si le cleanup est confirmé → `CANCELLED` ;
- sinon → `INTERRUPTED` avec erreur exploitable ;
- double annulation protégée par l'état final.

## 5. Concurrence

- un verrou service-level protège les transitions ;
- les tâches terminées/interrrompues ne sont pas relancées ;
- les annulations répétées sont idempotentes.

## 6. Tests exécutés

- `tests/core/test_quantar_service_phase36.py`
- `tests/core/test_quantar_real_task_runtime.py`
- `tests/core/test_quantar_security_phase37a.py`
- `tests/core/test_quantar_phase40.py`

Résultat : 11 passed.

Vérification supplémentaire de persistance effectuée manuellement : une tâche préparée puis chargée après réinstanciation est bien restaurée comme `INTERRUPTED`.

## 7. Limites

- pas de démonstration d'arrêt forcé réel ;
- pas de test Docker concurrent / réconciliation réelle ;
- pas de stockage distribué / base de données ;
- persistance filesystem locale uniquement.

## 8. Risques restants

- corruption `state.json` ;
- accès concurrent entre deux instances ETHAN ;
- credentials ou données sensibles à ne jamais persister ;
- annulation reportée mais conteneur réel non stoppé.

## 9. Critères de passage à la Phase 45

- test avancé d'annulation réelle ;
- test de redémarrage conteneur ;
- mutliples instances ETHAN coordonnées ;
- validations de persistance fichier.

Statut : `PARTIALLY_VALIDATED`.
