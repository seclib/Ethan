"""Shared fixtures and configuration for ETHAN CLI tests.

All tests that touch filesystem use tmp_path. Network calls are mocked.
The global COMMANDS registry is isolated per test session.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Generator
from unittest import mock

import pytest


# ── Alias de modules : interfaces.cli.* ≡ cli.* ────────────────────────────
# Les commandes CLI importent leurs dépendances via `interfaces.cli.*` (chemin
# absolu de prod) alors que les tests et monkeypatchs utilisent `cli.*`
# (alias exposé par pythonpath=["interfaces"]). Sans unification, les deux
# chemins chargent le MÊME fichier comme DEUX modules distincts et les mocks
# sont sans effet.
#
# Solution : un import hook (MetaPathFinder) qui route TOUT import de
# `interfaces.cli.*` — même lazy — vers l'objet `cli.*` déjà enregistré.
# Ce correctif est limité au conftest de test (aucune modification du code
# applicatif), conformément au principe « test-infra only ».

import importlib.abc
import importlib.util
import pkgutil


def _load_cli_tree() -> None:
    """Charge l'arbre cli.* complet pour que l'alias soit total."""
    import cli  # noqa: F401  (racine, via pythonpath=["interfaces"])

    for _m in pkgutil.walk_packages(cli.__path__, prefix="cli."):
        try:
            importlib.import_module(_m.name)
        except Exception:
            # Certaines feuilles (ex: hooks d'intégration) échouent hors
            # runtime ; l'import lazy par le code sous test les couvrira
            # via le finder ci-dessous.
            pass


class _CliAliasLoader(importlib.abc.Loader):
    """Loader renvoyant un module déjà existant (alias)."""

    def __init__(self, module) -> None:
        self._module = module

    def create_module(self, spec):
        return self._module

    def exec_module(self, module):  # déjà exécuté
        return None


class _CliAliasFinder(importlib.abc.MetaPathFinder):
    """Redirige interfaces.cli.* vers cli.* (même objet module)."""

    def find_spec(self, fullname, path=None, target=None):
        if fullname == "interfaces.cli":
            alias = "cli"
        elif fullname.startswith("interfaces.cli."):
            alias = "cli." + fullname[len("interfaces.cli."):]
        else:
            return None
        mod = sys.modules.get(alias)
        if mod is None:
            try:
                mod = importlib.import_module(alias)
            except ModuleNotFoundError:
                return None
        return importlib.util.spec_from_loader(fullname, _CliAliasLoader(mod))


# Le finder doit être installé AVANT tout import applicatif pour intercepter
# les imports interfaces.cli.* (y compris lazy) — y compris ceux déclenchés
# par _load_cli_tree() ci-dessous (ex: chat.py fait
# `from interfaces.cli.core.client import send, alive` au chargement).
sys.meta_path.insert(0, _CliAliasFinder())
_load_cli_tree()


@pytest.fixture(autouse=True)
def _alias_interfaces_modules():
    """No-op : l'alias est effectué au chargement du conftest (finder ci-dessus)."""
    yield


@pytest.fixture(autouse=True)
def _isolate_ethan_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Redirect ~/.ethan to a temp dir so tests never touch real files."""
    ethan_dir = tmp_path / ".ethan"
    ethan_dir.mkdir()
    monkeypatch.setattr("cli.core.memory.MEM_DIR", str(ethan_dir))
    monkeypatch.setattr("cli.core.memory.MEM_FILE", str(ethan_dir / "history.json"))
    monkeypatch.setattr("cli.core.memory.SESSION_FILE", str(ethan_dir / "session.txt"))
    monkeypatch.setattr("cli.core.logging.LOG_DIR", str(ethan_dir))
    monkeypatch.setattr("cli.core.logging.LOG_FILE", str(ethan_dir / "logs.json"))
    monkeypatch.setattr("cli.core.daemon.CACHE_DIR", str(ethan_dir))
    monkeypatch.setattr("cli.core.daemon.PID_FILE", str(ethan_dir / "ethan-daemon.pid"))
    monkeypatch.setattr("cli.core.daemon.CACHE_FILE", str(ethan_dir / "cache.json"))
    monkeypatch.setattr("cli.core.daemon.LOG_FILE", str(ethan_dir / "daemon.log"))
    monkeypatch.setattr("cli.core.first_run.FIRST_RUN_MARKER", str(ethan_dir / ".installed"))


@pytest.fixture(autouse=True)
def _isolate_config_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Redirect ~/.config/ethan to a temp dir."""
    config_dir = tmp_path / ".config" / "ethan"
    config_dir.mkdir(parents=True)
    monkeypatch.setattr("cli.core.config.CONFIG_DIR", config_dir)
    monkeypatch.setattr("cli.core.config.CONFIG_FILE", config_dir / "config.json")
    monkeypatch.setattr("cli.core.config.CONFIG_LOCAL_FILE", config_dir / "config.local.json")


