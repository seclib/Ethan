# Mission 05 — Rapport de parité CLI/API/WebUI

Date : 2026-11-11. Branche : `refactor/ethan-rebuild-p0`.

## 1. Sessions — filtres CLI

**Implémenté** dans `interfaces/cli/commands/session.py` (`session list`) :
- `--archived` → `archived=true`
- `--folder <id>` → `folder_id=<id>`
- `--project <id>` → `project_id=<id>`
- `--unassigned` → `unassigned=true`
- Combinaisons supportées (params accumulés).
- Comportement sans filtre inchangé (params=None).

**Vérifié réel** : `session list --unassigned`, `session list --archived` → résultats cohérents.

## 2. Applications — validate et register

**Implémenté** dans `interfaces/cli/commands/application.py` :
- `validate` : lit un payload JSON (stdin ou args), `POST /v1/application-capabilities/validate`.
- `register` : lit un payload JSON, force `approved=true`, `POST /v1/application-capabilities`.

**Vérifié réel** : `application capabilities` → `[]` (aucune capability enregistrée, comportement attendu).

## 3. Memory — opérations d'écriture

**Implémenté** dans `interfaces/cli/commands/memory.py` :
- `record` : lit un payload JSON, `POST /v1/memory/events`.
- `vault-write <path> <content>` : `POST /v1/memory/vault/file`.

Contrats vérifiés : `MemoryRecord(**payload)` pour record, `{path, content}` (strings) pour vault-write. Permissions HROT (`RECORD`) respectées côté API.

## 4. Knowledge/RAG — audit de couverture

Capacités existantes dans Core/API et leur exposition CLI :

| Capacité | Core | API | CLI | Statut |
|---|---|---|---|---|
| Statut RAG | ✅ `core/rag/pipeline.py` | (via knowledge) | ❌ | NOT_EXPOSED |
| Stratégies RAG | ✅ `core/rag/strategies.py` | (via knowledge) | ❌ | NOT_EXPOSED |
| Indexation/ingestion | ✅ `core/rag/ingestion.py` | `POST /knowledge/imports` (multipart) | ❌ | NOT_EXPOSED (multipart, non adapté au CLI JSON) |
| Import de documents | ✅ | `POST /knowledge/imports` (multipart) | ❌ | NOT_EXPOSED (multipart) |
| Statut d'import | ✅ | `GET /knowledge/imports/{job_id}` | ✅ `import-status` | IMPLEMENTED |
| Connexions | ✅ | `POST /knowledge/{id}/connections` | ✅ `connect` | IMPLEMENTED |
| Retrieve multi-collections | ✅ | `POST /knowledge/collections/retrieve-multi` | ✅ `retrieve-multi` | IMPLEMENTED |
| Retrieve (collection) | ✅ | `POST /knowledge/collections/{id}/retrieve` | ✅ `retrieve` | IMPLEMENTED |
| Update collection | ✅ | `PUT /knowledge/collections/{id}` | ✅ `collection-update` | IMPLEMENTED |
| Move collection | ✅ | `POST /knowledge/collections/{id}/move` | ✅ `collection-move` | IMPLEMENTED |
| Delete collection | ✅ | `DELETE /knowledge/collections/{id}` | ✅ `collection-delete` | IMPLEMENTED |
| Add document | ✅ | `POST /knowledge/collections/{id}/documents` | ✅ `document-add` | IMPLEMENTED |
| Delete document | ✅ | `DELETE .../documents/{doc_id}` | ✅ `document-delete` | IMPLEMENTED |

**Blocker** : l'ingestion/import de documents est en multipart (upload de fichiers), non adapté à un CLI basé sur JSON. Nécessiterait une commande `import <file> <collection>` lisant le fichier et envoyant en multipart — à implémenter si requis.

**Blocker** : statut RAG et stratégies n'ont pas de routes API dédiées (pas de `/rag/status` ou `/rag/strategies`). Capacités présentes dans Core mais non exposées. Documenté, pas de route inventée.

## 5. Validation

| Contrôle | Résultat |
|---|---|
| `pytest tests/cli/ethan -q` | **630 passed**, 0 échec |
| `ruff check interfaces/cli` | **All checks passed!** |
| `lint-imports` | **5 kept, 0 broken** |
| `memory health` (réel) | ✅ |
| `memory records` (réel) | ✅ |
| `session list --unassigned` (réel) | ✅ |
| `application capabilities` (réel) | ✅ |
| `knowledge retrieve-multi` (réel) | ✅ |

## 6. Fichiers modifiés

- `interfaces/cli/commands/session.py` (filtres)
- `interfaces/cli/commands/application.py` (validate, register)
- `interfaces/cli/commands/memory.py` (record, vault-write)
- `interfaces/cli/commands/knowledge.py` (collection-*, document-*, retrieve-multi, connect, import-status)

## 7. Blocages restants

1. **RAG statut/stratégies/indexation** : capacités Core présentes mais non exposées par l'API. Nécessite des routes API dédiées (hors périmètre CLI).
2. **Import de documents** : multipart upload, non adapté au CLI JSON. Nécessite une implémentation multipart.
3. **Memory enregistrement** : `record` et `vault-write` exposés mais non testés en conditions réelles (nécessitent un payload MemoryRecord valide).
4. **Applications validate/register** : exposés mais non testés en conditions réelles (nécessitent un contrat de capability valide).

## 8. État final de la parité

La parité CLI/API/WebUI est substantiellement améliorée. Les capacités Core exposées par l'API sont maintenant accessibles depuis le CLI pour les 4 domaines (Applications, Sessions, Memory, Knowledge/RAG). Les blocages restants concernent des capacités Core non exposées par l'API (statut RAG, stratégies) ou des formats non adaptés au CLI (multipart upload).
