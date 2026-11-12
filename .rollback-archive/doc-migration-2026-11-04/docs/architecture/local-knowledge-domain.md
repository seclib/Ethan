# ETHAN — Local Knowledge Domain Contract

**Status**: Design (contracts only — no implementation).
**Depends on**: `docs/architecture/local-knowledge-storage-audit.md`.
**Rule**: the ETHAN root directory is the authoritative local storage boundary.
Core owns path resolution, validation, ownership, membership, ingestion,
indexing, retrieval and authorization. The WebUI never touches the filesystem.

---

## 1. Six Distinct Concepts

| # | Concept | Identity | Owner (Core module) | Persistence |
|---|---|---|---|---|
| 1 | **Physical file** | `file_id` (uuid) | `core/state/files.py` (`FileStore`) | bytes on disk `<root>/data/files/<aa>/<sha256>`; metadata record in `files` domain. Content-addressed (sha256) → natural dedup. |
| 2 | **Knowledge resource** | `resource_id` (uuid) | **NEW** `core/knowledge/resources.py` (`ResourceStore`) | record in new `resources` domain (JSONB). Logical object: document or image. |
| 3 | **Folder** | `folder_id` | existing `core/folders/manager.py` (`FolderManager`) | `folders` + `folder-memberships` domains (multi-membership, open type registry). |
| 4 | **RAG Collection** | `collection_id` | existing `core/knowledge/collections.py` (`KnowledgeCollectionManager`) | `knowledge-collections` domain; retrieval delegated to the shared `RAGPipeline`. |
| 5 | **Vector index** | *(not a first-class object)* | existing `core/rag/vector_store.py` (`RAGVectorStore` ABC) | backend-internal (`memory`/`chromadb`/`qdrant`); chunks keyed by `document_id == resource_id`. Surfaced only through status endpoints. |
| 6 | **Project association** | *(relation, not a copy)* | existing `core/projects` | `project_ids: []` references on the resource record; validated against `projects` domain. |

**Invariant — no duplication**: a resource appears exactly once in `resources`;
folders/collections/projects hold **relations only** (same rule as folders vs
domains adopted in ADR-3005). The physical file is stored once (content
addressing) and shared by any number of resources.

---

## 2. Knowledge Resource Model (authoritative record)

```jsonc
{
  "id": "uuid",
  "kind": "document | image",              // discriminator (extensible whitelist)
  "name": "user-facing label",             // unique per owner (case-insensitive)
  "description": "",
  "file_id": "uuid",                       // → PhysicalFile (1:1, required)
  "mime_type": "application/pdf",
  "size": 123456,
  "sha256": "hex",                         // copied from FileStore for cheap dedup checks
  "status": "imported | ingesting | ready | error",
  "error": null,                           // last ingestion error message (sanitized)
  "chunk_count": 0,                        // set by the shared RAG pipeline
  "owner_user_id": "user uuid",
  "folder_ids": [],                        // READ-VIEW only — truth lives in folder-memberships
  "collection_ids": [],                    // READ-VIEW only — truth lives in collection membership
  "project_ids": [],                       // validated references (projects domain)
  "metadata": {},                          // free-form, never secrets
  "created_at": "...", "updated_at": "..."
}
```

Notes:
- `folder_ids` / `collection_ids` in responses are **projections** assembled by
  Core from the owning relations; clients must not write them directly
  (membership changes go through the folder/collection endpoints — §4 of the
  API contract).
- `status` lifecycle: `imported` (bytes safe, not ingested) → `ingesting` →
  `ready` | `error`. Re-index flips `error`/`imported` back to `ingesting`.
- `kind=image` skips text ingestion (no extraction) → stays `imported` unless a
  future vision pipeline consumes it.

---

## 3. Relationships

```
PhysicalFile (data/files, content-addressed)
      │ 1
      │
      │ 0..1
KnowledgeResource ──*─── Folder            (folder-memberships — existing, multi)
      │      │
      │      └──*─── RAGCollection        (membership → ingest target)
      │
      └────*─── Project                   (project_ids refs, existence-validated)

RAGCollection ──*─── VectorIndex chunks    (document_id = resource_id, backend-internal)
```

