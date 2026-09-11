"""API tests for the dedup gateway — call router functions directly."""

from __future__ import annotations

import asyncio
import pytest
from interfaces.api.routers import dedup as dedup_router
from core.state import CoreRecordStore
from core.state.files import FileStore
from core.knowledge import KnowledgeManager, KnowledgeCollectionManager
from core.rag import RAGPipeline


@pytest.fixture()
def wired():
    store = CoreRecordStore()
    files = FileStore(store=store)
    knowledge = KnowledgeManager(store=store)
    rag = RAGPipeline(store=store)
    collections = KnowledgeCollectionManager(store=store, rag=rag)
    dedup_router.set_dedup_managers(
        store=store, files=files, knowledge=knowledge,
        collections=collections, rag=rag,
    )
    yield store
    dedup_router.set_dedup_managers(store=CoreRecordStore())


def test_health_ok():
    resp = asyncio.run(dedup_router.dedup_health())
    assert resp["status"] == "ok"


def test_categories_lists_all():
    data = asyncio.run(dedup_router.list_categories())
    assert "exact_duplicate" in data["categories"]
    assert "keep_both" in data["actions"]


def test_scan_returns_report(wired):
    resp = asyncio.run(dedup_router.scan_duplicates(body=None, _perm=None))
    assert "scan_id" in resp
    assert resp["total_scanned"] == 0


def test_report_not_found():
    with pytest.raises(Exception):
        asyncio.run(dedup_router.get_report("missing-id"))
