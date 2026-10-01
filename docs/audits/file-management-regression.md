# File Management Regression — Audit & Correction

> **Statut final : FIXED** — consolidation file/folder ajoutée, aucun second
> pipeline.

---

## 1. Symptôme

Les dossiers et fichiers ne pouvaient pas être consolidés : aucun workflow de
fusion de dossiers, pas de copie/déplacement multi-ressources. Seul un
déplacement unitaire (`move-resource`) existait, sans rapport d'opération.

## 2. Audit de l'existant (avant modification)

| Élément | Existant | Rôle |
| ------- | -------- | ---- |
| `core/folders/manager.py` | ✅ `FolderManager` | Dossiers virtuels, arborescence, relations multi-ressources (knowledge/collection/skill), attach/detach/move-resource, delete avec re-parentage |
| `interfaces/api/routers/folders.py` | ✅ CRUD + `move-resource` | Gateway HTTP vers Core, protégée `Permission.MEMORY` |
| `lib/api/folders.ts` | ✅ client complet | Tree, CRUD, resources, index |
| Composants WebUI | ✅ `folders-workspace`, `folder-tree`, `folder-dialogs`, `folder-contents`, `classify-dialog` | Cockpit d'organisation existant |
| **Merge / copy / move multi** | ❌ **Absent** | → ajouté |
| **Rapport d'opération** | ❌ **Absent** | → ajouté |

**Décision** : réutiliser le système de dossiers virtuels existant (relations,
jamais de duplication physique). Aucun second stockage, aucun second pipeline.

## 3. Cause du problème

La consolidation n'avait jamais été implémentée : le modèle relationnel le
permettait (multi-membership + `move_resource` unitaire) mais aucune opération
multi-ressources / multi-dossiers n'existait, ni côté Core, ni côté UI.

## 4. Implémentation

### Backend Core (`core/folders/manager.py`)

- `_operation_report()` : rapport standard (`operation_id`, `status`
  completed/partially_completed/failed, compteurs, `errors`).
- `merge_folders(folder_ids, target_id, remove_sources=False)` : re-classe le
  contenu des sources vers la cible ; doublons inter-sources dédupliqués ;
  source = cible rejeté ; sources supprimables APRÈS transfert (jamais les
  ressources).
- `copy_resources_to_folder(items, target_id)` : attache dans la cible SANS
  retirer les classifications existantes (multi-membership).
- `move_resources_to_folder(items, target_id)` : la cible devient l'unique
  dossier de chaque ressource.

### API (`interfaces/api/routers/folders.py`)

`POST /v1/folders/merge` · `POST /v1/folders/copy-resources` ·
`POST /v1/folders/move-resources` — toutes protégées `Permission.MEMORY`.
Déclarées **avant** les routes `/{folder_id}` (évite les collisions).

### WebUI

- `lib/api/folders.ts` : `FolderOperationReport`, `mergeFolders`,
  `copyResources`, `moveResources`.
- `hooks/use-folders.ts` : mutations avec toasts selon le statut du rapport
  (success / info partiel / error échec).
- `components/consolidate-dialogs.tsx` : `MergeFoldersDialog` (sources +
  cible + remove_sources), `DestinationPickDialog` (copy/move + rapport).
- `folder-contents.tsx` : sélection multiple (checkboxes) + barre
  Copier/Déplacer.
- `folders-workspace.tsx` : bouton « Fusionner des dossiers… ».
- `folder-tree.tsx` : `FolderDialogState` étendu avec `{ kind: "merge" }`.

## 5. Gestion des conflits

Aucun écrasement possible : identification par `(resource_type, resource_id)`,
relation idempotente. Ressource déjà présente → `skipped`. Ressource
inexistante → erreur listée. Sources = cible → 422. Aucune suppression sans
`remove_sources` explicite.

## 6. Rollback / atomicité

Rapport complet rend l'état traçable ; reclasser en sens inverse restaure.
Partiel jamais masqué (`partially_completed`).

## 7. Tests

| Suite | Résultat |
| ----- | -------- |
| `tests/test_folders_consolidation.py` (11) | ✅ 11/11 |
| Régression folders (`test_folders.py`, `test_folders_collections.py`) | ✅ 18/18 |
| Jest `merge-folders-dialog.test.tsx` (4) | ✅ 4/4 |
| Suite Jest complète WebUI | ✅ **13 suites / 42 tests** |
| `tsc --noEmit` | ✅ exit 0 |
| `npm run build` | ✅ exit 0 |

## 8. Problèmes restants

- Pas de « restore » (corbeille) — hors périmètre, non existant dans le modèle.
- L'opération `remove_sources` d'un merge est destructrice mais toujours
  explicite après confirmation UI.

## 9. Documentation

- `docs/architecture/file-folder-consolidation.md` (modèle, opérations,
  conflits, rollback, sécurité, intégrations, tests).