Rules:
1. Deleting a PhysicalFile is forbidden while ≥1 resource references it
   (`file_id` refcount check in Core).
2. Deleting a resource: removes folder memberships, collection membership
   (purges its vectors via `RAGPipeline.delete_document`), keeps or deletes the
   physical file (`?delete_file=false` default — refcount decides).
3. Deleting a folder/collection/project **never** deletes resources (relations
   only, consistent with existing managers).
4. A resource in ≥2 collections is ingested once; retrieval scope is the union
   filter `document_ids` (existing pipeline behavior).

---

## 4. Filesystem Security Boundary (Core-enforced)

**Storage root**: `<ETHAN_ROOT>/data` — resolved exclusively by Core
(`runtime.data_dir` made effective; default `<repo>/data`, env override
`ETHAN_DATA_DIR`). Layout:

```
data/
├── files/<aa>/<sha256>     ← PhysicalFile bytes (content-addressed)
├── import/                 ← ONLY user-visible import zone (drop folder)
└── vectors/                ← vector backend persist_directory (chromadb local)
```

**Rules (all in Core, non-negotiable):**
1. The WebUI never sends absolute paths. Allowed inputs: `resource_id`,
   `file_id`, or a **relative path under `data/import/`** for local import.
2. Path resolution: `candidate = (root / rel).resolve()`; reject unless
   `candidate.is_relative_to(root_resolved)` (anti-traversal), reject symlinks
   whose target escapes the root, reject non-regular files and non-UTF-8 names.
3. Import zone whitelist: only `data/import/**` is walkable for `import-folder`;
   `import` (single) accepts multipart bytes OR a `data/import/` relative path.
4. Validation reuse: MIME whitelist + 50 MiB cap + sha256 dedup (same rules as
   the existing project-documents router → 413/415/409).
5. Authorization: `Permission.READ` for lists/metadata/status;
   `Permission.WRITE` (files/knowledge) for import/move/delete. Owner-scoped
   reads unless admin.
6. Responses never contain absolute paths or host layout — at most
   `storage: "local"` and `file_id`.
7. Logs contain resource ids and relative keys, never file contents or secrets.

---

## 5. Validation & Error Behavior (contract)

| Code | Condition |
|---|---|
| 400 | Malformed body; relative path escaping `data/import/`; absolute path supplied |
| 403 | RBAC denied (WRITE required for mutations); resource owned by another user |
| 404 | Unknown resource / folder / collection / project / file |
| 409 | Duplicate resource `name` for owner; sha256 already imported (`existing_resource_id` returned); delete while file refcount > 0 without `force` |
| 413 | File > 50 MiB (single) or bulk total cap exceeded |
| 415 | MIME not in whitelist (documents: md/txt/pdf/docx/csv/json; images: png/jpg/webp) |
| 422 | Invalid `kind`, invalid `retrieval_strategy`, `project_ids` referencing unknown projects |
| 503 | Storage root not initialized (`data_dir` unresolvable) |

Ingestion failures do **not** fail the import: the resource is kept with
`status="error"` + sanitized `error` message (existing pipeline contract);
re-index is a retry.

---

## 6. Database / Config Changes (documented — implementation deferred)

1. **No new SQL tables.** The generic `core_domain_records` (JSONB) absorbs the
   new `resources` domain (same as every post-005 domain).
2. **Config**: make `runtime.data_dir` effective in `core/config/loader.py`
   (default `<repo>/data`; `ETHAN_DATA_DIR` override already mapped) + expose
   `persist_directory` for the chromadb backend (`rag-config`, default
   `<data_dir>/vectors`). This resolves the dead-config finding of the audit.
3. **FileStore wiring**: instantiate with `storage_dir="<data_dir>/files"`
   (parameter already exists); keep the base64 fallback for records predating
   the change (dual-read in `download()` already supported).
4. **EventType additions**: `RESOURCE_IMPORTED`, `RESOURCE_STATUS_CHANGED`,
   `RESOURCE_DELETED` (same publication pattern as `PROJECT_CREATED`).
5. **Folder registry**: `FolderManager.add_provider("resource", …)` — the open
   registry absorbs the new type with zero changes to folders.

