# QUANTAR — Preuves runtime Docker et concurrence (Phase 46B)

Date : 2026-11-04
Statut : validation runtime partielle et preuves multi-instance obtenues

## 1. Environnement testé

- Image : `quantar-runtime:real-task`
- Utilisateur : `1000:1000`
- Réseau : `none` dans les commandes de test ;
- aucun montage sensible ;
- aucune analyse financière réelle.
- versions : Python 3.12 dans l'image, Docker 26.1.5.

## 2. Démonstration d'arrêt normal

Scénario `phase46b-normal2` :

- conteneur démarré avec `sleep 300`;
- conteneur associé à un workspace Quantar ;
- demande d'annulation passée par le service ;
- arrêt effectif confirmé ;
- état persistant `CANCELLED`;
- conteneur absent après traitement (`docker inspect`: No such object).

Conclusion : arrêt normal et confirmation de l'arrêt validés runtime.

## 3. Démonstration d'arrêt forcé

Scénario `force-test2` :

- processus de test ignorait `SIGTERM` via `trap "" TERM`;
- `docker stop -t 2` a excédé le délai de grâce ;
- arrêt final confirmé en environ 2,2 secondes ;
- état final `exited`.

Conclusion : l'arrêt forcé fondé sur `docker stop`/`SIGKILL` est réalisable et observable.

## 4. Démonstration multi-instance

Scénario `multi-1` :

- deux processus Python indépendants utilisant le même workspace et le même `task_id`;
- chacun a chargé `QuantarTaskService`;
- chacun a tenté d'annuler la même tâche contenant un conteneur actif ;
- aucun crash ;
- aucun fichier JSON corrompu ;
- état final persistant `CANCELLED`;
- nouveaux ID d'exécution conservés et reprise possible uniquement après interruption.

Observations :

- les deux processus ont retourné `CANCELLED`;
- un seul processus a effectivement réalisé l'arrêt ;
- l'autre a observé et persisté l'état déjà confirmé ;
- libération du verrou effectuée (retour propre).

## 5. Preuves résumées

- service associé à conteneur actif : oui ;
- annulation normale : oui ;
- arrêt forcé : oui ;
- multi-instance : oui, avec deux processus ;
- persistance finale : `CANCELLED`.

## 6. Limites restantes

- aucun test multi-processus de `RECONCILING` ;
- aucune démonstration automatique dans le pipeline pytest ;
- aucun tests héréditaire d'arrêt normal et forcé intégrés dans la suite ;
- aucune preuve d'annulation d'un conteneur réellement en cours de `TradingAgentsGraph.propagate()`.

## 7. Risques résiduels

- coordinating deux processus ETHAN reste du fait de la logique de concurrence et du scheduler ;
- la latence Docker peut dépasser le délai configuré ;
- les logs peuvent conserver des données sensibles si TradingAgents en écrit.

## Statut Phase 46B

Partiellement validé runtime. Le mécanisme Docker et le verrou fichier sont démontrés par des conteneurs dédiés. Reste à intégrer ces scénarios de manière reproductible avec des tests durables et une tâche Quantar réellement en exécution.

Statut global Quantar conservé : `PARTIALLY_VALIDATED`.
