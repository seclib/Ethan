# Rapport de migration documentaire ETHAN — 2026-11-04

Statut : Phase C exécutée (contrôlée), validation complémentaire requise

## 1. Résumé

- Migration contrôlée exécutée.
- Aucun document original n’a été supprimé (sauvegarde dans `.rollback-archive/doc-migration-2026-11-04/`).
- Manifeste complet : `Obsidian/_meta/DOCUMENTATION_MIGRATION_MANIFEST_2026-11-04.csv` (352 entrées).
- Nombre de mouvements effectués : 352.
- `docs/` restant : 60 fichiers Markdown à vocation utilisateur.
- Rapport de collision : `Obsidian/_meta/COLLISION_IDENTIFIER_TABLE_2026-11-04.md`.

## 2. Structure cible appliquée

- `Obsidian/Architecture/ADR/`
- `Obsidian/Architecture/ESR/`
- `Obsidian/Architecture/ASR/`
- `Obsidian/Architecture/System/`
- `Obsidian/Architecture/System-Reviews/`
- `Obsidian/Engineering/API/`
- `Obsidian/Engineering/Audits/`
- `Obsidian/Engineering/Benchmarks/`
- `Obsidian/Engineering/BUILD/`
- `Obsidian/Engineering/Development/`
- `Obsidian/Engineering/Misc/`
- `Obsidian/Engineering/Plans/`
- `Obsidian/Engineering/Runbooks/`
- `Obsidian/Engineering/Schemas/`
- `Obsidian/Engineering/Security/`
- `Obsidian/Engineering/Specs/`
- `Obsidian/Engineering/Tests-Validation/`
- `Obsidian/Engineering/WebUI/`

## 3. Fichiers déplacés

Les déplacements sont listés intégralement dans le manifeste. Répartition principale :

- 347 documents provenant de `docs/` vers Obsidian ;
- 3 centralisations depuis `Obsidian/Knowledge/Architecture/` vers `Obsidian/Architecture/`.

Documents restés dans `docs/` : présentation, getting-started, user-guide, tutorials, showcase, plugins, webui, learning, assets, includes, javascripts, stylesheets, overrides et pages publiques.

## 4. Collisions traitées

- `ADR-1013` : frame-fork et knowledge-task-lifecycle conservés avec slugs distincts
- `ADR-1014` : frame-service-integration et retrieval-permission-scope conservés avec slugs distincts
- `ESR-014` : frame-fork et knowledge-observability conservés avec slugs distincts

Aucune renumérotation automatique n’a été appliquée.

## 5. Réconciliation PROJECT_STATE

- Fichier canonique : `Obsidian/Operational-Memory/PROJECT_STATE.md`
- L’historique détaillé de `docs/memory/PROJECT_STATE.md` a été conservé sous forme d’annexe.
- Les deux originaux ont été sauvegardés dans `.rollback-archive/doc-migration-2026-11-04/`.

## 6. Liens et références

- Remplacement des chemins absolus et relatifs touchés par les déplacements effectué par lots.
- Les liens qui ne pointent plus vers des cibles existantes restants sont pour l’essentiel des références préexistantes (`api-reference/ethan`, placeholders dans showcase, liens temporaire `/tmp/...`, liens relatifs obsolètes dans `INDEX`).
- Lien Obsidian vers `Knowledge/Architecture/ADR-EM-001` corrigé vers `Architecture/ADR/`.

## 7. Décisions appliquées

- `plugins/`, `webui/`, `learning/`, `showcase/` ont été examinés individuellement : seuls les rapports internes évidents (`webui/open-webui-*`) ont été déplacés.
- Les ADR, ESR et ASR sont regroupés dans `Obsidian/Architecture/`.
- Les documentations techniques restantes sont conservées dans `Obsidian/Knowledge/`.
- La politique Git d’Obsidian/ n’a pas été modifiée.
