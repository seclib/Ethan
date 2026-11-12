import tempfile
from pathlib import Path
from datetime import datetime, timezone

from core.applications import (
    ApplicationIntegrationRegistry,
    ApplicationStateStore,
    ComplianceEngine,
    EventCollector,
    EventOrigin,
    EventStatus,
    OBSERVABILITY_SCHEMA_VERSION,
    PermissionService,
)


def manifest_data(app_id: str = "reference-app") -> dict[str, object]:
    return {
        "identity": {
            "app_id": app_id,
            "instance_id": "instance-1",
            "name": "Reference App",
            "version": "1.0.0",
            "contract_version": "1.0.0",
            "publisher": "ETHAN",
            "manifest_version": 1,
        },
        "capabilities": [{"name": "heartbeat"}],
        "permissions": [],
        "provenance": {
            "source": "git",
            "digest": "17f4307a216ed8854291bfcc554681d798ee96fd1b9f8700cfd786a6f3821f64",
        },
    }


def test_e2e_nominal_parcours() -> None:
    with tempfile.TemporaryDirectory() as directory:
        store = ApplicationStateStore(Path(directory) / "state.sqlite")
        registry = ApplicationIntegrationRegistry(store=store)
        record = registry.register(manifest_data())
        assert record.state.value == "registered"
        assert record.compliance_status == "COMPLIANT"

        registry.mark_available(record.app_id, record.instance_id)
        health = registry.health_check(record.app_id, record.instance_id)
        assert health["available"] is True
        assert health["compliance_status"] == "COMPLIANT"

        collector = EventCollector(store=store)
        event = collector.record({
            "event_id": "health-event",
            "schema_version": OBSERVABILITY_SCHEMA_VERSION,
            "app_id": record.app_id,
            "instance_id": record.instance_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "status",
            "operation": "health_check",
            "status": EventStatus.SUCCEEDED.value,
            "provenance": "registry",
            "evidence_refs": [record.manifest_digest],
            "origin": "verified",
        })
        assert collector.count(app_id=record.app_id, instance_id=record.instance_id) == 1

        store.close()
        restarted_store = ApplicationStateStore(Path(directory) / "state.sqlite")
        restarted_registry = ApplicationIntegrationRegistry(store=restarted_store)
        assert restarted_registry.get(record.app_id, record.instance_id) is not None
        restarted_collector = EventCollector(store=restarted_store)
        assert restarted_collector.count() == 1
        restarted_store.close()


def test_e2e_negative_duplicate_instance() -> None:
    with tempfile.TemporaryDirectory() as directory:
        registry = ApplicationIntegrationRegistry()
        registry.register(manifest_data())
        try:
            registry.register(manifest_data())
            raise AssertionError("duplicate instance accepted")
        except ValueError:
            pass


def test_e2e_negative_invalid_manifest() -> None:
    with tempfile.TemporaryDirectory() as directory:
        registry = ApplicationIntegrationRegistry()
        data = manifest_data()
        data["identity"]["app_id"] = "../bad"
        try:
            registry.register(data)
            raise AssertionError("invalid manifest accepted")
        except Exception:
            pass


def test_e2e_permission_absent_is_denied() -> None:
    service = PermissionService()
    decision = service.authorize("reference-app", "instance-1", "unknown", "resource", "read")
    assert decision.decision.value == "deny"
    assert decision.reason_code == "NO_MATCHING_PERMISSION"


def test_e2e_unavailable_application_action_denied() -> None:
    with tempfile.TemporaryDirectory() as directory:
        registry = ApplicationIntegrationRegistry()
        record = registry.register(manifest_data())
        try:
            registry.request_permission_action(record.app_id, record.instance_id, "heartbeat", "resource", "read")
            raise AssertionError("action accepted for unavailable application")
        except ValueError:
            pass


def test_e2e_event_with_secret_is_rejected() -> None:
    collector = EventCollector()
    accepted = collector.record_safe({
        "event_id": "bad-event",
        "schema_version": OBSERVABILITY_SCHEMA_VERSION,
        "app_id": "reference-app",
        "instance_id": "instance-1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": "status",
        "operation": "test",
        "status": EventStatus.SUCCEEDED.value,
        "provenance": "password=secret",
        "evidence_refs": ["ref"],
        "origin": "verified",
    })
    assert accepted is False
    assert collector.count() == 0


def test_e2e_compliance_status_unchanged_after_restart() -> None:
    with tempfile.TemporaryDirectory() as directory:
        db = Path(directory) / "state.sqlite"
        store = ApplicationStateStore(db)
        registry = ApplicationIntegrationRegistry(store=store)
        record = registry.register(manifest_data())
        assert record.compliance_status == "COMPLIANT"
        store.close()

        restarted_store = ApplicationStateStore(db)
        restarted_registry = ApplicationIntegrationRegistry(store=restarted_store)
        restarted_record = restarted_registry.get(record.app_id, record.instance_id)
        assert restarted_record is not None
        assert restarted_record.compliance_status == "COMPLIANT"
        restarted_store.close()
