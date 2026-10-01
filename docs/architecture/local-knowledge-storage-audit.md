# ETHAN — Local Knowledge Storage Audit

**Scope**: Knowledge, Documents, Images, RAG Collections, Skills, Agents, Project resources, Vector indexes.
**Constraint audited**: user requires these resources to remain inside the ETHAN root directory.
**Mode**: read-only audit. No directories created, no files migrated, no UI implemented, no new RAG pipeline.

---

## 1. Executive Summary

ETHAN already has a **single, Core-owned persistence architecture**: every domain
(knowledge, documents, files, skills, agents, projects, RAG catalogs, reminders,
integrations) persists as JSON records in PostgreSQL via `CoreRecordStore`,
with Redis as read cache and an in-process fallback. There is **no second
storage system** and the WebUI never touches storage directly.

However, the **"inside ETHAN root" requirement is NOT currently met**:

| Resource | Current physical location | Inside ETHAN root? |
|---|---|---|
| Domain records (knowledge, agents, skills, projects, docs) | PostgreSQL `core_domain_records` → Docker named volume `postgres_data` | ❌ (Docker-managed) |
| File binaries (documents, images) | **base64 in PostgreSQL** (`files_content` domain) | ❌ (Docker-managed) |
| Vector index | In-memory by default (rebuilt at startup from PG catalog) or external ChromaDB/Qdrant (no service in compose) | ❌ / N/A |
| Skills (builtins) | Python code in repo `core/skills/builtin/` | ✅ (repo) |
| Config | `./ethan.yaml` / `~/.config/ethan/` | ⚠️ mixed |
| `data_dir` / `plugins_dir` | Configured as `~/.ethan/...` but **never consumed** (dead config) | ❌ declared outside root |

The building blocks to satisfy the requirement **already exist** (a `storage_dir`
parameter on `FileStore`, a `persist_directory` on the ChromaDB backend,
`ETHAN_DATA_DIR` env mapping) — they are simply not wired to the ETHAN root.

---

## 2. Current Storage Layout (as inspected)

```
~/AI/Ethan/                          ← ETHAN root (repo + config entrypoint)
├── ethan.yaml                       (optional project-local config, highest file priority)
├── core/
│   ├── skills/builtin/*.py          ← builtin skills = CODE in repo (synced to store at boot)
│   ├── plugins/                     ← plugin code lives in repo
│   ├── state/                       ← record_store.py, files.py, chats.py (all Core-owned)
│   ├── rag/                         ← pipeline, ingestion, vector_store, retrieval
│   ├── knowledge/                   ← manager + web_ingest (no filesystem layout)
│   └── config/                      ← loader, schema, service, store, secrets
├── deploy/postgres/
│   ├── init.sql                     ← 15 tables (events, outbox, goals, …) — initdb only
│   └── migrations/001…006           ← users, llm_providers, core_domain_records, totp
└── (NO data/, uploads/, documents/, vectors/ directories exist today)

Docker named volumes (OUTSIDE the ETHAN root):
├── postgres_data     ← ALL durable records + base64 file binaries
├── redis_data        ← read cache + live state
├── nats_data         ← event bus persistence
└── postgres_backup

Outside the root (declared but unused):
└── ~/.ethan/data, ~/.ethan/plugins   ← defaults in RuntimeConfig, never read by any consumer
```

---

## 3. Current Ownership

| Layer | Owns | Does NOT do |
|---|---|---|
| **Core** (`core/state/*`, `core/rag/*`, `core/knowledge/*`, `core/skills/*`, `core/projects/*`) | Domain logic, validation, persistence, filesystem access parameters | — |
| **API** (`interfaces/api/routers/*`) | HTTP gateway, RBAC, multipart handling, delegation | No storage decisions |
| **WebUI** (`interfaces/webui/src/lib/api/*`) | Rendering + upload/download actions through the API | No parsing, no embeddings, no Qdrant access, no storage |
| **Runtime** (docker services: api, kernel, modules) | Execution, privileged DB/Redis/NATS connections | — |

