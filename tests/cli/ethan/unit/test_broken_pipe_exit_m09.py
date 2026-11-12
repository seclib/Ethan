"""Tests ciblés M09 — exit 141 pour un tube rompu (CLI_CONTRACT.md §5, code réservé).

Sans branche dédiée, `BrokenPipeError` (sous-classe de `ConnectionError`) est
re-étiqueté « Core API unreachable » par le dispatch : le diagnostic est
mensonger et l'exit code (5) ne décrit pas un client dont le lecteur aval a
fermé stdout. Le contrat réserve désormais 141 (convention Unix 128 + SIGPIPE).
"""

from __future__ import annotations

import pytest
from interfaces.cli.core.context import set_context
from interfaces.cli.main import main
from interfaces.cli.registry import COMMAND_HANDLERS


@pytest.fixture(autouse=True)
def _clean_context():
    from interfaces.cli.core.context import CLIContext

    set_context(CLIContext(output="human", timeout=5.0))
    yield
    set_context(CLIContext(output="human", timeout=5.0))


def test_broken_pipe_exits_141(monkeypatch, capsys) -> None:
    """Un handler interrompu par la fermeture de stdout sort 141, pas 5."""
    calls = []

    def _handler(args):
        calls.append(args)
        raise BrokenPipeError(32, "Broken pipe")

    with monkeypatch.context() as mp:
        mp.setitem(COMMAND_HANDLERS, "m09pipe", _handler)
        mp.setattr("sys.argv", ["ethan", "m09pipe"])
        with pytest.raises(SystemExit) as exc:
            main()

    assert calls == [[]]
    assert exc.value.code == 141
    err = capsys.readouterr().err
    # Le diagnostic ne doit plus être un mensonge d'indisponibilité API.
    assert "Core API unreachable" not in err
    assert "broken pipe" in err


def test_broken_pipe_json_mode_error_on_stderr(monkeypatch, capsys) -> None:
    """En mode json, stdout reste propre et l'erreur structurée va sur stderr."""
    import json

    def _handler(args):
        raise BrokenPipeError(32, "Broken pipe")

    with monkeypatch.context() as mp:
        mp.setitem(COMMAND_HANDLERS, "m09pipe", _handler)
        mp.setattr("sys.argv", ["ethan", "-o", "json", "m09pipe"])
        with pytest.raises(SystemExit) as exc:
            main()

    assert exc.value.code == 141
    captured = capsys.readouterr()
    assert captured.out == ""
    payload = json.loads(captured.err)
    assert payload["error"]["code"] == "broken_pipe"
