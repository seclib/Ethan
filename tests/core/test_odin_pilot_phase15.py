import tempfile
from pathlib import Path

import yaml

from core.applications import ApplicationIntegrationRegistry, ApplicationStateStore
from core.applications.models import ApplicationManifest


def test_odin_manifest_validates() -> None:
    manifest_path = Path("examples/odin/ethan-application-manifest.yaml")
    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    manifest = ApplicationManifest.from_mapping(data)
    assert manifest.identity.app_id == "odin"
    assert len(manifest.capabilities) == 6


def test_odin_registers_without_automatic_permission() -> None:
    manifest_path = Path("examples/odin/ethan-application-manifest.yaml")
    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as directory:
        store = ApplicationStateStore(Path(directory) / "state.sqlite")
        registry = ApplicationIntegrationRegistry(store=store)
        record = registry.register(data)
        assert record.app_id == "odin"
        assert record.state.value == "registered"
        assert record.available is False
        store.close()


def test_odin_health_check_requires_availability() -> None:
    with tempfile.TemporaryDirectory() as directory:
        store = ApplicationStateStore(Path(directory) / "state.sqlite")
        registry = ApplicationIntegrationRegistry(store=store)
        manifest_path = Path("examples/odin/ethan-application-manifest.yaml")
        data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        record = registry.register(data)
        assert registry.health_check(record.app_id, record.instance_id)["available"] is False
        store.close()
