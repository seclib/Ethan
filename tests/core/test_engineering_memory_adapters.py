from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from core.engineering_memory.adapters import EngineeringMemoryIntegration
from core.engineering_memory import EngineeringMemoryService


class FailingService:
    def record(self, record):  # type: ignore[no-untyped-def]
        raise RuntimeError("memory unavailable")

    def __getattr__(self, name: str):  # pragma: no cover - defensive
        return None


def test_adapter_records_service_event(tmp_path: Path) -> None:
    service = EngineeringMemoryService(root=tmp_path / "Obsidian")
    adapter = EngineeringMemoryIntegration(service=service, source="unit")
    record = adapter.record_service_event(
        component="backend",
        event_type="backend.service_started",
        title="backend started",
        status="RECORDED",
        origin=__import__("core.engineering_memory.models", fromlist=["RecordOrigin"]).RecordOrigin.OBSERVED,
        source_of_fact="test",
        details="started",
    )
    assert record is not None
    assert service.search(component="backend")
    assert adapter.stats.records_accepted == 1
    assert adapter.stats.records_failed == 0


def test_adapter_does_not_block_when_collection_fails() -> None:
    adapter = EngineeringMemoryIntegration(service=FailingService(), source="unit")
    record = adapter.record_service_event(
        component="backend",
        event_type="backend.error",
        title="probe",
        status="RECORDED",
        origin=__import__("core.engineering_memory.models", fromlist=["RecordOrigin"]).RecordOrigin.OBSERVED,
        source_of_fact="test",
        details="forced failure",
    )
    assert record is None
    assert adapter.stats.records_accepted == 0
    assert adapter.stats.records_failed == 1
    assert adapter.stats.last_failure != ""
