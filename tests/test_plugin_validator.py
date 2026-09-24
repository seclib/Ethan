"""Tests du validateur de plugins — capacité Core (P1-PLUGIN-01).

Valide :
  - le schéma manifest legacy (name/version/api_version) et Core
    (name/version/id) ;
  - les règles de code (imports/builtins interdits, syntaxe) ;
  - le shim legacy (une seule source de vérité : core/) ;
  - l'intégration dans PluginRegistry.install_custom().
"""

from __future__ import annotations

import asyncio

import pytest
from core.plugins import PluginRegistry, PluginValidator
from core.state import CoreRecordStore


class TestValidateManifest:
    def test_legacy_manifest_valid(self):
        result = PluginValidator().validate_manifest(
            {"name": "legacy-plugin", "version": "1.0.0", "api_version": "1"}
        )
        assert result.valid
        assert result.error == ""

    def test_core_manifest_valid(self):
        result = PluginValidator().validate_manifest(
            {"id": "mon-plugin", "name": "Mon Plugin", "version": "0.1.0"}
        )
        assert result.valid

    def test_missing_name_rejected(self):
        result = PluginValidator().validate_manifest({"version": "1.0.0", "id": "x"})
        assert not result.valid
        assert "name" in result.error

    def test_missing_version_rejected(self):
        result = PluginValidator().validate_manifest({"name": "x", "id": "x"})
        assert not result.valid
        assert "version" in result.error

    def test_blank_name_rejected(self):
        result = PluginValidator().validate_manifest({"name": "   ", "version": "1.0.0", "id": "x"})
        assert not result.valid
        assert "name" in result.error

    def test_missing_id_and_api_version_rejected(self):
        result = PluginValidator().validate_manifest({"name": "x", "version": "1.0.0"})
        assert not result.valid
        assert "id" in result.error

    def test_invalid_id_format_rejected(self):
        result = PluginValidator().validate_manifest(
            {"id": "Mon Plugin!", "name": "Mon Plugin", "version": "1.0.0"}
        )
        assert not result.valid
        assert "id" in result.error

    def test_uuid_like_id_accepted(self):
        result = PluginValidator().validate_manifest(
            {"id": "550e8400-e29b-41d4-a716-446655440000", "name": "x", "version": "1.0.0"}
        )
        assert result.valid


class TestValidateImports:
    def test_clean_code_valid(self, tmp_path):
        (tmp_path / "plugin.py").write_text("def run(x):\n    return x\n")
        assert PluginValidator().validate_imports(tmp_path).valid

    def test_forbidden_import_rejected(self, tmp_path):
        (tmp_path / "plugin.py").write_text("import os\n")
        result = PluginValidator().validate_imports(tmp_path)
        assert not result.valid
        assert "os" in result.error

    def test_forbidden_from_import_rejected(self, tmp_path):
        (tmp_path / "plugin.py").write_text("from subprocess import run\n")
        result = PluginValidator().validate_imports(tmp_path)
        assert not result.valid
        assert "subprocess" in result.error

    def test_forbidden_builtin_rejected(self, tmp_path):
        (tmp_path / "plugin.py").write_text('result = eval("1+1")\n')
        result = PluginValidator().validate_imports(tmp_path)
        assert not result.valid
        assert "eval" in result.error

    def test_syntax_error_rejected(self, tmp_path):
        (tmp_path / "plugin.py").write_text("def broken(:\n")
        result = PluginValidator().validate_imports(tmp_path)
        assert not result.valid
        assert "Syntax" in result.error

    def test_nested_subdir_scanned(self, tmp_path):
        sub = tmp_path / "helpers"
        sub.mkdir()
        (sub / "h.py").write_text("import socket\n")
        assert not PluginValidator().validate_imports(tmp_path).valid


class TestValidateComplete:
    def test_full_valid(self, tmp_path):
        (tmp_path / "plugin.py").write_text("def run():\n    return 1\n")
        result = PluginValidator().validate(
            tmp_path, {"name": "p", "version": "1.0.0", "api_version": "1"}
        )
        assert result.valid

    def test_manifest_error_reported_first(self, tmp_path):
        (tmp_path / "plugin.py").write_text("import os\n")
        result = PluginValidator().validate(tmp_path, {"version": "1.0.0"})
        assert not result.valid
        assert "name" in result.error


class TestShimCompat:
    def test_legacy_shim_reexports_core(self):
        from core.plugins import validator as core_validator

        import plugins.validator as legacy_shim

        assert legacy_shim.PluginValidator is core_validator.PluginValidator
        assert legacy_shim.ValidationResult is core_validator.ValidationResult


class TestRegistryIntegration:
    @pytest.fixture()
    def registry(self):
        return PluginRegistry(store=CoreRecordStore())

    def test_install_custom_valid_record(self, registry):
        installed = asyncio.run(registry.install_custom("Mon Plugin"))
        assert installed["name"] == "Mon Plugin"
        assert installed["installed"] is True

    def test_install_custom_kept_id_ok(self, registry):
        installed = asyncio.run(registry.install_custom("Mon Plugin", plugin_id="my-plugin"))
        assert installed["id"] == "my-plugin"

    def test_install_custom_blank_name_rejected(self, registry):
        with pytest.raises(ValueError, match="name"):
            asyncio.run(registry.install_custom("   "))

    def test_install_custom_invalid_id_rejected(self, registry):
        with pytest.raises(ValueError, match="id"):
            asyncio.run(registry.install_custom("Nom", plugin_id="Pas Valide!"))
