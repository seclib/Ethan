import tempfile
from pathlib import Path

from core.applications import ApplicationIntegrationRegistry, ApplicationStateStore
from core.applications.frame_integration import register_frame_pilot


def test_frame_manifest_validates_and_registers() -> None:
    with tempfile.TemporaryDirectory() as directory:
        store = ApplicationStateStore(Path(directory) / "state.sqlite")
        registry = ApplicationIntegrationRegistry(store=store)
        record = register_frame_pilot(registry)
        assert record.app_id == "frame"
        assert record.state.value == "registered"
        assert record.available is False
        assert len(record.capabilities) == 6
        store.close()

        restarted_store = ApplicationStateStore(Path(directory) / "state.sqlite")
        restarted_registry = ApplicationIntegrationRegistry(store=restarted_store)
        assert restarted_registry.get("frame", "frame-local-default") is not None
        restarted_store.close()
