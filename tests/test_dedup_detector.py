"""Tests Core — Duplicate Detector (read-only scan + classification).

The detector never mutates state; it only normalises items into
:class:`~core.dedup.types.ScannedItem` and classifies groups by name.
Content-hash buckets stay empty until a file supplies a hash.
"""

from __future__ import annotations

import asyncio
import pytest
from core.dedup import DuplicateCategory, DuplicateDetector, DuplicateReport
from core.dedup.types import DuplicateGroup, ItemDomain, ScannedItem
from core.state import CoreRecordStore


def _make_detector(store: CoreRecordStore | None = None) -> DuplicateDetector:
    return DuplicateDetector(store=store or CoreRecordStore())


def _file_item(file_id: str, name: str, **kw) -> ScannedItem:
    return ScannedItem(
        id=file_id,
        domain=ItemDomain.FILE,
        name=name,
        size=kw.get("size", 100),
        content_type=kw.get("content_type", "text/plain"),
        content_hash=kw.get("content_hash", ""),
        created_at=kw.get("created_at", "2025-01-01T00:00:00Z"),
        updated_at=kw.get("updated_at", "2025-01-01T00:00:00Z"),
        locations=kw.get("locations", []),
        metadata=kw.get("metadata", {}),
    )


def test_scan_returns_report_with_zero_items_when_store_empty():
    async def scenario():
        det = _make_detector()
        report = await det.scan()
        assert isinstance(report, DuplicateReport)
        assert report.total_scanned == 0
        assert report.groups == []
        assert report.orphans == []
        assert report.broken_references == []

    asyncio.run(scenario())


def test_group_by_exact_duplicate_needs_matching_name_and_hash():
    det = _make_detector()
    f1 = _file_item("f1", "doc.txt", content_hash="abc123")
    f2 = _file_item("f2", "doc.txt", content_hash="abc123")
    groups = det._group_by_exact_duplicate([f1, f2], [])
    assert len(groups) == 1
    assert groups[0].category == DuplicateCategory.EXACT_DUPLICATE
    assert len(groups[0].items) == 2
    assert groups[0].confidence == 1.0


def test_group_by_exact_duplicate_ignores_different_names():
    det = _make_detector()
    f1 = _file_item("f1", "a.txt", content_hash="abc123")
    f2 = _file_item("f2", "b.txt", content_hash="abc123")
    groups = det._group_by_exact_duplicate([f1, f2], [])
    assert groups == []


def test_group_by_name_flags_same_name_different_content():
    det = _make_detector()
    f1 = _file_item("f1", "rapport.pdf", content_hash="hash_a")
    f2 = _file_item("f2", "rapport.pdf", content_hash="hash_b")
    groups = det._group_by_name([f1, f2], [])
    assert len(groups) == 1
    assert groups[0].category == DuplicateCategory.SAME_NAME_DIFFERENT_CONTENT


def test_group_by_name_ignores_unique_names():
    det = _make_detector()
    f1 = _file_item("f1", "alpha.txt")
    f2 = _file_item("f2", "beta.txt")
    assert det._group_by_name([f1, f2], []) == []


def test_group_same_content_different_location():
    det = _make_detector()
    f1 = _file_item("f1", "x.txt", content_hash="h1", locations=["/a/x.txt"])
    f2 = _file_item("f2", "x.txt", content_hash="h1", locations=["/b/x.txt"])
    groups = det._group_same_content_different_location([f1, f2])
    assert len(groups) == 1
    assert groups[0].category == DuplicateCategory.SAME_CONTENT_DIFFERENT_LOCATION


def test_group_already_indexed_matches_file_and_rag_doc_with_same_name():
    det = _make_detector()
    f1 = _file_item("f1", "guide.md")
    rag = ScannedItem(id="r1", domain=ItemDomain.RAG_DOCUMENT, name="guide.md")
    groups = det._group_already_indexed([f1], [rag])
    assert len(groups) == 1
    assert groups[0].category == DuplicateCategory.ALREADY_INDEXED
    assert {i.id for i in groups[0].items} == {"f1", "r1"}


def test_find_orphans_flags_rag_doc_without_matching_file():
    det = _make_detector()
    rag = ScannedItem(id="r1", domain=ItemDomain.RAG_DOCUMENT, name="ghost.md")
    orphans = det._find_orphans([rag], [])
    assert len(orphans) == 1
    assert orphans[0].id == "r1"


def test_find_orphans_excludes_rag_doc_with_matching_file():
    det = _make_detector()
    rag = ScannedItem(id="r1", domain=ItemDomain.RAG_DOCUMENT, name="present.md")
    f1 = _file_item("f1", "present.md")
    assert det._find_orphans([rag], [f1]) == []


def test_file_to_item_normalises_metadata():
    det = _make_detector()
    item = det._file_to_item({
        "id": "xyz",
        "filename": "data.csv",
        "content_type": "text/csv",
        "size": 2048,
        "storage_path": "/store/data.csv",
        "metadata": {"project": "p1"},
    })
    assert item.id == "xyz"
    assert item.name == "data.csv"
    assert item.size == 2048
    assert item.locations == ["/store/data.csv"]
    assert item.metadata == {"project": "p1"}


def test_report_to_dict_roundtrip_serialises_all_fields():
    det = _make_detector()
    f1 = _file_item("f1", "doc.txt", content_hash="abc123")
    f2 = _file_item("f2", "doc.txt", content_hash="abc123")
    groups = det._group_by_exact_duplicate([f1, f2], [])
    report = DuplicateReport(
        scan_id="scan-1",
        timestamp="2025-01-01T00:00:00Z",
        total_scanned=2,
        total_files=2,
        groups=groups,
    )
    data = report.to_dict()
    assert data["scan_id"] == "scan-1"
    assert data["total_scanned"] == 2
    assert data["groups"][0]["category"] == "exact_duplicate"
    assert len(data["groups"][0]["items"]) == 2
