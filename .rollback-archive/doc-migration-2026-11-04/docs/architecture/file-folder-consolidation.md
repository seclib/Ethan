# File/Folder Consolidation — Architecture

> **Statut : FIXED** — consolidation multi-dossiers ajoutée au-dessus du
> système de dossiers virtuels existant (`core/folders`), sans second pipeline.

---

## 1. Modèle de stockage (existant, non remplacé)

Les dossiers ETHAN sont **virtuels** : un dossier est un enregistrement
(`folders`), le classement des ressources est une **relation**
(`folder-memberships`). Une ressource (knowledge, collection, skill) reste
possédée par son manager Core d'origine ; le dossier n'est qu'un contenant
logique, avec **multi-membership** (une ressource peut vivre dans plusieurs
dossiers). Aucune donnée n'est dupliquée — seule la relation s'ajoute.

- Domaine Core : `core/folders/manager.py` (`FolderManager`)
- Store : `CoreRecordStore` (PostgreSQL durable + Redis + fallback mémoire)
- Événements : `FOLDER_*` dans `core/ethan_types/event.py` (mutations publiées
  sur le bus)
- Types de ressources classables : registre ouvert (défaut : knowledge,
  collection, skill) — `add_provider()`

## 2. Opérations de consolidation (ajoutées)

| Opération | Sémantique | API | Rapport |
|-----------|-----------|-----|---------|
| **Merge folders** | Re-classe le contenu des sources vers la cible ; sources supprimées uniquement si `remove_sources` explicite | `POST /v1/folders/merge` | `operation_id`, `status`, `attached`, `skipped`, `removed_sources`, `errors` |
| **Copy resources** | Ajoute la cible aux dossiers des ressources, sans retirer les classifications existantes (multi-membership) | `POST /v1/folders/copy-resources` | idem |
| **Move resources** | La cible devient l'unique dossier de chaque ressource (detach des autres) | `POST /v1/folders/move-resources` | idem |

Différences explicites (jamais confondues) :
- **Move** : modifie l'ensemble des dossiers d'une ressource (relation).
- **Copy** : ajoute une relation (la ressource existe dans source ET cible).
- **Merge** : opération au niveau dossiers — transfère le contenu des sources
  vers la cible (ressource unique par id ; doublons inter-sources dédupliqués).
- **Import/Index** : délégué au pipeline Knowledge/RAG officiel — la
  consolidation ne crée pas d'ingestion parallèle.

## 3. Gestion des conflits

Aucun conflit de nom n'est possible : les ressources sont identifiées par
`(resource_type, resource_id)` et la relation est **idempotente**
(`attach_resource`). Une ressource déjà classée dans la cible est comptée
`skipped` — jamais écrasée. Le seul « échec » est une ressource inexistante
(fail-closed) ou une source inexistante : l'erreur est **rapportée** dans
## 4. Atomicité, rollback et rapport d'opération

Chaque opération retourne un **rapport** jamais masqué :

```json
{
  "operation_id": "a1b2c3d4e5f6",
  "operation": "merge",
  "status": "partially_completed",
  "attached": 12,
  "moved": 0,
  "skipped": 2,
  "errors": ["skill:ghost: skill ghost not found"],
  "target_id": "...",
  "sources": ["...", "..."],
  "removed_sources": []
}
```

- `completed` : tout a réussi.
- `partially_completed` : au moins une réussite et une erreur (jamais déclaré
  completed).
- `failed` : aucune réussite.
- Rollback : les relations sont idempotentes et le rapport reflète l'état
  réel — reclasser en sens inverse restaure l'état. Les sources ne sont
  supprimées qu'**après** le transfert et uniquement sur `remove_sources`
  explicite.

## 5. Isolation et sécurité

- Toutes les mutations passent par `FolderManager` avec validation
  `_require_folder` / `_require_resource` (fail-closed : jamais de relation
  fantôme).
- Routes protégées par `Permission.MEMORY` (`require_permission`).
- Ressource inexistante → error rapportée, jamais de suppression silencieuse,
  jamais d'écrasement (identification par id).
- Aucun accès arbitraire au filesystem : la consolidation porte sur des
  **relations métier**, pas sur des chemins.

## 6. Intégration Projects / Knowledge / RAG

- **Knowledge/RAG** : le classement d'un document/collection dans un dossier
  est une relation ; l'indexation RAG reste celle du pipeline officiel
  (`core/rag`). La consolidation ne réindexe pas, ne recrée pas d'ingestion.
- **Projects** : retirer une ressource d'un dossier ne supprime jamais la
  ressource ; l'association projet reste gérée par `core/projects`.

## 7. UI WebUI

- Bouton **« Fusionner des dossiers… »** (sidebar Folders) → dialogue sources
  multiples + cible unique + `remove_sources` optionnel.
- **Sélection multiple** dans la liste des ressources → barre d'actions
  **Copier / Déplacer** vers une cible.
- Rapport d'opération affiché (succès / partiel / échec).
- Toute la logique reste côté Core ; le WebUI transmet des intentions.

## 8. Extension

Nouveau type de ressource : `manager.add_provider(type, provider)` →
immédiatement classable / copiable / déplaçable / fusionnable, sans
modification de la consolidation.

## 9. Tests

- Backend : `tests/test_folders_consolidation.py` — 11 tests (merge, merge +
  remove_sources, rejet cible-source, source inconnue, skip idempotent,
  partiel rapporté, copy multi-membership, copy idempotent, move unique,
  move partiel, move total failed).
- Frontend : `tests/unit/folders/merge-folders-dialog.test.tsx` — 4 tests
  (bouton désactivé, args onMerge, radios désactivées, removeSources).
`errors`, l'opération reste `partially_completed`.