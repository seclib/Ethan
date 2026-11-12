from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from core.applications import ApplicationManifest, ContractValidator, ValidationError


def minimal_manifest(app_id: str = "a") -> dict[str, object]:
    return {
        "identity": {
            "app_id": app_id,
            "instance_id": "instance-a",
            "name": "App",
            "version": "1.0.0",
            "contract_version": "1.0.0",
            "publisher": "Publisher",
            "manifest_version": 1,
        }
    }


def test_one_character_identifier_is_allowed() -> None:
    validator = ContractValidator()
    result = validator.validate_manifest_data(minimal_manifest("z"))
    assert result.is_valid is True
    assert result.status == "valid"


def test_contract_version_mismatch_is_incompatible() -> None:
    validator = ContractValidator()
    data = minimal_manifest()
    data["identity"]["contract_version"] = "2.0.0"
    result = validator.validate_manifest_data(data)
    assert result.is_valid is False
    assert result.status == "incompatible"


def test_unauthorized_root_field_is_invalid() -> None:
    validator = ContractValidator()
    data = minimal_manifest()
    data["unexpected"] = "value"
    result = validator.validate_manifest_data(data)
    assert result.is_valid is False
    assert result.status == "invalid"
    assert "unauthorized" in " ".join(result.errors)


def test_missing_identity_is_incomplete() -> None:
    validator = ContractValidator()
    result = validator.validate_manifest_data({"capabilities": []})
    assert result.is_valid is False
    assert result.status == "incomplete"


def test_malformed_yaml_is_invalid() -> None:
    validator = ContractValidator()
    with TemporaryDirectory() as directory:
        path = Path(directory) / "manifest.yaml"
        path.write_text("identity:\n  - [broken\n", encoding="utf-8")
        result = validator.validate_manifest_file(path)
    assert result.is_valid is False
    assert result.status == "invalid"


def test_bad_version_is_invalid() -> None:
    validator = ContractValidator()
    data = minimal_manifest()
    data["identity"]["version"] = "latest"
    result = validator.validate_manifest_data(data)
    assert result.is_valid is False
    assert result.status == "invalid"


def test_secret_assignment_is_detected_without_value_disclosure() -> None:
    validator = ContractValidator()
    data = minimal_manifest()
    data["metadata"] = {"token": "api_key=super-secret-value"}
    result = validator.validate_manifest_data(data)
    assert result.is_valid is False
    assert result.status == "invalid"
    assert "super-secret-value" not in " ".join(result.errors)


def test_validate_accepts_yaml_text() -> None:
    import yaml

    validator = ContractValidator()
    payload = yaml.safe_dump(minimal_manifest(), sort_keys=False)
    result = validator.validate(payload)
    assert result.is_valid is True
    assert result.status == "valid"


def test_from_yaml_and_to_yaml_roundtrip() -> None:
    manifest = ApplicationManifest.from_yaml(
        "identity:\n  app_id: roundtrip\n  instance_id: instance-1\n"
        "  name: Roundtrip\n  version: 1.0.0\n  contract_version: 1.0.0\n"
        "  publisher: Publisher\n  manifest_version: 1\n"
    )
    reparsed = ApplicationManifest.from_yaml(manifest.to_yaml())
    assert reparsed.identity.app_id == "roundtrip"
    assert reparsed.identity.instance_id == "instance-1"


def test_float_manifest_version_rejected() -> None:
    validator = ContractValidator()
    data = minimal_manifest()
    data["identity"]["manifest_version"] = 1.5
    result = validator.validate_manifest_data(data)
    assert result.is_valid is False
    assert result.status == "invalid"


def test_non_boolean_required_rejected() -> None:
    validator = ContractValidator()
    data = minimal_manifest()
    data["dependencies"] = [{"name": "python", "version": ">=3.11", "required": 1}]
    result = validator.validate_manifest_data(data)
    assert result.is_valid is False
    assert result.status == "invalid"
