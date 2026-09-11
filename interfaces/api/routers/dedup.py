"""Duplicate Detection API — scan + resolve endpoints.

This router is a thin HTTP gateway.  All classification and resolution logic
lives in the Core (:mod:`core.dedup`); this layer only (1) invokes the
detector/resolver and (2) returns serialisable reports.  The WebUI renders
those reports and sends resolution intents back through ``POST /resolve``.

Safety: ``DELETE_AFTER_CONFIRM`` requires an explicit ``confirmed: true`` body
field — the resolver returns ``needs_confirm`` otherwise, never deleting.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.dedup import (
    DuplicateAction,
    DuplicateCategory,
    DuplicateDetector,
    DuplicateGroup,
    DuplicateReport,
    DuplicateResolver,
    ScannedItem,
)
from interfaces.api.auth import require_permission
from core.auth import Permission
from core.state import CoreRecordStore
from core.state.files import FileStore
from core.projects import ProjectManager
from core.knowledge import KnowledgeManager, KnowledgeCollectionManager
from core.rag import RAGPipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/dedup", tags=["dedup"])

# ── Injected Core managers (set once at startup, like other routers) ──────

_store: CoreRecordStore | None = None
_files: FileStore | None = None
_projects: ProjectManager | None = None
_knowledge: KnowledgeManager | None = None
_collections: KnowledgeCollectionManager | None = None
_rag: RAGPipeline | None = None

# Latest scan report, kept in memory for GET /report/{scan_id}.
_latest_report: DuplicateReport | None = None


def set_dedup_managers(
    store: CoreRecordStore,
    files: FileStore | None = None,
    projects: ProjectManager | None = None,
    knowledge: KnowledgeManager | None = None,
    collections: KnowledgeCollectionManager | None = None,
    rag: RAGPipeline | None = None,
) -> None:
    """Inject Core-owned managers (called from main.py at startup)."""
    global _store, _files, _projects, _knowledge, _collections, _rag
    _store = store
    _files = files
    _projects = projects
    _knowledge = knowledge
    _collections = collections
    _rag = rag


def _detector() -> DuplicateDetector:
    if _store is None:
        raise HTTPException(503, "Dedup store not initialised")
    return DuplicateDetector(
        store=_store, files=_files, projects=_projects,
        knowledge=_knowledge, collections=_collections, rag=_rag,
    )


def _resolver() -> DuplicateResolver:
    if _store is None:
        raise HTTPException(503, "Dedup store not initialised")
    return DuplicateResolver(
        store=_store, files=_files, projects=_projects,
        collections=_collections, rag=_rag,
    )

class ScanRequest(BaseModel):
    user_id: str | None = None


class ResolveRequest(BaseModel):
    group_id: str
    action: DuplicateAction
    confirmed: bool = False
    primary_item_id: str = ""


@router.get("/health")
async def dedup_health():
    """Liveness probe for the dedup gateway."""
    return {"status": "ok", "scope": "v1/dedup"}


@router.post("/scan", response_model=None)
async def scan_duplicates(
    body: ScanRequest | None = None,
    _perm: None = Depends(require_permission(Permission.MEMORY)),
):
    """Run a read-only scan across all Core domains and return a report.

    The scan never mutates state — it only normalises and classifies.
    """
    user_id = body.user_id if body else None
    report = await _detector().scan(user_id=user_id)
    global _latest_report
    _latest_report = report
    return report.to_dict()


@router.get("/report/{scan_id}")
async def get_report(scan_id: str):
    """Return a previously generated report by its scan id."""
    if _latest_report is None or _latest_report.scan_id != scan_id:
        raise HTTPException(404, f"Report {scan_id} not found")
    return _latest_report.to_dict()


@router.get("/categories")
async def list_categories():
    """List the duplicate categories and available resolution actions."""
    return {
        "categories": [c.value for c in DuplicateCategory],
        "actions": [a.value for a in DuplicateAction],
    }


@router.post("/resolve")
async def resolve_group(
    body: ResolveRequest,
    _perm: None = Depends(require_permission(Permission.MEMORY)),
):
    """Apply a resolution action to a duplicate group.

    ``DELETE_AFTER_CONFIRM`` with ``confirmed=false`` returns a
    ``needs_confirm`` result (no mutation).  Re-post with ``confirmed=true``
    to actually delete.
    """
    if _latest_report is None:
        raise HTTPException(400, "No scan available — run POST /scan first")
    group = next((g for g in _latest_report.groups if g.group_id == body.group_id), None)
    if group is None:
        raise HTTPException(404, f"Group {body.group_id} not found")
    result = await _resolver().resolve(
        group, body.action, confirmed=body.confirmed, primary_item_id=body.primary_item_id,
    )
    return result.to_dict()
