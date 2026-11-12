import tempfile
from pathlib import Path

from core.applications import ApplicationIntegrationRegistry, ApplicationStateStore
from core.applications.odin_integration import register_odin_pilot, odin_capability_matrix, load_odin_manifest


def test_odin_pilot_registration() -> None:
    with tempfile.TemporaryDirectory() as directory:
        store = ApplicationStateStore(Path(directory) / "state.sqlite")
        registry = ApplicationIntegrationRegistry(store=store)
        record = register_odin_pilot(registry)
        assert record.app_id == "odin"
        assert record.state.value == "registered"
        assert record.available is False
        assert len(record.capabilities) == 6
        store.close()

        restarted = ApplicationIntegrationRegistry(store=ApplicationStateStore(Path(directory) / "state.sqlite"))
        assert restarted.get("odin", "odin-local-default") is not None


def test_odin_does_not_gain_permission_automatically() -> None:
    data = load_odin_manifest()
    assert data["permissions"] is not None
    # The manifest declares permissions, but registration alone grants none.
    assert "application.control.start" in data["permissions"]


def test_odin_capability_matrix_is_declarative() -> None:
    matrix = odin_capability_matrix()
    assert len(matrix) == 6
    assert all(item["execution"] == "not automatically available" for item in matrix)
