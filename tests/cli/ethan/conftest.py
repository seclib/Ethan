"""Shared fixtures and configuration for ETHAN CLI tests.

All tests that touch filesystem use tmp_path. Network calls are mocked.
The global COMMANDS registry is isolated per test session.
"""

from __future__ import annotations

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
import json
import os
import pkgutil
import sys
from pathlib import Path
from typing import Any, Generator
from unittest import mock

import pytest

_REPO_ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# Mode fidélité (diagnostic) : désactive l'alias quand le module cible vient
# d'un autre arbre que le repo. Utile pour vérifier qu'un échec vient bien du
# code testé et non de la résolution de modules.
#   ETHAN_CONFTEST_FIDELITY=1 pytest tests/cli/...
_FIDELITY = os.environ.get("ETHAN_CONFTEST_FIDELITY") == "1"


def _in_repo(mod) -> bool:
    """True si le module a été chargé depuis l'arbre du repo courant."""
    path = getattr(mod, "__file__", None)
    return bool(path) and _REPO_ROOT in os.path.realpath(path)


def _purge_stale_modules() -> None:
    """Purge les modules `cli`/`core` chargés depuis un AUTRE arbre que le repo.

    Dette d'environnement : si le virtualenv contient un paquet `cli`/`core`
    homonyme (ancien wheel installé), il est résolu AVANT la racine projet
    (`pythonpath=[".", "interfaces"]` est ajouté en fin de `sys.path`,
    site-packages passe avant). Les tests exécutent alors du code obsolète,
    produisant des échecs non corrélés aux sources. On purge, puis les imports
    se résolvent vers l'arbre courant.
    """
    purged = []
    for name, mod in list(sys.modules.items()):
        if not (name == "cli" or name.startswith(("cli.", "core"))):
            continue
        if _in_repo(mod) or getattr(mod, "__file__", None) is None:
            continue
        del sys.modules[name]
        purged.append(f"{name} → {mod.__file__}")
    if purged:
        print(
            "\n[conftest] modules hors-repo purgés (venv pollué) :\n  - "
            + "\n  - ".join(purged[:10])
        )


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
            alias = "cli." + fullname[len("interfaces.cli.") :]
        else:
            return None
        mod = sys.modules.get(alias)
        if mod is None:
            try:
                mod = importlib.import_module(alias)
            except ModuleNotFoundError:
                return None
        if _FIDELITY and not _in_repo(mod):
            # Mode fidélité : ne pas masquer un homonyme hors-repo, pour que
            # l'import suive le chemin réel (site-packages).
            return None
        return importlib.util.spec_from_loader(fullname, _CliAliasLoader(mod))


# Le finder doit être installé AVANT tout import applicatif pour intercepter
# les imports interfaces.cli.* (y compris lazy) — y compris ceux déclenchés
# par _load_cli_tree() ci-dessous (ex: chat.py fait
# `from interfaces.cli.core.client import send, alive` au chargement).
sys.meta_path.insert(0, _CliAliasFinder())
_purge_stale_modules()
_load_cli_tree()


@pytest.fixture(autouse=True)
def _reset_api_circuit_breaker() -> Generator[None, None, None]:
    """Réarme le disjoncteur API autour de chaque test.

    `cli.core.client._circuit_breaker` est un état GLOBAL : un test qui
    simule des échecs réseau l'ouvre pour tout le reste de la session, et les
    tests suivants court-circuitent sans appel réseau (échecs en cascade).
    """
    from interfaces.cli.core import client as _client

    _client.reset_circuit_breaker()
    yield
    _client.reset_circuit_breaker()


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

        if isinstance(url, str):
            url_str = url
        elif hasattr(url, "full_url"):
            url_str = url.full_url
        else:
            url_str = str(url)

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


# ── Seams mockés ───────────────────────────────────────────────────────────
# Les commandes importent leurs dépendances directement
# (`from cli.core.client import send, alive`) : la référence est alors liée
# dans le namespace du module CONSOMMATEUR. Patcher `cli.core.client.*` ne
# remplace donc pas `cli.commands.chat.alive` — cause des échecs en cascade sur
# les tests de chat. On patche le module client ET les consommateurs importés.
_CONSUMER_MODULES = (
    "cli.commands.chat",
    "cli.commands.status",
    "cli.commands.run",
    "cli.commands.think",
)


def _patch_seam(attr: str, new) -> list:
    """Patche `attr` dans cli.core.client et chez ses consommateurs importés."""
    patchers = [mock.patch(f"cli.core.client.{attr}", new)]
    for mod_name in _CONSUMER_MODULES:
        mod = sys.modules.get(mod_name)
        if mod is not None and hasattr(mod, attr):
            patchers.append(mock.patch.object(mod, attr, new))
    for patcher in patchers:
        patcher.start()
    return patchers


@pytest.fixture
def mock_client_send():
    """Mock le seam `send()` (module client + consommateurs)."""
    m = mock.MagicMock(return_value=("mock response", 42))
    patchers = _patch_seam("send", m)
    yield m
    for patcher in patchers:
        patcher.stop()


@pytest.fixture
def mock_client_alive():
    """Mock le seam `alive()` (module client + consommateurs)."""
    m = mock.MagicMock(return_value=True)
    patchers = _patch_seam("alive", m)
    yield m
    for patcher in patchers:
        patcher.stop()


@pytest.fixture
def mock_client_get_state():
    """Mock le seam `get_state()` (module client + consommateurs)."""
    m = mock.MagicMock(return_value={"mode": "running", "active_goal": "test", "running_tasks": 0})
    patchers = _patch_seam("get_state", m)
    yield m
    for patcher in patchers:
        patcher.stop()


@pytest.fixture
def mock_api_direct():
    """Réponse HTTP instantanée pour `cli.core.client.urlopen` (benchmarks).

    Fixture manquante auparavant : `benchmarks/test_api_latency.py` la
    référençait sans qu'elle existe → erreur de collecte du fichier entier.
    """
    payload = json.dumps({"response": "pong"}).encode()
    resp = mock.MagicMock()
    resp.status = 200
    resp.read.return_value = payload
    resp.__enter__.return_value = resp
    with mock.patch("cli.core.client.urlopen", return_value=resp) as m:
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
