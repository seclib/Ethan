"""Validation des enregistrements de la mémoire technique."""

from __future__ import annotations

from datetime import datetime

from core.engineering_memory.models import (
    ConfidenceLevel,
    MemoryRecord,
    RecordOrigin,
    SourceOfFactLevel,
)


class ValidationError(Exception):
    """Erreur explicite de validation."""


_ALLOWED_STATUSES_BY_TYPE: dict[str, set[str]] = {
    "component": {"PLANNED", "IMPLEMENTED", "VERIFIED", "DEPRECATED", "UNKNOWN"},
    "decision": {"PROPOSED", "UNDER_REVIEW", "APPROVED", "REJECTED", "DEPRECATED", "SUPERSEDED"},
    "engineering_event": {
        "PROPOSED",
        "UNDER_REVIEW",
        "IMPLEMENTED",
        "VERIFIED",
        "DECLINED",
        "FAILED",
        "REJECTED",
        "RECORDED",
        "OBSERVED",
    },
    "incident": {"OPEN", "INVESTIGATING", "MITIGATED", "RESOLVED", "VERIFIED", "FALSE_POSITIVE"},
    "repair": {"PROPOSED", "APPROVED", "IMPLEMENTED", "VERIFIED", "FAILED", "ABANDONED"},
    "verification": {"PENDING", "PASSED", "FAILED", "INCONCLUSIVE", "OBSOLETE"},
    "dependency": {"CLEAN", "VULNERABLE", "REMEDIATED", "ACCEPTED_RISK", "UNKNOWN"},
    "test_result": {"RECORDED", "VERIFIED", "STALE", "INVALIDATED"},
    "technical_debt": {"IDENTIFIED", "ACCEPTED", "FIXED", "VERIFIED", "WAIVED"},
    "evidence": {"COLLECTED", "TRUSTED", "DISPUTED", "RETRACTED"},
    "agent_report": {"PROVISIONAL", "REVIEWED", "VALIDATED", "REJECTED", "ABANDONED"},
}


def _parse_iso8601(value: str) -> None:
    value = value.strip().replace("Z", "+00:00")
    try:
        datetime.fromisoformat(value)
    except ValueError as error:
        raise ValidationError(f"invalid ISO-8601 timestamp: {value}") from error


class MemoryRecordValidator:
    """Valide les données essentielles sans masquer les incohérences."""

    @staticmethod
    def validate(record: MemoryRecord) -> MemoryRecord:
        if not 1 <= len(record.id) <= 128:
            raise ValidationError("invalid id length")
        if any(char.islower() for char in record.id):
            raise ValidationError("id must use canonical uppercase identifiers")
        if not record.title.strip():
            raise ValidationError("title must not be empty")
        if not record.source_of_fact.strip():
            raise ValidationError("source_of_fact must not be empty")
        _parse_iso8601(record.created_at)
        _parse_iso8601(record.updated_at)
        if record.provenance_level not in [item.value for item in SourceOfFactLevel]:
            raise ValidationError("invalid provenance_level")
        if record.origin not in [item.value for item in RecordOrigin]:
            raise ValidationError("invalid origin")
        if record.confidence not in [item.value for item in ConfidenceLevel]:
            raise ValidationError("invalid confidence")
        record_type = record.record_type.value if hasattr(record.record_type, "value") else record.record_type
        allowed_statuses = _ALLOWED_STATUSES_BY_TYPE.get(record_type, set())
        if record.status.upper() not in allowed_statuses:
            raise ValidationError(f"status {record.status} is not allowed for {record.record_type.value}")
        for evidence_ref in record.evidence_refs:
            if not isinstance(evidence_ref, str) or not evidence_ref.strip():
                raise ValidationError("evidence_refs must contain non-empty strings")
        for component in record.components:
            if not isinstance(component, str) or not component.strip():
                raise ValidationError("components must contain non-empty strings")
        for author in record.authors:
            if not isinstance(author, str) or not author.strip():
                raise ValidationError("authors must contain non-empty strings")
        return record
