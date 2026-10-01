# Duplicate Detection — Architecture

> **Statut : IMPLEMENTED** — Core module `core/dedup/`, API gateway
> `/v1/dedup`, WebUI page `/dedup`.  Read-only detector + secure resolver.
> No automatic deletion.

---

## 1. Purpose

Identify potentially identical resources across **Library** (FileStore),
**Projects** (ProjectManager), **Knowledge** (KnowledgeManager + collections)
and the **RAG** pipeline — **without deleting anything automatically**.

The detector classifies candidates into categories so the user can decide
what to keep, merge, archive or (after explicit confirmation) remove.

---

## 2. Principles

1. **Core-owned** — all classification and resolution logic lives in
   `core/dedup/`.  The API and WebUI are thin gateways that render reports
   and send intents.
2. **Read-only detection** — `DuplicateDetector.scan()` never mutates state.
   Only `DuplicateResolver` owns mutations, and only after explicit user intent.
3. **Never auto-delete** — `DELETE_AFTER_CONFIRM` requires `confirmed=true`.
   Without it the resolver returns `needs_confirm` and deletes nothing.
4. **Physical deletion is never triggered by membership removal** — removing a
   file from a project or collection never touches the underlying bytes.
5. **RAG consistency** — index cleanup uses the official
   `RAGPipeline.delete_document()` (no second collection, no double embedding).
6. **Transparency** — before any destructive step, the resolver records full
   context (associations, locations, RAG references, projects) in the returned
   `ResolutionResult` so the UI can display it for confirmation.

---

## 3. Component Overview

```
                ETHAN Core
        ┌──────────────────────────┐
        │   core/dedup/types.py    │  ScannedItem, DuplicateGroup,
        │                          │  DuplicateReport, ResolutionResult,
        │                          │  DuplicateCategory, DuplicateAction
        ├──────────────────────────┤
        │  core/dedup/detector.py  │  DuplicateDetector (read-only scan)
        ├──────────────────────────┤
        │  core/dedup/resolver.py  │  DuplicateResolver (secure mutations)
        └──────────┬───────────────┘
                   │ calls
        ┌──────────▼───────────────┐
        │  Core domains            │  FileStore, ProjectManager,
        │  (data sources)          │  KnowledgeManager, RAGPipeline
        └──────────────────────────┘
                   │
        ┌──────────▼───────────────┐
        │  API Gateway             │  /v1/dedup/scan | report | resolve
        │  routers/dedup.py       │
        └──────────┬───────────────┘
                   │ renders + sends intents
        ┌──────────▼───────────────┐
        │  WebUI  /dedup           │  DedupWorkspace
        └──────────────────────────┘
```

---

## 4. Scanned Domains

| Domain | Source | Record type | Key fields |
| ------ | ------ | ----------- | ---------- |
| Library | `FileStore` (domain `files`) | `file` record | `filename`, `size`, `content_type`, `storage_path`, `metadata` |
| Projects | `ProjectManager` (domain `projects` + `documents`) | project document | `title`, `size`, `content_type`, `project_id` |
| Knowledge | `KnowledgeManager` (domain `knowledge`) | `KnowledgeNode` | `label`, `node_type`, `source`, `connections` |
| RAG | `RAGPipeline` (domain `rag-documents`) | `IngestedDocument` | `title`, `source`, `chunks` |

Each record is normalised into a :class:`~core.dedup.types.ScannedItem` so the
classifier can compare across domains with a single vocabulary.

> **Note:** `ProjectManager` is not yet composed in `interfaces/api/main.py`,
> so project-document scanning is wired but inactive until the composition root
> instantiates it.  Library, Knowledge and RAG scanning work today.

---

## 5. Duplicate Categories

| Category | Rule | Confidence |
| -------- | ---- | ---------- |
| `exact_duplicate` | Same name **and** same content hash | 1.0 |
| `probable_duplicate` | Same hash, different name | 0.9 |
| `same_name_different_content` | Same name, different/missing hashes | 0.7 |
| `different_version` | Same name/location lineage (version metadata) | 0.6 |
| `same_content_different_location` | Same hash, different storage paths | 0.9 |
| `already_indexed` | File exists **and** RAG doc with same name exists | 0.8 |
| `orphan_document` | RAG doc without a matching source file | — |
| `broken_reference` | Project/collection doc pointing at a missing source | — |

Content-hash buckets stay empty until a file supplies a hash.  The detector
computes SHA-256 via :meth:`DuplicateDetector.compute_file_hash` when the
binary is readable from the in-Core store (`files_content`) or the
`storage_path`.

---

## 6. Resolution Actions

