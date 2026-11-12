# QUANTAR — Audit de consolidation des mécanismes de lancement

Date : 2026-11-04
Statut : PARTIALLY_VALIDATED (audit, no migration)

## 1. État actuel

Le dépôt contient plusieurs mécanismes cohérents mais superposés :

- `QuantarTaskService` dans `core/applications/quantar_service.py` pour les tâches, la persistance et l'exécution one-shot.
- `ComposeService` réutilisé par `core/plugins/quantar.py` pour le cycle de vie Compose optionnel.
- Un runner Docker one-shot dans `examples/quantar/quantar_task_runner.py`.
- Des API Web quantar dans `interfaces/api/routers/quantar.py`.
- Un état d'intégration applicative dans `core/applications/quantar_integration.py`.

Quantar n'est pas référencé dans `docker-compose.yml` principal.

## 2. Points d'entrée susceptibles de lancer Quantar

1. WebUI → `POST /v1/quantar/tasks` + `/tasks/{id}/run?use_docker=true`
2. WebUI → `POST /v1/quantar/lifecycle/start`
3. CLI / services internes → ComposeService Quantar
4. Direct `docker compose -f examples/quantar/compose.yaml` via terminal
5. Direct `docker run` construit par `run_task_in_container()`
6. Runner `examples/quantar/quantar_task_runner.py` dans une image

## 3. Générations et statut

| Mécanisme | État | Commentaires |
|---|---|---|
| `run_task_in_container` direct | Actif et utilisé | Chemin recommandé pour one-shot |
| `ComposeService` Quantar | Présent / non démontré actif | `not_installed` par défaut |
| `quantar-task` compose service | Présent | Point d'entrée runner direct; pas de port de service |
| HROT Provider Gateway | Expérimental | Non connecté |
| Persistance JSON | Implémenté/testé | Per-task workspace |
| Réconciliation/reprise | Implémenté/testé contrôlé | Non démontré en runtime |
| Annulation réelle | Implémenté/testé partiellement | Arrêt gracieux/forcé démontré isolé |

## 4. Conflits détectés

- Le service Compose de Quantar est conçu pour lancer le runner one-shot et sortir immédiatement.
- Le statut Compose `not_installed` n'est pas un signal suffisant pour l'utilisateur.
- Le compose service et la tâche service cohabitent, mais ne sont pas orchestrés ensemble.
- Les conteneurs one-shot peuvent être terminés alors que le tableau de bord ne reflète pas exactement cet état.
- La gateway HROT n'est pas intégrée au runtime.

## 5. Dépendances

- `examples/quantar/compose.yaml`
- `core/applications/quantar_service.py`
- `core/plugins/quantar.py` (`ComposeService`)
- `interfaces/api/routers/quantar.py`
- `examples/quantar/Dockerfile` et `quantar_task_runner.py`
- image `quantar-runtime:latest`

## 6. Plan recommandé

1. Garder `run_task_in_container()` comme chemin officiel one-shot pour les tâches réelles.
2. Conserver `ComposeService` pour le démarrage manuel ou piloté depuis le WebUI, mais l'associer explicitement au mode one-shot.
3. Harmoniser les états returned (`APPLICATION_READY`, `TASK_RUNNING`, `APPLICATION_STOPPED`) via le runtime service.
4. Ne pas ouvrir de port réseau.
5. Améliorer la réconciliation des containers absents/completed.
6. Ne jamais relancer automatiquement au démarrage d'ETHAN sans human authorization.

## 7. Éléments à conserver

- runner et image canonique ;
- persistance JSON et réconciliation ;
- sécurité HROT et isolation ;
- annulation et arrêt forcé ;
- tests et historiques.

## 8. Éléments à vérifier ou migrer

- intégration runtime WebUI Compose ;
- documentation du mode one-shot ;
- les endpoints lifecycle Quantar ;
- la supervision d'état après arrêt.

## 9. Tests nécessaires

- lifecycle complet par Compose ;
- réconciliation après disparition ;
- double demande ;
- préservation des données ;
- tests de refus réseau.

## 10. Ordre recommandé

1. Audit des contrats.
2. Clarification des états.
3. Mise à jour WebUI minimale.
4. Implémentation interprocessus et lifecycle pour one-shot.
5. Validation réelle contrôlée.
6. documentation et clôture.

## 11. Risques résiduels

- plusieurs API peuvent piloter le même conteneur en parallèle;
- les anciens scripts peuvent référencer des chemins ou noms de conteneurs obsolètes ;
- absence de vrais end-to-end ;
- tests d'annulation et containers réels encore manquants.

## Statut

Audit non destructif terminé. Aucune modification effectuée.
