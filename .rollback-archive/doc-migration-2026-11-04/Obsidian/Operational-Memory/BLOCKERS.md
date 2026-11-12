# BLOCKERS — ETHAN

## B-01 — Réseau GitHub indisponible

- Statut : BLOCKED
- Effet : visibilité de `seclib/Ethan`, branches/tags et secrets distants non vérifiables.
- Source : `git ls-remote` et `gh auth status` le 2026-11-03.
- Action requise : environnement avec réseau et token GitHub valide.

## B-02 — Contradiction entre index Source A et Source B

- Statut : IN_PROGRESS
- Effet : comptage sessions incohérent (85 collectées vs 0 collectées / 87 doublons).
- Source : `_meta/INDEX_ODSIDIAN_SOURCE.md` et `_meta/odsidian-metadata/COVERAGE-REPORT.md`.
- Action requise : réconcilier manuellement en conservant les deux sources.

## B-03 — Représentation fragmentée de l'archive Cline volumineuse

- Statut : IN_PROGRESS
- Effet : l'archive unifiée de 8 748 269 octets et ses cinq fragments peuvent représenter la même conversation, mais aucune équivalence bit à bit n'est établie.
- Source : `_meta/odsidian-metadata/PARTS-INDEX.md`.
- Action requise : comparaison indépendante, hors migration.

## B-04 — Statut applicatif partiellement inconnu

- Statut : UNKNOWN
- Effet : cette migration n'a pas exécuté de tests applicatifs ETHAN.
- Source : session 2026-11-02 indique tests WebUI réussis à cette date.
- Action requise : rerun ciblé seulement si une implémentation le justifie.

## B-05 — Nom et chemin définitifs de la mémoire

- Statut : PLANNED
- Effet : le dossier existant est `Odsidian`, la destination demandée est `Obsidian` (avec `b`).
- Source : inventaire et warrants.
- Action requise : accord humain avant réorganisation.
