from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import pytest

from core.engineering_memory import MemoryRecord, RecordType
from core.engineering_memory.security import SecurityPolicy, SecurityPolicyError
from core.engineering_memory.validators import ValidationError


class SecretRecordPlaceholder(MemoryRecord):
    pass


def _record(notes: str) -> MemoryRecord:
    return MemoryRecord(
        id="EVT-2026-001",
        record_type=RecordType.ENGINEERING_EVENT,
        title="safe title",
        status="RECORDED",
        source_of_fact="test",
        provenance_level=__import__("core.engineering_memory.models", fromlist=["SourceOfFactLevel"]).SourceOfFactLevel.OBSERVED,
        components=["CMP-test"],
        created_at=datetime.now(timezone.utc).isoformat(),
        updated_at=datetime.now(timezone.utc).isoformat(),
        evidence_refs=[],
        authors=["pytest"],
        origin=__import__("core.engineering_memory.models", fromlist=["RecordOrigin"]).RecordOrigin.DECLARED,
        confidence=__import__("core.engineering_memory.models", fromlist=["ConfidenceLevel"]).ConfidenceLevel.MEDIUM,
        notes=notes,
    )


def test_security_policy_rejects_secret_like_notes() -> None:
    record = _record("bucket password=very-secret-value")
    with pytest.raises(SecurityPolicyError):
        SecurityPolicy.validate_record(record)


def test_security_policy_accepts_safe_notes() -> None:
    record = _record("All clear, no credentials here.")
    SecurityPolicy.validate_record(record)


def test_path_escape_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "memory"
    evil = tmp_path / "secret.md"
    with pytest.raises(SecurityPolicyError):
        SecurityPolicy.ensure_path_in_root(root, evil)


def test_human_root_roles_do_not_self_approve() -> None:
    assert not SecurityPolicy.can(__import__("core.engineering_memory.security", fromlist=["Role"]).Role.PROPOSER, __import__("core.engineering_memory.security", fromlist=["Permission"]).Permission.HUMAN_APPROVE)
    assert SecurityPolicy.requires_human_approval("approve_decision")
