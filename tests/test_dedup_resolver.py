"""Tests Core — Duplicate Resolver (secure mutation)."""

from __future__ import annotations

import asyncio
from core.dedup import DuplicateAction, DuplicateCategory, DuplicateResolver
from core.dedup.types import DuplicateGroup, ItemDomain, ScannedItem
from core.state import CoreRecordStore


def _make_resolver(store=None, **mocks):
    return DuplicateResolver(store=store or CoreRecordStore(), **mocks)


def _file_item(file_id, name, **kw):
    return ScannedItem(
        id=file_id, domain=ItemDomain.FILE, name=name,
        size=kw.get("size", 100), content_hash=kw.get("content_hash", ""),
        created_at=kw.get("created_at", "2025-01-01T00:00:00Z"),
        updated_at=kw.get("updated_at", "2025-01-01T00:00:00Z"),
        locations=kw.get("locations", []), project_ids=kw.get("project_ids", []),
        collection_ids=kw.get("collection_ids", []), folder_ids=kw.get("folder_ids", []),
        rag_document_id=kw.get("rag_document_id", ""), metadata=kw.get("metadata", {}),
    )


def _group(*items, category=DuplicateCategory.EXACT_DUPLICATE):
    return DuplicateGroup(group_id="g1", category=category, items=list(items))


class _FakeProjects:
    def __init__(self):
        self.removed = []
        self.added = []

    async def remove_document(self, project_id, doc_id):
        self.removed.append((project_id, doc_id))

    async def add_document(self, project_id, doc_id):
        self.added.append((project_id, doc_id))


class _FakeCollections:
    def __init__(self):
        self.removed = []
        self.added = []

    async def remove_document(self, cid, doc_id):
        self.removed.append((cid, doc_id))

    async def add_document(self, cid, doc_id):
        self.added.append((cid, doc_id))


class _FakeRag:
    def __init__(self):
        self.deleted = []

    async def delete_document(self, doc_id):
        self.deleted.append(doc_id)


class _FakeFiles:
    def __init__(self):
        self.deleted = []

    async def delete(self, file_id):
        self.deleted.append(file_id)


def test_keep_both_does_not_mutate():
    async def scenario():
        res = _make_resolver()
        group = _group(_file_item("f1", "a.txt"), _file_item("f2", "a.txt"))
        result = await res.resolve(group, DuplicateAction.KEEP_BOTH)
        assert result.status == "applied"
    asyncio.run(scenario())


def test_delete_after_confirm_requires_confirmation():
    async def scenario():
        files = _FakeFiles()
        res = _make_resolver(files=files)
        group = _group(_file_item("f1", "a.txt"), _file_item("f2", "a.txt"))
        result = await res.resolve(group, DuplicateAction.DELETE_AFTER_CONFIRM, confirmed=False)
        assert result.status == "needs_confirm"
        assert result.needs_confirmation is True
        assert files.deleted == []
    asyncio.run(scenario())


def test_delete_after_confirm_with_flag_removes_and_deletes():
    async def scenario():
        files, projects, collections, rag = _FakeFiles(), _FakeProjects(), _FakeCollections(), _FakeRag()
        res = _make_resolver(files=files, projects=projects, collections=collections, rag=rag)
        f1 = _file_item("f1", "a.txt", project_ids=["p1"], collection_ids=["c1"], rag_document_id="r1")
        f2 = _file_item("f2", "a.txt", project_ids=["p2"], collection_ids=["c2"], rag_document_id="r2")
        group = _group(f1, f2)
        result = await res.resolve(group, DuplicateAction.DELETE_AFTER_CONFIRM, confirmed=True)
        assert result.status == "applied"
        assert result.kept_item_id == "f1"
        assert files.deleted == ["f2"]
        assert ("p2", "f2") in projects.removed
        assert ("c2", "f2") in collections.removed
        assert "r2" in rag.deleted
    asyncio.run(scenario())

def test_move_to_archive_marks_metadata_not_delete():
    async def scenario():
        store = CoreRecordStore()
        await store.save("files", "f1", {"id": "f1", "filename": "a.txt", "metadata": {}})
        res = _make_resolver(store=store)
        group = _group(_file_item("f1", "a.txt"), _file_item("f2", "a.txt"))
        result = await res.resolve(group, DuplicateAction.MOVE_TO_ARCHIVE)
        assert result.status == "applied"
        rec = await store.get("files", "f1")
        assert rec["metadata"]["archived"] is True
    asyncio.run(scenario())


def test_replace_with_newest_keeps_newest():
    async def scenario():
        files = _FakeFiles()
        res = _make_resolver(files=files)
        f1 = _file_item("f1", "a.txt", updated_at="2025-01-01T00:00:00Z")
        f2 = _file_item("f2", "a.txt", updated_at="2025-06-01T00:00:00Z")
        group = _group(f1, f2)
        result = await res.resolve(group, DuplicateAction.REPLACE_WITH_NEWEST, confirmed=True)
        assert result.kept_item_id == "f2"
        assert files.deleted == ["f1"]
    asyncio.run(scenario())


def test_keep_primary_requires_valid_id():
    async def scenario():
        res = _make_resolver()
        group = _group(_file_item("f1", "a.txt"), _file_item("f2", "a.txt"))
        r1 = await res.resolve(group, DuplicateAction.KEEP_PRIMARY, primary_item_id="")
        assert r1.status == "failed"
        r2 = await res.resolve(group, DuplicateAction.KEEP_PRIMARY, primary_item_id="ghost")
        assert r2.status == "failed"
    asyncio.run(scenario())


def test_merge_associations_unifies_ids():
    async def scenario():
        projects, collections = _FakeProjects(), _FakeCollections()
        res = _make_resolver(projects=projects, collections=collections)
        f1 = _file_item("f1", "a.txt", project_ids=["p1"], collection_ids=["c1"])
        f2 = _file_item("f2", "a.txt", project_ids=["p2"], collection_ids=["c2"])
        group = _group(f1, f2)
        result = await res.resolve(group, DuplicateAction.MERGE_ASSOCIATIONS)
        assert result.status == "applied"
        assert set(result.project_ids) == {"p1", "p2"}
        assert set(result.collection_ids) == {"c1", "c2"}
        assert ("p2", "f1") in projects.added
        assert ("c2", "f1") in collections.added
    asyncio.run(scenario())


def test_repair_reference_prefers_file():
    async def scenario():
        res = _make_resolver()
        rag = ScannedItem(id="r1", domain=ItemDomain.RAG_DOCUMENT, name="a.txt")
        f1 = _file_item("f1", "a.txt")
        group = DuplicateGroup(group_id="g1", category=DuplicateCategory.BROKEN_REFERENCE, items=[rag, f1])
        result = await res.resolve(group, DuplicateAction.REPAIR_REFERENCE)
        assert result.status == "applied"
        assert result.kept_item_id == "f1"
    asyncio.run(scenario())


def test_resolution_result_to_dict_roundtrip():
    from core.dedup.resolver import ResolutionResult
    res = ResolutionResult(group_id="g1", action=DuplicateAction.KEEP_BOTH, status="applied")
    data = res.to_dict()
    assert data["action"] == "keep_both"
    assert data["status"] == "applied"