Ownership is clean: `FileStore` and `CoreRecordStore` are the only persistence
boundaries; domain managers (`KnowledgeManager`, `AgentManager`, `SkillStore`,
`ProjectManager`, `RAGPipeline`) all delegate to them.

---

## 4. Existing Core APIs (storage-relevant)

| API | Owner | Storage effect |
|---|---|---|
| `POST /files/upload`, `GET /files`, `GET /files/{id}`, `DELETE /files/{id}`, download | `FileStore` | metadata → `files` domain; bytes → `files_content` (base64) or `storage_path` |
| Knowledge CRUD (`/v1/knowledge…`) | `KnowledgeManager` | records in `knowledge` domain (node `source` field is metadata, not a filesystem path) |
| RAG ingest/reindex (`/v1/rag…`, `PUT /v1/rag/config`) | `RAGPipeline` | catalog in record store; vectors in pluggable backend |
| Project documents (`POST/GET/DELETE /v1/projects/{id}/documents`) | `ProjectManager` + shared pipeline | records in `documents` domain, extraction → shared RAG pipeline |
| Skills CRUD + import/export | `SkillStore` | records in `skills` domain; builtins synced from repo code |
| Agents CRUD | `AgentManager` | records in `agents`, executions in `agent-executions` |
| Web ingest scan/preview/ingest | `WebIngestionManager` | transient preview in memory; durable output via RAG pipeline |

WebUI clients (`lib/api/files.ts`, `library.ts`, `projects.ts`, …) map 1:1 to
these endpoints and contain no storage logic — verified.

---

## 5. Existing Models & Migrations

- **`core_domain_records`** (migration 005): `(domain, record_id, record JSONB, updated_at)`
  — the single generic table backing every domain listed above.
- Dedicated tables: `users` (003), `llm_providers` (004), `totp` (006),
  `events`, `events_outbox`, goals & step history (init.sql — 15 tables).
- No Alembic; migrations are plain SQL applied under `schema_migrations` tracking.
- Models are JSON records inside each domain manager (validated by domain code),
  e.g. `FileRecord {filename, content_type, size, storage_path, has_content, …}`,
  `KnowledgeNode {…, source}`, skill records with `kind/steps/required_tools`.

---

## 6. Existing Ingestion Pipeline (single, shared)

```
Upload (multipart) → API router (size/MIME/RBAC validation)
  → domain manager (ProjectManager / KnowledgeManager / WebIngestionManager)
    → core/rag/extractors.extract_text()   (PDF, DOCX, TXT/MD/CSV/JSON; images: no text)
    → RAGIngestion: chunking (character | sentence | paragraph; chunk_size/overlap)
    → RAGEmbeddings (dimension validated before any network call)
    → RAGVectorStore.upsert (idempotent by chunk_id)
    → catalog record persisted (status: ready | error)
Retrieval → RAGRetrieval (auto | keyword | semantic | hybrid/RRF), scoped by document_ids
```

There is exactly **one** pipeline; Projects, Knowledge and web-ingest share it
(`main.py` injects the same `RAGPipeline` as `ingestion_service`).

---

## 7. Existing RAG / Vector Architecture

`core/rag/vector_store.py` — ABC `RAGVectorStore` with three backends:

| Backend | Location of vectors | Local-dir capable? |
|---|---|---|
| `memory` (default) | process RAM; rebuilt at startup by re-indexing the PG catalog | n/a (data lives in PG catalog) |
| `chromadb` | HTTP client (host:port) **or** `PersistentClient(path=persist_directory)` | ✅ parameter exists, not exposed by default config |
| `qdrant` | HTTP only (host:port 6333) | ❌ remote-only; **no qdrant service in docker-compose** |

Key property: the **catalog of chunks persists in PostgreSQL**, so switching or
losing a vector backend is recoverable (idempotent re-index on open). This makes
a future "vectors inside ETHAN root" migration low-risk.

---

## 8. Duplicated Systems

**None found.** One record store, one file store, one RAG pipeline, one vector
ABC. The only noteworthy tension (not a duplication):

