"""Non-régression : la commande CLI `plugin` est découverte et dispatchée.

Régression détectée (post-rebuild) : les imports des modules de
commandes avaient disparu de ``interfaces/cli/main.py`` et
``discover_commands()`` n'était appelé nulle part en prod → toute
commande tombait dans le REPL de repli (hang sur stdin).  Ce test
prouve le dispatch complet : discovery dans ``main()`` + handler
``plugin`` + exit codes du validator Core.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_discover_registers_plugin_command():
    from interfaces.cli.registry import COMMAND_HANDLERS, discover_commands

    discover_commands()
    assert "plugin" in COMMAND_HANDLERS


def _run_cli(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "interfaces.cli.main", *args],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def test_cli_help_lists_discovered_plugin_command():
    result = _run_cli(["--help"])
    assert result.returncode == 0
    assert "plugin" in result.stdout


def test_cli_plugin_validate_valid_exit0(tmp_path):
    (tmp_path / "manifest.json").write_text(
        '{"name": "demo", "version": "1.0.0", "api_version": "2"}'
    )
    (tmp_path / "plugin.py").write_text("def run():\n    return 1\n")
    result = _run_cli(["plugin", "validate", str(tmp_path)])
    assert result.returncode == 0
    assert "valide" in (result.stdout + result.stderr)


def test_cli_plugin_validate_forbidden_import_exit1(tmp_path):
    (tmp_path / "manifest.json").write_text(
        '{"name": "bad", "version": "1.0.0", "api_version": "2"}'
    )
    (tmp_path / "plugin.py").write_text("import os\n")
    result = _run_cli(["plugin", "validate", str(tmp_path)])
    assert result.returncode == 1
    assert "os" in (result.stdout + result.stderr)


def test_cli_plugin_list_exit0():
    result = _run_cli(["plugin", "list"])
    assert result.returncode == 0


# ── Phase 4 : plus de conflit `plugin` (doublons fusionnés) ────────────────


def test_single_plugin_handler_after_fusion():
    """Un seul handler `plugin` : commands/plugin.py (plugin_cmd/plugins supprimés)."""
    from interfaces.cli.registry import COMMAND_HANDLERS, discover_commands

    discover_commands()
    fn = COMMAND_HANDLERS["plugin"]
    # discover charge une instance dédiée du module (spec_from_file) :
    # on vérifie le handler lui-même, pas l'identité d'objet.
    assert getattr(fn, "__name__", "") == "cmd_plugin"
    # L'ancien doublon `plugins` (supprimé) ne doit plus exister.
    assert "plugins" not in COMMAND_HANDLERS


def test_duplicated_command_modules_removed():
    import importlib.util

    for ghost in ("interfaces.cli.commands.plugin_cmd", "interfaces.cli.commands.plugins"):
        assert importlib.util.find_spec(ghost) is None, f"{ghost} doit être supprimé"


# ── plugin_manager : validation AST Core avant exécution (install) ─────────


def _write_plugin(dest, code: str):
    dest.mkdir()
    (dest / "plugin.py").write_text(code)


def test_install_rejects_forbidden_import(tmp_path, monkeypatch):
    import interfaces.cli.plugin_manager as pm

    monkeypatch.setattr(pm, "USER_PLUGIN_DIR", tmp_path / "user_plugins")
    src = tmp_path / "bad-plugin"
    _write_plugin(
        src,
        "import os\n"
        'ETHAN_PLUGIN = {"name": "bad", "version": "1.0.0", "api_version": "2"}\n',
    )
    assert pm.install(str(src)) is False
    # Le plugin rejeté ne doit pas persister dans le répertoire utilisateur.
    assert not (tmp_path / "user_plugins" / "bad-plugin").exists()


def test_install_accepts_clean_plugin_and_lists_it(tmp_path, monkeypatch):
    import interfaces.cli.plugin_manager as pm

    monkeypatch.setattr(pm, "USER_PLUGIN_DIR", tmp_path / "user_plugins")
    src = tmp_path / "clean-plugin"
    _write_plugin(
        src,
        'ETHAN_PLUGIN = {"name": "clean", "version": "1.2.3", "api_version": "2"}\n',
    )
    assert pm.install(str(src)) is True
    assert (tmp_path / "user_plugins" / "clean-plugin" / "plugin.py").exists()
    names = [p.get("name") for p in pm.list_installed()]
    assert "clean" in names
    # install() stocke sous le nom du dossier source (comportement historique).
    assert pm.remove("clean-plugin") is True