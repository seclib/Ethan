from core.applications import (
    ExtensionContract,
    ExtensionContractValidator,
    IntegrationType,
)


def valid_contract_data() -> dict[str, object]:
    return {
        "identity": {
            "app_id": "alpha",
            "instance_id": "instance-a",
            "name": "Alpha",
            "version": "1.0.0",
            "contract_version": "1.0.0",
            "publisher": "Publisher",
            "manifest_version": 1,
        },
        "integration_type": "application",
        "capabilities": ["read-health"],
        "requested_permissions": ["read-health:execute"],
        "permission_requirements": {"read-health:execute": "read-health"},
    }


def test_valid_contract_and_compatible_versions() -> None:
    contract = ExtensionContract.from_mapping(valid_contract_data())
    assert contract.integration_type == IntegrationType.APPLICATION
    assert contract.requested_permissions == ["read-health:execute"]

    validator = ExtensionContractValidator()
    result = validator.validate(valid_contract_data())
    assert result.is_valid is True
    assert result.status == "valid"


def test_incomplete_contract_is_incomplete() -> None:
    validator = ExtensionContractValidator()
    data = valid_contract_data()
    del data["identity"]["app_id"]
    result = validator.validate(data)
    assert result.is_valid is False
    assert result.status == "incomplete"


def test_unknown_fields_do_not_crash_and_invalid_type() -> None:
    validator = ExtensionContractValidator()
    data = valid_contract_data()
    data["unexpected"] = "value"
    result = validator.validate(data)
    # The manifest layer rejects unknown fields, preserving strictness.
    assert result.is_valid is False
    assert result.status == "invalid"

    data2 = valid_contract_data()
    data2["integration_type"] = "unsupported-type"
    result2 = validator.validate(data2)
    assert result2.is_valid is False
    assert result2.status == "invalid"


def test_undeclared_capability_permission_is_invalid() -> None:
    validator = ExtensionContractValidator()
    data = valid_contract_data()
    data["requested_permissions"] = ["admin:all"]
    result = validator.validate(data)
    assert result.is_valid is False
    assert result.status == "invalid"
    assert "compatible" in " ".join(result.errors)


def test_incompatible_contract_version() -> None:
    validator = ExtensionContractValidator()
    data = valid_contract_data()
    data["identity"]["contract_version"] = "2.0.0"
    result = validator.validate(data)
    assert result.is_valid is False
    assert result.status == "incompatible"


def test_integration_types_are_distinct() -> None:
    for integration_type in ("application", "plugin", "extension", "skill"):
        data = valid_contract_data()
        data["integration_type"] = integration_type
        contract = ExtensionContract.from_mapping(data)
        assert contract.integration_type.value == integration_type


def test_contract_does_not_execute_or_create_adapter() -> None:
    # Construction and validation are purely declarative and create no adapter.
    data = valid_contract_data()
    contract = ExtensionContract.from_mapping(data)
    assert contract.adapters == []
    assert contract.to_dict()["integration_type"] == "application"
