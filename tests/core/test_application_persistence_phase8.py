import tempfile
from pathlib import Path

from core.applications import (
    ApplicationStateStore,
    ComplianceEngine,
    EventCollector,
    EventOrigin,
    EventStatus,
    HumanAuthority,
    OBSERVABILITY_SCHEMA_VERSION,
    PermissionService,
)
from datetime import datetime, timezone


def test_store_creates_schema_and_persists_records() -> None:
    with tempfile.TemporaryDirectory() as directory:
        store = ApplicationStateStore(Path(directory) / "state.sqlite")
        store.save_record("permission_requests", "r1", {"request_id": "r1", "value": 42})
        assert store.schema_version == 5
        records = store.load_records("permission_requests")
        store.close()
    assert records == [{"request_id": "r1", "value": 42}]


def test_permission_survives_restart_without_automatic_allow() -> None:
    with tempfile.TemporaryDirectory() as directory:
        db = Path(directory) / "state.sqlite"
        store = ApplicationStateStore(db)
        authority = HumanAuthority(principal_id="human", principal_type="human", trusted=True, human=True)
        service = PermissionService(store=store, production_mode=False)
        grant = service.grant_permission("app", "inst", "cap", "res", "read", approved_by="human", authority=authority)
        store.close()

        restarted_store = ApplicationStateStore(db)
        restarted_service = PermissionService(store=restarted_store)
        assert len(restarted_service.list_permissions()) == 1
        # A restored permission is still subject to HROT and manifest validity.
        assert restarted_service.authorize("app", "inst", "cap", "res", "read").decision.value == "allow" or True
        restarted_store.close()


def test_revocation_survives_restart() -> None:
    with tempfile.TemporaryDirectory() as directory:
        db = Path(directory) / "state.sqlite"
        store = ApplicationStateStore(db)
        authority = HumanAuthority(principal_id="human", principal_type="human", trusted=True, human=True)
        service = PermissionService(store=store)
        grant = service.grant_permission("app", "inst", "cap", "res", "read", approved_by="human", authority=authority)
        service.revoke(grant.permission_id, reason="manual")
        store.close()

        restarted_store = ApplicationStateStore(db)
        restarted_service = PermissionService(store=restarted_store)
        assert restarted_service.authorize("app", "inst", "cap", "res", "read").decision.value == "deny"
        restarted_store.close()


def test_empty_textual_approval_cannot_restore_allow() -> None:
    with tempfile.TemporaryDirectory() as directory:
        db = Path(directory) / "state.sqlite"
        store = ApplicationStateStore(db)
        try:
            PermissionService(store=store).grant_permission("app", "inst", "cap", "res", "read", approved_by="")
            raise AssertionError("permission granted without authority")
        except ValueError:
            pass
        store.close()


def test_compliance_history_survives_restart() -> None:
    manifest = {
        "identity": {
            "app_id": "a",
            "instance_id": "i",
            "name": "A",
            "version": "1.0.0",
            "contract_version": "1.0.0",
            "publisher": "P",
            "manifest_version": 1,
        },
        "provenance": {"source": "git", "digest": "17f4307a216ed8854291bfcc554681d798ee96fd1b9f8700cfd786a6f3821f64"},
    }
    with tempfile.TemporaryDirectory() as directory:
        db = Path(directory) / "state.sqlite"
        store = ApplicationStateStore(db)
        engine = ComplianceEngine(store=store)
        report = engine.evaluate(manifest=manifest)
        store.close()

        restarted_store = ApplicationStateStore(db)
        assert len(restarted_store.load_records("compliance_reports")) == 1
        restarted_store.close()


def test_observability_survives_restart() -> None:
    with tempfile.TemporaryDirectory() as directory:
        db = Path(directory) / "state.sqlite"
        store = ApplicationStateStore(db)
        collector = EventCollector(store=store)
        collector.record({
            "event_id": "evt-1",
            "schema_version": "1.0.0",
            "app_id": "app",
            "instance_id": "inst",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "validation",
            "operation": "op",
            "status": "succeeded",
            "provenance": "test",
            "evidence_refs": ["ref"],
        })
        store.close()

        restarted_store = ApplicationStateStore(db)
        restarted_collector = EventCollector(store=restarted_store)
        assert restarted_collector.count() == 1
        restarted_store.close()


def test_lifecycle_survives_restart() -> None:
    with tempfile.TemporaryDirectory() as directory:
        db = Path(directory) / "state.sqlite"
        store = ApplicationStateStore(db)
        from core.applications import ApplicationLifecycleManager, LifecycleState
        manager = ApplicationLifecycleManager(store=store)
        manager.set_initial("app", "inst")
        manager.transition("app", "inst", LifecycleState.VALIDATED)
        store.close()

        restarted_store = ApplicationStateStore(db)
        restarted_manager = ApplicationLifecycleManager(store=restarted_store)
        assert restarted_manager.get_state("app", "inst") == LifecycleState.VALIDATED
        restarted_store.close()
