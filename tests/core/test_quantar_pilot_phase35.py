import tempfile
from pathlib import Path

from core.applications import ApplicationIntegrationRegistry, ApplicationStateStore
from core.applications.quantar_integration import register_quantar_pilot


def test_quantar_registers_without_execution() -> None:
    with tempfile.TemporaryDirectory() as directory:
        store = ApplicationStateStore(Path(directory) / "state.sqlite")
        registry = ApplicationIntegrationRegistry(store=store)
        record = register_quantar_pilot(registry)
        assert record.app_id == "quantar"
        assert record.state.value == "registered"
        assert record.available is False
        assert set(record.capabilities) >= {"research-analysis", "reports"}
        store.close()
