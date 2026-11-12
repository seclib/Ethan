import yaml
from pathlib import Path

from core.applications import ApplicationManifest, ContractValidator


def test_quantar_manifest_validates() -> None:
    path = Path("examples/quantar/ethan-application-manifest.yaml")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    manifest = ApplicationManifest.from_mapping(data)
    assert manifest.identity.app_id == "quantar"
    assert [capability.name for capability in manifest.capabilities] == ["research-analysis", "reports"]

    result = ContractValidator().validate_manifest_data(data)
    assert result.status == "valid"
