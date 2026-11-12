import tempfile
from pathlib import Path

from core.applications import (
    ApplicationIntegrationRegistry,
    ApplicationStateStore,
)


def valid_manifest() -> dict[str, object]:
    return {
        "identity": {
            "app_id": "reference-app",
            "instance_id": "instance-1",
            "name": "Reference App",
            "version": "1.0.0",
            "contract_version": "1.0.0",
            "publisher": "ETHAN",
            "manifest_version": 1,
        },
        "capabilities": ["heartbeat"],
        "permissions": [],
        "provenance": {
            "source": "git",
            "digest": "17f4307a216ed8854291bfcc554681d798ee96fd1b9f8700cfd786a6f3821f64",
        },
    }


def test_register_and_persist_application() -> None:
    with tempfile.TemporaryDirectory() as directory:
        store = ApplicationStateStore(Path(directory) / "state.sqlite")
        registry = ApplicationIntegrationRegistry(store=store)
        record = registry.register(valid_manifest())
        assert record.state.value == "registered"
        assert record.app_id == "reference-app"
        store.close()

        restarted_store = ApplicationStateStore(Path(directory) / "state.sqlite")
        restarted_registry = ApplicationIntegrationRegistry(store=restarted_store)
        assert len(restarted_registry.list()) == 1
        restarted_store.close()


def test_duplicate_instance_is_rejected() -> None:
    with tempfile.TemporaryDirectory() as directory:
        registry = ApplicationIntegrationRegistry()
        registry.register(valid_manifest())
        try:
            registry.register(valid_manifest())
            raise AssertionError("duplicate registration accepted")
        except ValueError:
            pass


def test_invalid_manifest_is_rejected() -> None:
    with tempfile.TemporaryDirectory() as directory:
        registry = ApplicationIntegrationRegistry()
        data = valid_manifest()
        data["identity"]["app_id"] = "../bad"
        try:
            registry.register(data)
            raise AssertionError("invalid manifest accepted")
        except Exception:
            pass


def test_manifest_update_invalidates_state() -> None:
    with tempfile.TemporaryDirectory() as directory:
        registry = ApplicationIntegrationRegistry()
        record = registry.register(valid_manifest())
        updated = valid_manifest()
        updated["identity"]["version"] = "1.0.1"
        updated_record = registry.update_manifest(record.app_id, record.instance_id, updated)
        assert updated_record.manifest.identity.version == "1.0.1"
        assert updated_record.state.value == "validated"


def test_withdraw_and_health() -> None:
    with tempfile.TemporaryDirectory() as directory:
        registry = ApplicationIntegrationRegistry()
        record = registry.register(valid_manifest())
        withdrawn = registry.withdraw(record.app_id, record.instance_id, reason="test")
        assert withdrawn.available is False
        assert withdrawn.state.value == "withdrawn"
        health = registry.health_check(record.app_id, record.instance_id)
        assert health["available"] is False


def test_application_cannot_gain_permission_automatically() -> None:
    with tempfile.TemporaryDirectory() as directory:
        registry = ApplicationIntegrationRegistry()
        record = registry.register(valid_manifest())
        assert not hasattr(registry, "grant_permission")
        assert record.requested_permissions == ()
