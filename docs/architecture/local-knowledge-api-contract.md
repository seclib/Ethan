# ETHAN — Local Knowledge API Contract

**Status**: Design (contracts only — no implementation). Companion to
`local-knowledge-domain.md`.
**Principle**: existing Core endpoints are referenced, never duplicated. New
endpoints cover only the gaps (unified resource + local import).

---

## 1. Endpoint Map — existing vs new

| Required capability | Contract | Status |
|---|---|---|
| List collections | `GET /v1/rag/collections` | **EXISTING** — no change |
| Create collection | `POST /v1/rag/collections` (`name`, `retrieval_strategy`, `embedding_provider/model`) | **EXISTING** — no change |
| List folders | `GET /v1/folders/tree` (+ `GET /v1/folders/index?resource_type=resource`) | **EXISTING** — registry gains the `resource` type |
| Create folder | `POST /v1/folders` | **EXISTING** — no change |
| List resources | `GET /v1/knowledge/resources` | **NEW** |
| Import resource | `POST /v1/knowledge/resources/import` | **NEW** |
| Import folder | `POST /v1/knowledge/resources/import-folder` | **NEW** |
| Move resource | `POST /v1/folders/move-resource` | **EXISTING** — works for `resource_type="resource"` via the open registry |
| Delete resource | `DELETE /v1/knowledge/resources/{id}` | **NEW** |
| Resource metadata | `GET /v1/knowledge/resources/{id}` | **NEW** |
| Collection status | `GET /v1/rag/collections/{id}/status` | **NEW** (thin read-only projection over existing pipeline state) |

Collection/folder **membership mutations** remain where they live today
(`POST /v1/folders/move-resource`, collection attach endpoints). No parallel
membership API is introduced.

---

## 2. New Contracts

### 2.1 `GET /v1/knowledge/resources`

Query: `kind`, `q` (name/description), `folder_id`, `collection_id`,
`project_id`, `status`, `limit` (≤200, default 50), `offset`.
Auth: `Permission.READ`, owner-scoped (admin sees all).

`200 OK`
```jsonc
{ "resources": [ { /* resource record — domain doc §2 */ } ],
  "total": 123, "limit": 50, "offset": 0 }
```
Filter semantics: `folder_id`/`collection_id`/`project_id` intersect via the
owning relations (no denormalized copy).

### 2.2 `POST /v1/knowledge/resources/import`

Two mutually exclusive sources:
- **multipart**: `file` (bytes) — the browser path; OR
- **JSON**: `{ "relative_path": "import/notes/foo.pdf" }` — local path **inside
  `data/import/`** only (boundary rules, domain doc §4).

Common body fields: `name?`, `kind?` (default from MIME),
`folder_ids?: []`, `collection_ids?: []`, `project_ids?: []`,
`ingest?: true` (default).

Auth: `Permission.WRITE`. Flow: validate → sha256 dedup → `FileStore.register`
(content-addressed on disk) → create `resources` record (`status=imported`) →
attach relations → if `ingest` and kind=document: shared `RAGPipeline.ingest`
→ `ready`/`error`.

`201 Created` → resource record (+`existing_resource_id` when sha256 dedup hit,
HTTP 200 instead). `202 Accepted` if ingestion deferred async.
Errors: 400/403/409/413/415/422/503 per the error table.

### 2.3 `POST /v1/knowledge/resources/import-folder`

`{ "relative_path": "import/mydir", "recursive": true, "collection_ids": [],
  "folder_ids": [], "project_ids": [], "max_files": 200 }`

Bounded walk of `data/import/<rel>` (regular files only, whitelist MIME,
per-file + total size caps, deterministic order). Per-file errors are
**isolated**: one bad file never aborts the batch.

`207 Multi-Status`
```jsonc
{ "imported": [ /* resource records */ ],
  "failed":  [ { "relative_path": "…", "code": 415, "detail": "unsupported MIME" } ],
  "skipped": [ { "relative_path": "…", "reason": "sha256 duplicate of <resource_id>" } ] }
```
Hard caps → 413 with counts. Auth: `Permission.WRITE`.

### 2.4 `GET /v1/knowledge/resources/{id}`

`200 OK` → full resource record including the membership **projections**
(`folder_ids`, `collection_ids`, `project_ids`), `chunk_count`, `status`.
Never: file bytes, absolute paths. Content download stays on the existing
`GET /files/{id}/download` route (Core streams from disk or base64 fallback).

### 2.5 `DELETE /v1/knowledge/resources/{id}`

Query: `delete_file=false` (default; `true` deletes the PhysicalFile when
refcount reaches 0), `purge_vectors=true` (default; runs
`RAGPipeline.delete_document(resource_id)`).
`204 No Content` | `404` | `403` | `409` (refcount > 0 without force).
Side effects: folder memberships and collection membership removed; projects
keep the tombstone-free reference cleaned.

### 2.6 `GET /v1/rag/collections/{id}/status`

Read-only projection assembled by Core from the shared pipeline catalog:

```jsonc
{ "collection_id": "…", "retrieval_strategy": "hybrid",
  "embedding": { "provider": "…", "model": "…" },
  "vector_backend": "chromadb",           // effective backend name only
  "documents": 42, "chunks": 1337,
  "by_status": { "ready": 40, "ingesting": 1, "error": 1 },
  "last_indexed_at": "…", "health": "ok | degraded | error" }
```
`health=degraded` when any document is `error`/stale; never exposes backend
hosts, credentials or paths.

---

## 3. Cross-Cutting Contract Rules

1. **Auth**: JWT (existing `auth.py` middleware); RBAC as per the error table.
   Owner scoping on every list/get/delete; admin bypass explicit.
2. **Events**: `RESOURCE_IMPORTED` / `RESOURCE_STATUS_CHANGED` / `RESOURCE_DELETED`
   published on the EventBus — folders, Library and future WebUI react via API,
   never via shared state.
3. **No duplication guarantees**:
   - bytes → `FileStore` only; metadata → `resources` only;
   - membership → folders/collections managers only;
   - ingestion/index/retrieval → shared `RAGPipeline` only;
   - vector backend access → `RAGVectorStore` only (WebUI: zero direct access).
4. **Idempotency**: sha256 dedup makes single and bulk imports safely retryable;
   `RAGPipeline` upserts are idempotent by `chunk_id`.
5. **Versioning**: new routes mount under the existing `/v1` gateway with the
   same JWT→Bearer proxy; response shapes follow existing router conventions
   (camelCase only at the WebUI boundary via existing clients).

---

## 4. Explicit Non-Goals (per instructions)

- No WebUI implementation in this phase.
- No new storage engine, no second RAG pipeline, no second membership system.
- No arbitrary integrations (e.g. S3/remote import) — local boundary only.
- No breaking change to existing `/v1/rag`, `/v1/folders`, `/v1/projects`
  routes; the `resource` type is additive to the open folder registry.