| Action | Effect | Destructive? |
| ------ | ------ | ------------ |
| `keep_both` | No change. | No |
| `replace_with_newest` | Keep the newest (by `updated_at`), remove the rest. | After confirm |
| `keep_primary` | Keep a chosen item (`primary_item_id`), remove the rest. | After confirm |
| `move_to_archive` | Mark metadata `archived=true`. **Never** deletes the physical file. | No |
| `delete_after_confirm` | Remove from projects/collections + delete physical file. | **Yes, only with `confirmed=true`** |
| `repair_reference` | Re-link a broken reference to the best candidate in the group. | No |
| `merge_associations` | Merge project/collection/folder memberships onto one item without duplicating the underlying file. | No |

`replace_with_newest` and `keep_primary` perform physical deletion only when
called through `_remove_items(..., confirmed=True)`, which is reached solely
via `DELETE_AFTER_CONFIRM` with `confirmed=true` or when the caller explicitly
passes `confirmed=True`.

---

## 7. Safety Contract

The resolver enforces these rules (verified by `tests/test_dedup_resolver.py`):

1. **No automatic deletion** — `DELETE_AFTER_CONFIRM` with `confirmed=false`
   returns `needs_confirm` and deletes nothing.
2. **Membership removal never deletes bytes** — removing a document from a
   project or collection only drops the relationship record.
3. **Full context before destruction** — :meth:`DuplicateResolver.resolve`
   builds an `associations` map (project/collection/folder ids per item),
   `locations`, `rag_document_ids`, `project_ids`, `collection_ids` and
   returns them in :class:`ResolutionResult` so the UI can show exactly what
   will be affected.
4. **Partial failure is never masked** — errors are collected and returned in
   `ResolutionResult.error`; status becomes `partially_completed` instead of
   `applied`.
5. **RAG uses the official pipeline** — index cleanup calls
   `RAGPipeline.delete_document()`, which removes the durable record, the
   ingestion catalogue entry and the retrieval index in one call.  No second
   collection is created without reason.

---

## 8. RAG Integrity

After consolidation or deduplication:

* **Stale indexes detected** — `orphan_document` flags RAG docs whose source
  file is gone.
* **No double embeddings** — re-indexing reuses the official
  `RAGPipeline.ingest()` path; the detector never parses or embeds.
* **Controlled reindex** — the WebUI offers a "Repair reference" action that
  re-links a broken doc to the best candidate without re-embedding.
* **No gratuitous collection** — the resolver never creates a new collection
  to hold deduplicated documents; it merges memberships onto the keeper.

---

## 9. API

All routes are under `/v1/dedup` and require `Permission.MEMORY`.

| Method | Path | Purpose |
| ------ | ---- | ------- |
| `GET`  | `/health` | Liveness probe. |
| `POST` | `/scan` | Run a read-only scan, return a `DuplicateReport`. |
| `GET`  | `/report/{scan_id}` | Fetch a previously generated report. |
| `GET`  | `/categories` | List categories and available actions. |
| `POST` | `/resolve` | Apply a resolution action to a group. |

The latest report is kept in memory on the gateway so `GET /report/{scan_id}`
and `POST /resolve` can reference it without a second scan.

---

## 10. Flow

```
User clicks "Scan" (WebUI)
        │
        ▼
POST /v1/dedup/scan  ──►  DuplicateDetector.scan()
        │                       ├─ scan_files()
        │                       ├─ scan_project_documents()
        │                       ├─ scan_knowledge()
        │                       ├─ scan_rag()
        │                       └─ classify into DuplicateGroup[]
        │
        ▼
WebUI renders groups by category
        │
        ▼
User picks an action (e.g. "Delete")
        │
        ▼
POST /v1/dedup/resolve {confirmed:false}
        │
        ▼
DuplicateResolver.resolve() → needs_confirm + full context
        │
        ▼
WebUI shows context + "Confirm delete" button
        │
        ▼
User confirms → POST /v1/dedup/resolve {confirmed:true}
        │
        ▼
Resolver removes from projects/collections, deletes RAG index,
deletes physical file (only now) → ResolutionResult(status=applied)
```

---

## 11. Tests

| Suite | Scope | Count |
| ----- | ----- | ----- |
| `tests/test_dedup_detector.py` | Classification logic (read-only) | 10 |
| `tests/test_dedup_resolver.py` | Safety contract + mutations | 10 |
| `tests/test_dedup_api.py` | Gateway wiring (health, categories, scan) | 4 |

All 24 tests pass (`EXIT=0`).  The WebUI build compiles (`next build`
`BUILD_EXIT=0`) and `tsc --noEmit` reports no errors.