@pytest.fixture(autouse=True)
def _clear_registry_before_test() -> Generator[None, None, None]:
    """Clear the global command registry between tests to avoid cross-contamination.

    NOTE: l'API de cli.registry a été renommée lors du rebuild :
    l'ancien dict global ``COMMANDS`` s'appelle désormais
    ``COMMAND_HANDLERS`` (la source de vérité étant cli.core.discovery.registry).
    """
    import cli.registry as reg

    saved = dict(reg.COMMAND_HANDLERS)
    reg.COMMAND_HANDLERS.clear()
    yield
    reg.COMMAND_HANDLERS.clear()
    reg.COMMAND_HANDLERS.update(saved)


@pytest.fixture
def mock_api_server():
    """Mock an HTTP API server for client tests.

    Returns a dict of functions to control responses per endpoint.
    """
    responses: dict[str, Any] = {
        "state_200": True,
        "state_data": {"mode": "running", "active_goal": "test", "running_tasks": 0},
        "message_response": {"response": "Hello from Ethan"},
        "raise_on": None,  # set to ("state"|"message", Exception) to simulate errors
    }

    def _urlopen_side_effect(url, *args, **kwargs):
        """Simulate urllib.request.urlopen responses."""
        from urllib.error import URLError

        url_str = url if isinstance(url, str) else url.full_url if hasattr(url, "full_url") else str(url)

        if responses.get("raise_on") and responses["raise_on"][0] in url_str:
            exc = responses["raise_on"][1]
            raise exc

        if "/state" in url_str:
            if not responses["state_200"]:
                raise URLError("Connection refused")
            data = json.dumps(responses["state_data"]).encode()
            # NOTE: l'ancien code mort (http.client.HTTPResponse.__new__ +
            # conn.begin()) levait une exception sans socket et faisait
            # échouer alive()/get_state() (exception avalée → False/None).
            # Le mock ci-dessous suffit (cf. test_client.TestAlive).
            mock_resp = mock.MagicMock()
            mock_resp.status = 200
            mock_resp.read.return_value = data
            mock_resp.__enter__.return_value = mock_resp
            return mock_resp

        if "/message" in url_str:
            data = json.dumps(responses["message_response"]).encode()
            mock_resp = mock.MagicMock()
            mock_resp.status = 200
            mock_resp.read.return_value = data
            mock_resp.__enter__.return_value = mock_resp
            return mock_resp

        raise ValueError(f"Unexpected URL: {url_str}")

    patcher = mock.patch("cli.core.client.urlopen", side_effect=_urlopen_side_effect)
    patcher.start()

    yield responses

    patcher.stop()


@pytest.fixture
def mock_client_send():
    """Mock cli.core.client.send() to return controlled (text, latency_ms)."""
    with mock.patch("cli.core.client.send") as m:
        m.return_value = ("mock response", 42)
        yield m


@pytest.fixture
def mock_client_alive():
    """Mock cli.core.client.alive() to simulate API state."""
    with mock.patch("cli.core.client.alive") as m:
        m.return_value = True
        yield m


@pytest.fixture
def mock_client_get_state():
    """Mock cli.core.client.get_state() to return controlled state."""
    with mock.patch("cli.core.client.get_state") as m:
        m.return_value = {"mode": "running", "active_goal": "test", "running_tasks": 0}
        yield m


@pytest.fixture
def captured_output():
    """Capture stdout for assertion.

    Returns a (buffer, tear_down) tuple.
    """
    from io import StringIO

    captured = StringIO()
    original = sys.stdout
    sys.stdout = captured

    def restore():
        sys.stdout = original
        return captured.getvalue()

    return captured, restore


@pytest.fixture
def registered_commands():
    """Register known test commands in the global COMMANDS dict."""
    from cli.registry import register

    @register("test_cmd")
    def _test_cmd(args):
        return 0

    @register("error_cmd")
    def _error_cmd(args):
        return 1

    @register("output_cmd")
    def _output_cmd(args):
        print("output_cmd executed")
        return 0

    return {"test_cmd", "error_cmd", "output_cmd"}


@pytest.fixture
def clear_registry():
    """Explicit registry clear (for tests that manipulate it directly)."""
    from cli.registry import COMMAND_HANDLERS

    saved = dict(COMMAND_HANDLERS)
    COMMAND_HANDLERS.clear()
    yield
    COMMAND_HANDLERS.clear()
    COMMAND_HANDLERS.update(saved)