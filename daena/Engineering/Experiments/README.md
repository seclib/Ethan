# Experiment Tracking & Failure Learning — ETHAN

Ce registre documente les tentatives techniques importantes, réussies, échouées, partielles ou remplacées.

Il ne s'agit pas d'un second stockage applicatif. Il complète la mémoire documentaire existante d'ETHAN et réutilise les conventions d'identité, d'ADR, de runbooks et d'incidents.

## Règles fondamentales

1. Une tentative historique n'est jamais écrasée.
2. Chaque nouvelle approche reçoit un nouvel `Attempt ID`.
3. Une tentative peut être remplacée par une autre, mais reste consultable.
4. Le statut `WORKING` n'est accordé qu'avec preuve vérifiable.
5. Les tentatives échouées sont conservées pour empêcher la répétition.

## Statuts

- `ATTEMPTED` : tentative réalisée, résultat pas encore établi.
- `WORKING` : critères de réussite démontrés avec preuve.
- `FAILED` : critères de réussite non atteints.
- `PARTIAL` : certains critères atteints, d'autres non.
- `SUPERSEDED` : approche remplacée par une autre.

## Anti-répétition

Avant de reprendre une approche déjà essayée :

1. Rechercher les expériences similaires.
2. Lire leurs résultats et causes d'échec.
3. Comparer les conditions actuelles avec les conditions antérieures.
4. Justifier toute nouvelle tentative.
5. Signaliser le risque de répétition si les conditions n'ont pas changé et qu'aucune nouvelle hypothèse n'est apportée.

Une nouvelle tentative reste possible si le contexte a réellement changé.

## Documents liés

- Incident : pour un blocage réel ou une production dégradée.
- Leçon apprise : pour un enseignement généralisable.
- Règle de prévention : pour une contrainte à respecter.
- ADR : pour une décision architecturale durable.
- Runbook : pour l'exploitation.
- Recommandation : pour une direction future.

Ces documents restent distincts et sont liés aux tentatives correspondantes.


## Relation avec ECLL

- Les experiment records dans ce dossier sont l'implémentation documentaire du cycle ECLL.
- Voir `../ECLL/08-ECLL-Index.md`.
