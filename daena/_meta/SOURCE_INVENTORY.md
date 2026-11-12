# SOURCE_INVENTORY — Mémoire technique ETHAN

## Sources traitées

| Source | Chemin | Type | Fichiers | Taille | Git | Statut |
|---|---|---|---:|---:|---|---|
| Source principale | `/home/fatsio/AI/Ethan` | dépôt Git actif | 2722 fichiers suivis | 6.3 Go dont dépendances et builds | oui | intact |
| Source A | `/home/fatsio/ethan-knowledge` | export externe local | 90 | 71 Mo | non | intact |
| Source B | `/home/fatsio/AI/Ethan/Odsidian` | archive locale intégrée | 104 | 82 Mo | oui sous `/home/fatsio/AI/Ethan` | intact |
| Mémoire opérationnelle source | `/home/fatsio/AI/Ethan/docs/memory` | documentation interne | 5 | 28 Ko | modifications locales non commitées | intact |
| Candidate publique | `/home/fatsio/AI/Ethan-Public-Candidate` | candidate non commitée | 3299 | 40 Mo | dépôt non initialisé | non modifiée |

## Méthode de consolidation

1. Source B a été copiée comme hiérarchie primaire de référence.
2. Source A n'a apporté que les éléments dont la provenance ou le contenu était absent ou divergent dans Source B.
3. Les doublons exacts par SHA-256 n'ont pas été recopiés.
4. Les divergences ont été conservées avec des noms horodatés ou des répertoires de provenance.
5. Les fichiers opérationnels ont été copiés dans `Operational-Memory/sources/` puis synthétisés sans écraser d'information plus récente sans justification.
6. Aucune source n'a été supprimée ni modifiée.

## Résultats de comparaison

| Catégorie | Nombre |
|---|---:|
| Fichiers combinés analysés | 194 |
| Doublons exacts consolidés | 84 |
| Fichiers au même chemin avec SHA différent | 4 |
| Chemins propres à Source A | 2 |
| Chemins propres à Source B | 16 |
| Éléments uniques importés de Source A | 6 |

## Les six éléments uniques préservés

| Élément | Provenance Source A | Taille | Préfixe SHA-256 (12 car.) |
|---|---|---:|---|
| Archive Cline unifiée | `01-Archives/cline/2026-08-13/1786588790163.md` | 8748269 | `eafb96a6075b297f1f73dae4c6cc3399` |
| Index Source A | `INDEX.md` | 8527 | `e984ebdeba61` |
| Synthèse Cline ancienne | `06-Syntheses/by-agent/cline-summary.md` | 6746 | `f70f4790b5e9` |
| Synthèse Codex ancienne | `06-Syntheses/by-agent/codex-summary.md` | 188 | `d7abd4575d68` |
| Synthèse Copilot ancienne | `06-Syntheses/by-agent/copilot-summary.md` | 448 | `c8c7e2dc349d` |
| État de synchronisation Source A | `_meta/sync-state.json` | 22969 | `83d8b1d4` |

Les valeurs ci-dessus sont des préfixes de 12 caractères. Les empreintes complètes des éléments uniques sont disponibles via `sha256sum` sur les fichiers sources. Les colonnes ci-dessus présentent un préfixe et les tailles vérifiées.

## Classification des contenus dans la cible

### Archives

- Source principale de référence : Source B (`Odsidian`), copiée dans `Archives/Conversations/`.
- Archives fragmentées conservées telles quelles.
- Archive unifiée Cline Source A copiée dans `Archives/Conversations/from-ethan-knowledge/cline/2026-08-13/1786588790163.md`.
- Rapports d'archives copiés dans `Archives/Rapports-Agents/` si présent.

### Knowledge

- Synthèses canoniques Source B copiées dans `Knowledge/Syntheses/by-agent/`.
- Versions historiques Source A conservées avec suffixe de date.
- Documents `02-ETHAN`, `03-Procedures`, `04-Incidents-Solutions`, `04-Tests-et-Preuves`, `05-Decisions`, `05-Tests-Validations` copiés uniquement s'ils contiennent des fichiers.
- `INDEX_ETHAN_KNOWLEDGE.md` importe l'index Source A sous un nom distinct.

### Operational-Memory

- `PROJECT_STATE.md`, `DECISIONS.md`, `TASKS.md`, `BLOCKERS.md` ont été créés à partir de `docs/memory` et du dépôt.
- Les fichiers source originaux sont conservés sous `Operational-Memory/sources/docs-memory/`.
- Les métadonnées Source A sont conservées sous `Operational-Memory/sources/ethan-knowledge-meta/`.

### Métadonnées

- Métadonnées Source B conservées sous `_meta/odsidian-metadata/`.
- Audit et index Source B copiés sous `_meta/`.
- Rapport de migration et inventaire conservés dans `_meta/`.

## Traçabilité des résultats

Les provenances possibles sont :

- `SourceA` : `/home/fatsio/ethan-knowledge`
- `SourceB` : `/home/fatsio/AI/Ethan/Odsidian`
- `SourceDocsMemory` : `/home/fatsio/AI/Ethan/docs/memory`
- `SourceInventory` : `/tmp/ETHAN_RESOURCES_INVENTORY.md`
- `SourcePhase2` : `/tmp/ETHAN_PHASE2_SEPARATION_PLAN.md`
- `SourceMergePlan` : `/tmp/ETHAN_OBSIDIAN_MERGE_PLAN.md`

## Problèmes résolus pendant la migration

- Les index Source A et Source B sont contradictoires ; ils ont été conservés comme deux représentations et synthétisés dans cette documentation.
- L'archive volumineuse Cline existe à la fois sous forme unifiée et fragmentée ; les deux formes ont été conservées.
- Les synthèses d'agents divergent par horodatage et contenu ; les deux versions ont été conservées.
- Les fichiers `sync-state.json` proviennent de deux emplacements relatifs différents ; ils ont été conservés sous des noms distincts.
- Les artefacts `.bak` n'ont pas été inventoriés comme documents canoniques.

## Limites connues

- Les archives volumineuses n'ont pas été re-découpées dans cette étape.
- `ethan-knowledge` n'a pas été entièrement recopié, conformément à la règle de consolidation des doublons.
- Les images, binaires, dépendances et builds ne sont pas inclus.
- Les références `Odsidian` dans le dépôt principal n'ont pas été modifiées, car l'orthographe définitive du dossier cible est une décision humaine encore ouverte.
- Aucun test applicatif ETHAN n'a été exécuté pendant cette migration documentaire.

## Snapshots de sources

- `_meta/source-snapshots/ethan-knowledge/` contient les versions Source A des éléments conflictuels.
- `_meta/source-snapshots/odsidian/` contient les versions Source B des éléments conflictuels.
- Ces snapshots sont des références traçables et non des fichiers de travail.
