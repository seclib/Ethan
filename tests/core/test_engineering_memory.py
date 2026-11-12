from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from core.engineering_memory import EngineeringMemoryService, MemoryRecord, RecordType
from core.engineering_memory.models import (
    RecordOrigin,
    SourceOfFactLevel,
    ConfidenceLevel,
)
from core.engineering_memory.validators import ValidationError


def make_event(service: EngineeringMemoryService, event_id: str) -> MemoryRecord:
    return MemoryRecord(
        id=event_id,
        record_type=RecordType.ENGINEERING_EVENT,
        title="Migration test event",
        status="RECORDED",
        source_of_fact=str(service.root / "test-source"),
        provenance_level=SourceOfFactLevel.OBSERVED,
        components=["CMP-memory-service"],
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat(),
        evidence_refs=[],
        authors=["pytest-agent"],
        origin=RecordOrigin.DECLARED,
        confidence=ConfidenceLevel.MEDIUM,
        notes="integration test",
    )


def test_valid_event_is_persisted_and_reloaded(tmp_path: Path) -> None:
    service = EngineeringMemoryService(root=tmp_path / "Obsidian")
    record = make_event(service, "EVT-2026-001")

    stored = service.record(record)
    assert stored is not None

    path = service.repository_path(record.id, record.record_type)
    assert path.is_file()
    assert path.read_text(encoding="utf-8").startswith("---")

    loaded = service.get(record.id)
    assert loaded is not None
    assert loaded.id == record.id
    assert loaded.status == "RECORDED"


def test_invalid_event_is_rejected_without_writing(tmp_path: Path) -> None:
    service = EngineeringMemoryService(root=tmp_path / "Obsidian")
    record = make_event(service, "not-a-valid-id")

    with pytest.raises(ValidationError):
        service.record(record)

    search = service.search(component="CMP-memory-service")
    assert search == []


def test_duplicate_event_is_idempotent(tmp_path: Path) -> None:
    service = EngineeringMemoryService(root=tmp_path / "Obsidian")
    record = make_event(service, "EVT-2026-002")

    first = service.record(record)
    assert first is not None

    files_before = list(service.repository_path(record.id, record.record_type).parent.rglob("*.md"))
    second = service.record(record)
    files_after = list(service.repository_path(record.id, record.record_type).parent.rglob("*.md"))

    assert second is not None
    assert second.id == first.id
    assert first.repository_path == second.repository_path
    assert len(files_before) == len(files_after)


def test_search_and_component_history_are_consistent(tmp_path: Path) -> None:
    service = EngineeringMemoryService(root=tmp_path / "Obsidian")
    service.record(make_event(service, "EVT-2026-003"))

    records = service.search(component="CMP-memory-service")
    history = service.component_history("CMP-memory-service")

    assert [r.id for r in records] == ["EVT-2026-003"]
    assert [r.id for r in history] == ["EVT-2026-003"]


def test_agent_report_provenance_is_retained(tmp_path: Path) -> None:
    service = EngineeringMemoryService(root=tmp_path / "Obsidian")
    report = MemoryRecord(
        id="RPT-2026-001",
        record_type=RecordType.AGENT_REPORT,
        title="Memory protocol",
        status="PROVISIONAL",
        source_of_fact="test",
        provenance_level=SourceOfFactLevel.DERIVED,
        components=["CMP-memory-service"],
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat(),
        authors=["test-agent"],
        evidence_refs=[],
        origin=RecordOrigin.DECLARED,
        confidence=ConfidenceLevel.LOW,
        notes="",

    )

    stored = service.record(report)
    assert stored is not None
    assert stored.status == "PROVISIONAL"
