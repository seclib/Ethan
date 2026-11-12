"""Observability and engineering-memory integration for ETHAN applications (MEM-014 Phase 7)."""

from __future__ import annotations

import re
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Callable, Iterable, Mapping

OBSERVABILITY_SCHEMA_VERSION = "1.0.0"

_SECRET_PATTERNS = [
    __import__("re").compile(r"(?i)\b(?:password|passwd|api[_-]?key|secret(?:_?key)?|token|private[_-]?key)\s*[:=]\s*\S+"),
    re.compile(r"-----BEGIN (?:[A-Z ]+)?PRIVATE KEY-----", re.IGNORECASE),
    re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    re.compile(r"\b(?:sk|pk)_(?:live|test|prod)_[0-9A-Za-z]{10,}\b", re.IGNORECASE),
    re.compile(r"\bgh[ps]_[0-9A-Za-z]{20,}\b"),
]


class EventOrigin(StrEnum):
    """Provenance level of an observed event."""

    DECLARED = "declared"
    RECEIVED = "received"
    VERIFIED = "verified"


class EventStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    PENDING = "pending"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"
    RECORDED = "recorded"


class EventValidationError(ValueError):
    """Raised for malformed observability events."""


MEMORY_WORTHY_EVENT_TYPES = frozenset(
    {
        "decision",
        "significant_change",
        "incident",
        "correction",
        "repair",
        "validation",
        "technical_debt",
        "risk",
        "architecture_change",
    }
)

OPERATIONAL_ONLY_EVENT_TYPES = frozenset(
    {
        "info",
        "heartbeat",
        "request",
        "response",
        "metric",
        "trace",
    }
)


@dataclass(frozen=True, slots=True)
class IntegrationEvent:
    """A versioned, validated observation event for an application."""

    event_id: str
    schema_version: str
    app_id: str
    instance_id: str
    timestamp: datetime
    event_type: str
    operation: str
    status: str
    provenance: str
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    correlation_id: str | None = None
    duration_ms: float | None = None
    error_kind: str | None = None
    source: str = "application"
    app_version: str | None = None
    contract_version: str | None = None
    origin: EventOrigin = EventOrigin.RECEIVED

    def validate(self) -> None:
        if not self.event_id.strip():
            raise EventValidationError("event_id must not be empty")
        if self.schema_version != OBSERVABILITY_SCHEMA_VERSION:
            raise EventValidationError(
                f"schema_version must be {OBSERVABILITY_SCHEMA_VERSION}"
            )
        if not self.app_id.strip():
            raise EventValidationError("app_id must not be empty")
        if not self.instance_id.strip():
            raise EventValidationError("instance_id must not be empty")
        if not self.event_type.strip():
            raise EventValidationError("event_type must not be empty")
        if not self.operation.strip():
            raise EventValidationError("operation must not be empty")
        if self.status not in {item.value for item in EventStatus}:
            raise EventValidationError(f"invalid event status: {self.status}")
        if not self.provenance.strip():
            raise EventValidationError("provenance must not be empty")
        for ref in self.evidence_refs:
            if not isinstance(ref, str) or not ref.strip():
                raise EventValidationError("evidence_refs must contain non-empty strings")
        if self.duration_ms is not None and self.duration_ms < 0:
            raise EventValidationError("duration_ms must not be negative")
        if self.app_version is not None and not self.app_version.strip():
            raise EventValidationError("app_version must not be empty")
        if self.contract_version is not None and not self.contract_version.strip():
            raise EventValidationError("contract_version must not be empty")
        _validate_no_secret_material(self)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "IntegrationEvent":
        if not isinstance(data, Mapping):
            raise EventValidationError("event must be an object")
        _require_keys(
            data,
            {
                "event_id",
                "schema_version",
                "app_id",
                "instance_id",
                "timestamp",
                "event_type",
                "operation",
                "status",
                "provenance",
            },
        )
        try:
            timestamp_raw = data["timestamp"]
            if isinstance(timestamp_raw, str):
                timestamp = datetime.fromisoformat(timestamp_raw.replace("Z", "+00:00"))
            elif isinstance(timestamp_raw, datetime):
                timestamp = timestamp_raw
            else:
                raise EventValidationError("timestamp must be an ISO-8601 string")
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=timezone.utc)
            duration_raw = data.get("duration_ms")
            duration = None if duration_raw is None else float(duration_raw)
            origin_raw = data.get("origin", "received")
            event = cls(
                event_id=str(data["event_id"]),
                schema_version=str(data["schema_version"]),
                app_id=str(data["app_id"]),
                instance_id=str(data["instance_id"]),
                timestamp=timestamp,
                event_type=str(data["event_type"]),
                operation=str(data["operation"]),
                status=str(data["status"]),
                provenance=str(data["provenance"]),
                evidence_refs=tuple(str(item) for item in data.get("evidence_refs", [])),
                correlation_id=None if data.get("correlation_id") is None else str(data.get("correlation_id")),
                duration_ms=duration,
                error_kind=None if data.get("error_kind") is None else str(data.get("error_kind")),
                source=str(data.get("source", "application")),
                app_version=None if data.get("app_version") is None else str(data.get("app_version")),
                contract_version=None if data.get("contract_version") is None else str(data.get("contract_version")),
                origin=EventOrigin(str(origin_raw)),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise EventValidationError(f"event is missing or has invalid field: {exc}") from exc
        event.validate()
        return event

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "schema_version": self.schema_version,
            "app_id": self.app_id,
            "instance_id": self.instance_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "operation": self.operation,
            "status": self.status,
            "provenance": self.provenance,
            "evidence_refs": list(self.evidence_refs),
            "correlation_id": self.correlation_id,
            "duration_ms": self.duration_ms,
            "error_kind": self.error_kind,
            "source": self.source,
            "app_version": self.app_version,
            "contract_version": self.contract_version,
            "origin": self.origin.value,
            "event_origin": self.origin.value,
        }

    @property
    def event_origin(self) -> str:
        return self.origin.value

    def to_memory_entry(self) -> dict[str, Any]:
        """Selective, non-operational record suitable for Engineering Memory."""
        return {
            "event_id": self.event_id,
            "schema_version": self.schema_version,
            "app_id": self.app_id,
            "instance_id": self.instance_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "operation": self.operation,
            "status": self.status,
            "origin": self.origin.value,
            "provenance": self.provenance,
            "evidence_refs": list(self.evidence_refs),
            "correlation_id": self.correlation_id,
            "app_version": self.app_version,
            "contract_version": self.contract_version,
            "duration_ms": self.duration_ms,
            "error_kind": self.error_kind,
        }


