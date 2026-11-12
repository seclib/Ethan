from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest
import yaml

from core.applications import ApplicationIdentity, ApplicationManifest, ContractValidator
from core.applications.models import ValidationError


def valid_manifest_dict() -> dict[str, object]:
	return {
		"identity": {
			"app_id": "trading-agents",
			"instance_id": "instance-a",
			"name": "TradingAgents",
			"version": "0.7.1",
			"contract_version": "1.0.0",
			"publisher": "TauricResearch",
			"manifest_version": 1,
		},
		"capabilities": ["research-analysis", "reports"],
		"dependencies": [{"name": "python", "version": ">=3.11"}],
		"compatibility": ["ethan 2026.05"],
		"interfaces": {"cli": {"entrypoint": "tradingagents analyze"}},
		"permissions": ["read:system-health"],
		"provenance": {"source": "git", "digest": "17f4307a216ed8854291bfcc554681d798ee96fd1b9f8700cfd786a6f3821f64"},
	}


def test_valid_manifest_is_accepted() -> None:
	validator = ContractValidator()
	result = validator.validate_manifest_data(valid_manifest_dict())
	assert result.is_valid is True
	assert result.status == "valid"
	assert result.errors == ()


def test_yaml_manifest_is_loaded(tmp_path: Path) -> None:
	validator = ContractValidator()
	file_path = tmp_path / "manifest.yaml"
	file_path.write_text(yaml.safe_dump(valid_manifest_dict(), sort_keys=False), encoding="utf-8")
	result = validator.validate_manifest_file(file_path)
	assert result.is_valid is True
	assert result.identity is not None


def test_invalid_yaml_is_rejected(tmp_path: Path) -> None:
	validator = ContractValidator()
	file_path = tmp_path / "manifest.yaml"
	file_path.write_text(":\n  - broken", encoding="utf-8")
	result = validator.validate_manifest_file(file_path)
	assert result.is_valid is False
	assert result.status == "invalid"


def test_missing_required_fields_are_rejected() -> None:
	validator = ContractValidator()
	data = valid_manifest_dict()
	del data["identity"]["app_id"]
	result = validator.validate_manifest_data(data)
	assert result.is_valid is False
	assert result.status == "incomplete"
	assert any("app_id" in message for message in result.errors)


def test_bad_id_is_rejected() -> None:
	validator = ContractValidator()
	data = valid_manifest_dict()
	data["identity"]["app_id"] = "../evil"
	result = validator.validate_manifest_data(data)
	assert result.is_valid is False
	assert "app_id" in " ".join(result.errors)


def test_bad_version_is_rejected() -> None:
	validator = ContractValidator()
	data = valid_manifest_dict()
	data["identity"]["version"] = "latest"
	result = validator.validate_manifest_data(data)
	assert result.is_valid is False
	assert "version" in " ".join(result.errors)


def test_missing_permission_is_declared_explicitly() -> None:
	data = valid_manifest_dict()
	data["identity"]["app_id"] = "trading-agents"
	manifest = ApplicationManifest.from_dict(data)
	assert manifest.permissions == ["read:system-health"]


def test_json_schema_has_required_top_level_fields() -> None:
	schema = ApplicationManifest.json_schema()
	assert schema["required"] == ["identity"]
	assert "capabilities" in schema["properties"]
	assert "dependencies" in schema["properties"]
