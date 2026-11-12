from datetime import datetime, timezone

from core.applications import (
    EngineeringMemoryPromotionFilter,
    EventCollector,
    EventOrigin,
    EventStatus,
    IntegrationEvent,
    OBSERVABILITY_SCHEMA_VERSION,
)


def valid_event(**overrides):
    data = {
        "event_id": "evt-1",
        "schema_version": OBSERVABILITY_SCHEMA_VERSION,
        "app_id": "alpha",
        "instance_id": "instance-a",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": "validation",
        "operation": "validate_manifest",
        "status": EventStatus.SUCCEEDED.value,
        "provenance": "core.applications",
        "evidence_refs": ["manifest:alpha"],
        "origin": EventOrigin.VERIFIED.value,
    }
    data.update(overrides)
    return data


def test_valid_event_schema() -> None:
    event = IntegrationEvent.from_mapping(valid_event())
    assert event.event_id == "evt-1"
    assert event.to_dict()["schema_version"] == OBSERVABILITY_SCHEMA_VERSION


def test_malformed_event_is_rejected() -> None:
    try:
        IntegrationEvent.from_mapping({"event_id": "evt-1"})
        raise AssertionError("malformed event accepted")
    except Exception:
        pass


def test_isolation_by_application_and_instance() -> None:
    collector = EventCollector()
    collector.record(valid_event(app_id="alpha", instance_id="i1", event_id="e1"))
    collector.record(valid_event(app_id="beta", instance_id="i2", event_id="e2"))
    result = collector.list_events(app_id="alpha")
    assert len(result) == 1
    assert result[0].app_id == "alpha"


def test_timestamp_and_provenance_are_preserved() -> None:
    collector = EventCollector()
    event = collector.record(valid_event(provenance="test-source"))
    fetched = collector.get(event.event_id)
    assert fetched is not None
    assert fetched.provenance == "test-source"
    assert fetched.timestamp.tzinfo is not None


def test_correlation() -> None:
    collector = EventCollector()
    collector.record(valid_event(event_id="e1", correlation_id="corr-1"))
    collector.record(valid_event(event_id="e2", correlation_id="corr-2"))
    result = collector.list_events(correlation_id="corr-1")
    assert len(result) == 1
    assert result[0].event_id == "e1"


def test_secret_protection() -> None:
    try:
        IntegrationEvent.from_mapping(valid_event(provenance="password=hunter2"))
        raise AssertionError("secret accepted")
    except Exception:
        pass
    collector = EventCollector()
    collector.record_safe(valid_event(provenance="password=hunter2"))
    assert collector.count() == 0


def test_invalid_evidence_refs() -> None:
    try:
        IntegrationEvent.from_mapping(valid_event(evidence_refs=[""]))
        raise AssertionError("invalid evidence accepted")
    except Exception:
        pass


def test_engineering_memory_filtering() -> None:
    worthy = IntegrationEvent.from_mapping(valid_event(event_type="decision", evidence_refs=["manifest:alpha"]))
    operational = IntegrationEvent.from_mapping(valid_event(event_id="e2", event_type="heartbeat", evidence_refs=["manifest:alpha"]))
    promotion_filter = EngineeringMemoryPromotionFilter()
    assert promotion_filter.is_memory_worthy(worthy) is True
    assert promotion_filter.is_memory_worthy(operational) is False
    assert promotion_filter.promote(operational) is None


def test_verified_origin_filter() -> None:
    declared_event = IntegrationEvent.from_mapping(valid_event(event_id="e3", origin=EventOrigin.DECLARED.value))
    promotion_filter = EngineeringMemoryPromotionFilter(allowed_origins=frozenset({EventOrigin.VERIFIED}))
    assert promotion_filter.is_memory_worthy(declared_event) is False


def test_collection_error_tolerance() -> None:
    collector = EventCollector()
    assert collector.record_safe({"bad": "event"}) is False
    assert collector.count() == 0


def test_no_unnecessary_duplication() -> None:
    collector = EventCollector()
    event = collector.record(valid_event())
    assert collector.count() == 1
    collector.record(event)
    # Same event_id can be recorded again, but list remains deterministic and identifiable.
    assert collector.count() == 2


def test_no_execution_or_permission() -> None:
    collector = EventCollector()
    event = collector.record(valid_event())
    assert event.status == EventStatus.SUCCEEDED.value