def _require_keys(data: Mapping[str, Any], required: set[str]) -> None:
    missing = required - set(data)
    if missing:
        raise EventValidationError("event is missing required fields: " + ", ".join(sorted(missing)))


def _redact(value: Any) -> Any:
    if isinstance(value, str):
        if _looks_secret(value):
            return "[REDACTED]"
        return value
    if isinstance(value, Mapping):
        return {str(key): _redact(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_redact(item) for item in value]
    return value


def _looks_secret(value: str) -> bool:
    return any(pattern.search(value) for pattern in _SECRET_PATTERNS)


def _validate_no_secret_material(event: IntegrationEvent) -> None:
    payload = event.to_dict()
    if _looks_secret(str(payload)):
        # Narrow the check to ordinary scalar fields to avoid false positives in
        # ISO timestamps, identifiers and digest-like evidence references.
        for field_value in (
            event.provenance,
            event.operation,
            event.error_kind or "",
            event.source,
        ):
            if _looks_secret(field_value):
                raise EventValidationError("event contains obvious secret material")


@dataclass(slots=True)
class EventCollector:
    """In-memory event collector isolated by application and instance."""

    max_events_per_scope: int = 1000
    store: Any | None = None
    _events: dict[tuple[str, str], deque[IntegrationEvent]] = field(
        default_factory=lambda: defaultdict(deque)
    )
    _by_id: dict[str, IntegrationEvent] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.store is not None:
            try:
                for payload in self.store.load_records("observability_events"):
                    try:
                        self._events[(str(payload["app_id"]), str(payload["instance_id"]))].append(
                            IntegrationEvent.from_mapping(payload)
                        )
                        self._by_id[str(payload["event_id"])] = IntegrationEvent.from_mapping(payload)
                    except Exception:
                        continue
            except Exception:
                pass

    def record(self, event: IntegrationEvent | Mapping[str, Any]) -> IntegrationEvent:
        if isinstance(event, IntegrationEvent):
            parsed = event
        else:
            parsed = IntegrationEvent.from_mapping(event)
        parsed.validate()
        redacted_event = _redact_event(parsed)
        key = (redacted_event.app_id, redacted_event.instance_id)
        queue = self._events[key]
        queue.append(redacted_event)
        while len(queue) > self.max_events_per_scope:
            removed = queue.popleft()
            self._by_id.pop(removed.event_id, None)
        self._by_id[redacted_event.event_id] = redacted_event
        if self.store is not None:
            try:
                self.store.save_record("observability_events", redacted_event.event_id, redacted_event.to_dict())
            except Exception:
                pass
        return redacted_event

    def record_safe(self, event: IntegrationEvent | Mapping[str, Any]) -> bool:
        try:
            self.record(event)
            return True
        except Exception:
            return False

    def get(self, event_id: str) -> IntegrationEvent | None:
        return self._by_id.get(event_id)

    def list_events(
        self,
        *,
        app_id: str | None = None,
        instance_id: str | None = None,
        event_type: str | None = None,
        status: str | None = None,
        origin: EventOrigin | str | None = None,
        correlation_id: str | None = None,
        since: datetime | None = None,
        limit: int | None = None,
    ) -> tuple[IntegrationEvent, ...]:
        origin_value = None if origin is None else (origin.value if isinstance(origin, EventOrigin) else str(origin))
        result: list[IntegrationEvent] = []
        for (stored_app, stored_instance), queue in self._events.items():
            if app_id is not None and stored_app != app_id:
                continue
            if instance_id is not None and stored_instance != instance_id:
                continue
            for event in queue:
                if event_type is not None and event.event_type != event_type:
                    continue
                if status is not None and event.status != status:
                    continue
                if origin_value is not None and event.origin.value != origin_value:
                    continue
                if correlation_id is not None and event.correlation_id != correlation_id:
                    continue
                if since is not None and event.timestamp < since:
                    continue
                result.append(event)
        result.sort(key=lambda item: (item.timestamp, item.event_id))
        if limit is not None and limit >= 0:
            result = result[:limit]
        return tuple(result)

    def count(self, app_id: str | None = None, instance_id: str | None = None) -> int:
        return len(self.list_events(app_id=app_id, instance_id=instance_id))

    def clear(self, app_id: str | None = None, instance_id: str | None = None) -> None:
        if app_id is None and instance_id is None:
            self._events.clear()
            self._by_id.clear()
            return
        keys = [key for key in self._events if (app_id is None or key[0] == app_id) and (instance_id is None or key[1] == instance_id)]
        for key in keys:
            for event in self._events.pop(key, ()):
                self._by_id.pop(event.event_id, None)

    def list_scopes(self) -> tuple[tuple[str, str], ...]:
        return tuple(sorted(self._events))


@dataclass(slots=True)
class EngineeringMemoryPromotionFilter:
    """Selects events suitable for Engineering Memory without dumping logs."""

    memory_worthy_types: frozenset[str] = MEMORY_WORTHY_EVENT_TYPES
    allowed_origins: frozenset[EventOrigin] = frozenset({EventOrigin.VERIFIED})

    def is_memory_worthy(self, event: IntegrationEvent) -> bool:
        if event.event_type in OPERATIONAL_ONLY_EVENT_TYPES:
            return False
        if event.event_type not in self.memory_worthy_types:
            return False
        if event.origin not in self.allowed_origins:
            return False
        if not event.evidence_refs:
            return False
        return True

    def promote(self, event: IntegrationEvent) -> dict[str, Any] | None:
        if not self.is_memory_worthy(event):
            return None
        return event.to_memory_entry()


def _redact_event(event: IntegrationEvent) -> IntegrationEvent:
    # String fields are redacted; evidence refs and identifiers remain as they
    # are expected to be non-secret references, not values.
    redacted = IntegrationEvent(
        event_id=_redact_string(event.event_id),
        schema_version=event.schema_version,
        app_id=_redact_string(event.app_id),
        instance_id=_redact_string(event.instance_id),
        timestamp=event.timestamp,
        event_type=_redact_string(event.event_type),
        operation=_redact_string(event.operation),
        status=event.status,
        provenance=_redact_string(event.provenance),
        evidence_refs=tuple(_redact_string(ref) for ref in event.evidence_refs),
        correlation_id=None if event.correlation_id is None else _redact_string(event.correlation_id),
        duration_ms=event.duration_ms,
        error_kind=None if event.error_kind is None else _redact_string(event.error_kind),
        source=_redact_string(event.source),
        app_version=event.app_version,
        contract_version=event.contract_version,
        origin=event.origin,
    )
    redacted.validate()
    return redacted


def _redact_string(value: str) -> str:
    if _contains_secret_string(value):
        return "[REDACTED]"
    return value


def _contains_secret_string(value: str) -> bool:
    return any(pattern.search(value) for pattern in _SECRET_PATTERNS)


# Aliases.
ObservabilityCollector = EventCollector
ApplicationEventCollector = EventCollector
ApplicationEvent = IntegrationEvent
IntegrationEventCollector = EventCollector
EngineeringMemoryFilter = EngineeringMemoryPromotionFilter
EventPromotionFilter = EngineeringMemoryPromotionFilter


__all__ = [
    "EngineeringMemoryFilter",
    "EngineeringMemoryPromotionFilter",
    "EventCollector",
    "EventOrigin",
    "EventStatus",
    "EventValidationError",
    "IntegrationEvent",
    "OBSERVABILITY_SCHEMA_VERSION",
]