- **Binary-in-DB**: `files_content` stores file bytes base64 inside PostgreSQL.
  It is a deliberate zero-dependency fallback, but it bloats the DB and keeps
  binaries outside the ETHAN root. `FileStore.storage_dir` exists precisely to
  avoid this and is simply not wired (`main.py`: `FileStore(store=domain_store)`).

Dead configuration (P2): `runtime.data_dir` / `runtime.plugins_dir`
(`~/.ethan/…`, env `ETHAN_DATA_DIR` / `ETHAN_PLUGINS_DIR`) are defined in
`core/config/schema.py` and mapped in `core/config/loader.py` but **no consumer
reads them** — they neither store nor load anything today.

---

## 9. Missing Capabilities (relative to the root-local requirement)

1. **No ETHAN-root data directory**: no `data/` tree is created or mounted;
   Docker mounts only `init.sql` read-only into postgres.
2. **File binaries not on disk**: `FileStore` instantiated without `storage_dir`,
   so images/documents live base64-encoded in PostgreSQL.
3. **Local vector persistence not exposed**: ChromaDB `persist_directory` is
   supported by the class but not surfaced in `rag-config` defaults; Qdrant
   cannot persist locally at all (HTTP-only client, no compose service).
4. **`data_dir`/`plugins_dir` unimplemented** despite being part of the config schema.
5. **No user skill directory discovery**: user skills exist only as store records
   (import/export via API); builtins are repo code. (Acceptable — not a gap in
   ownership, only in on-disk layout.)

---

## 10. Recommended Target Architecture (no implementation in this audit)

Keep the current single-system boundaries; re-point physical storage into the root:

```
~/AI/Ethan/data/
├── files/                 ← FileStore storage_dir (binaries; DB keeps metadata only)
├── vectors/               ← ChromaDB PersistentClient path (or local Qdrant alternate)
└── plugins/               ← future consumer of runtime.plugins_dir
```

Minimal-change wiring options (for a future RFC — **not done here**):
1. `FileStore(store=…, storage_dir="<root>/data/files")` — parameter already exists.
2. Expose `vector_backend_config.persist_directory` in `rag-config` and default
   it to `<root>/data/vectors` when backend is `chromadb`.
3. Make `runtime.data_dir` effective (resolve `<root>/data` by default) and add a
   `./data:/app/data` bind mount to the `api` service so Docker and local modes
   share the same root-local location.
4. Postgres/Redis/NATS volumes may stay Docker-managed (infrastructure), but
   optionally bind-mount `postgres_data` under `<root>/data/postgres` if strict
   "everything in root" is required — trade-offs in §11.

---

## 11. Migration Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Base64-in-PG → on-disk files: existing `files_content` records must be drained or dual-read | Medium | Keep `download()` resolution order (content record first, then `storage_path`) — already implemented; drain under feature flag |
| Docker vs local mode path divergence (container paths ≠ host paths) | High | Single bind mount `./data:/app/data` + root-relative resolution at startup; never store absolute host paths in records |
| Vector backend switch: `memory` → local dir loses nothing (re-index from PG catalog is idempotent) | Low | Already handled by pipeline re-index-on-open |
| `dimension mismatch` after embedding-model change during re-index | Medium | Existing validation raises at ingest; document re-embedding procedure before switching models |
| Root-local DB bind mount (if chosen) increases accidental-deletion surface (`rm -rf data/`) | Medium | Keep named volume as default; bind mount only behind explicit opt-in; `postgres_backup` volume unchanged |
| Concurrent writers to `data/files` from api + kernel replicas | Low | Only the API service writes files today; keep single-writer convention or add per-service subdirs |

---

## 12. Verdict on the Current Implementation

- **Local-storage capable?** Partially. The architecture is storage-agnostic and
  Core-owned (correct), but the *wired default* stores binaries in PostgreSQL
  (Docker volume) and vectors in memory — both physically outside the ETHAN root.
- **Effort to comply**: low. The required parameters (`storage_dir`,
  `persist_directory`, `ETHAN_DATA_DIR`) already exist; wiring + a small
  migration/drain script + one compose bind mount are sufficient. No second
  storage system is needed, and none should be created.
