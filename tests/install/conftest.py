"""Test fixtures for installer / cold-start refresh tests."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Quarantaine locale (miroir du collect_ignore global de tests/conftest.py).
#
# Ces tests importent `openjarvis.*`, paquet applicatif historique supprimé
# lors du rebuild (core/ + sdk/ + plugins/ + interfaces/). Le collect_ignore
# global ne s'applique PAS lorsque ce dossier est ciblé directement
# (`pytest tests/install`), d'où ce garde-fou local : sans le paquet
# `openjarvis`, aucun fichier n'est collecté (10 erreurs de collection avant).
#
# Ils redeviendront actifs automatiquement quand la migration
# openjarvis.* → core.* (RFC dédiée) sera réalisée.
# ---------------------------------------------------------------------------
collect_ignore_glob = []
if importlib.util.find_spec("openjarvis") is None:
    collect_ignore_glob += ["*.py", "*/*.py"]


@pytest.fixture
def tmp_openjarvis_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point ``DEFAULT_CONFIG_DIR`` at a tmpdir for isolated tests.

    Returns the directory; teardown is automatic via tmp_path.
    """
    home = tmp_path / ".openjarvis"
    home.mkdir()
    (home / ".state").mkdir()
    (home / ".state" / "models").mkdir()
    (home / ".scripts").mkdir()
    config_path = home / "config.toml"
    monkeypatch.setattr("openjarvis.core.config.DEFAULT_CONFIG_DIR", home)
    monkeypatch.setattr("openjarvis.core.config.DEFAULT_CONFIG_PATH", config_path)
    # Also patch init_cmd's module-level bindings (imported with ``from ... import``).
    monkeypatch.setattr("openjarvis.cli.init_cmd.DEFAULT_CONFIG_DIR", home)
    monkeypatch.setattr("openjarvis.cli.init_cmd.DEFAULT_CONFIG_PATH", config_path)
    # Patch doctor_cmd's module-level bindings.
    monkeypatch.setattr("openjarvis.cli.doctor_cmd.DEFAULT_CONFIG_PATH", config_path)
    monkeypatch.setenv("HOME", str(tmp_path))
    return home
