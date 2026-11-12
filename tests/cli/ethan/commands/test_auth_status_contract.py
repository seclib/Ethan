"""Tests ciblés M09 — contrat `ethan auth status` (CLI_CONTRACT.md §7.3, §5).

- `-o json` renvoie l'objet `/auth/me` du Core tel quel (probe de session) ;
- absence de session → exit 3 (AUTH), erreur structurée sur stderr, stdout propre ;
- 401 du Core → exit 3 ; 403 → exit 4 (mapping figé §5) ;
- le mode humain conserve son message.

La frontière HTTP est mockée : aucun socket, aucun secret réel.
"""

from __future__ import annotations

import importlib
import json

import pytest
from interfaces.cli.core.context import CLIContext, set_context
from interfaces.cli.core.errors import CLIError
from interfaces.cli.core.exit_codes import ExitCode

ME = {"user": {"username": "admin", "role": "admin"}, "permissions": ["read"]}


@pytest.fixture(autouse=True)
def _clean_context():
    """Chaque test démarre d'un contexte pristine en mode humain."""
    set_context(CLIContext(output="human", timeout=5.0))
    yield
    set_context(CLIContext(output="human", timeout=5.0))


def _cmd_auth():
    module = importlib.import_module("interfaces.cli.commands.auth")
    return module.cmd_auth


def test_json_mode_returns_auth_me_object(core, capsys, monkeypatch) -> None:
    """§7.3 : en mode json, le document /auth/me est passé tel quel."""
    monkeypatch.setattr("interfaces.cli.core.client.get_token", lambda: "tok")
    core.payload = dict(ME)
    set_context(CLIContext(output="json", timeout=5.0))

    assert _cmd_auth()(["status"]) == ExitCode.SUCCESS

    captured = capsys.readouterr()
    assert json.loads(captured.out) == ME  # §4.2 : le CLI ne renomme ni ne masque rien


def test_human_mode_keeps_session_message(core, capsys, monkeypatch) -> None:
    monkeypatch.setattr("interfaces.cli.core.client.get_token", lambda: "tok")
    core.payload = dict(ME)

    assert _cmd_auth()(["status"]) == ExitCode.SUCCESS

    out = capsys.readouterr().out
    assert "Logged in as admin" in out
    assert "(admin)" in out


def test_not_logged_in_is_exit_3_with_structured_error(capsys, monkeypatch) -> None:
    """§5 : session absente → exit 3 (AUTH), jamais 1."""
    monkeypatch.setattr("interfaces.cli.core.client.get_token", lambda: None)

    with pytest.raises(CLIError) as err:
        _cmd_auth()(["status"])

    assert err.value.exit_code == ExitCode.AUTH
    assert err.value.hint == "ethan auth login"


def test_401_maps_to_exit_3(monkeypatch) -> None:
    """§5 : 401 du Core → exit 3, jamais 1."""
    from interfaces.cli.core.client import APIError

    def _raise(*args, **kwargs):
        raise APIError(401, "Authentification requise")

    monkeypatch.setattr("interfaces.cli.core.client.get_token", lambda: "tok")
    monkeypatch.setattr("interfaces.cli.core.client.request_json", _raise)

    with pytest.raises(CLIError) as err:
        _cmd_auth()(["status"])

    assert err.value.exit_code == ExitCode.AUTH


def test_403_maps_to_exit_4(monkeypatch) -> None:
    """§5 : 403 du Core → exit 4 (FORBIDDEN)."""
    from interfaces.cli.core.client import APIError

    def _raise(*args, **kwargs):
        raise APIError(403, "Permission manquante")

    monkeypatch.setattr("interfaces.cli.core.client.get_token", lambda: "tok")
    monkeypatch.setattr("interfaces.cli.core.client.request_json", _raise)

    with pytest.raises(CLIError) as err:
        _cmd_auth()(["status"])

    assert err.value.exit_code == ExitCode.FORBIDDEN
