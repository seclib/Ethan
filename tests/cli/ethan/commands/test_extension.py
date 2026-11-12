"""Tests for the unified `ethan extension` family (contract §8.11).

One CLI family drives the ONE Core lifecycle for the three kinds
(`capability`, `plugin`, `cookbook`) — no per-kind CLI manager. Matrix:
list · info · install · error · enable · disable · uninstall · update ·
restart · persistence · permissions · JSON output — plus the async contract
(progress on stderr, timeout exit 7, interruption exit 130 + recovery, T8
destructive guard before ANY network call, frozen HTTP → exit codes §5).

The HTTP boundary is mocked by `core`: no socket, no bypass of the Core.
"""

from __future__ import annotations

import importlib
import json
from unittest import mock

import pytest
from interfaces.cli.core.context import CLIContext, set_context
from interfaces.cli.core.errors import CLIError
from interfaces.cli.core.exit_codes import ExitCode


@pytest.fixture(autouse=True)
def _clean_context():
    """Every test starts from a pristine human-mode context."""
    set_context(CLIContext(output="human", timeout=5.0))
    yield
    set_context(CLIContext(output="human", timeout=5.0))


@pytest.fixture
def ext():
    """The command module under test (namespace alias unified by conftest)."""
    return importlib.import_module("interfaces.cli.commands.extension")


@pytest.fixture
def handler(ext):
    return ext.cmd_extension


def _op(**overrides) -> dict:
    """A Core operation record (core/extensions/manager.py `_start_operation`)."""
    operation = {
        "operation_id": "opx_1",
        "extension_id": "cap-demo",
        "kind": "capability",
        "operation": "install",
        "status": "SUCCESS",
        "actor": "user",
        "progress": 100,
        "error": None,
        "done": True,
    }
    operation.update(overrides)
    return operation


def _item(**overrides) -> dict:
    """A Core `ExtensionStatus` row (spec + real state)."""
    item = {
        "id": "cap-demo",
        "kind": "capability",
        "state": "ENABLED",
        "enabled": True,
        "version": "1.0.0",
        "installed_version": "1.0.0",
        "last_error": None,
        "updated_at": "2026-10-05T00:00:00Z",
        "actions": ["disable"],
    }
    item.update(overrides)
    return item


# ── list ──────────────────────────────────────────────────────────────────────


class TestList:
    def test_list_calls_v1_extensions(self, handler, core) -> None:
        core.payload = {"extensions": []}
        assert handler(["list"]) == ExitCode.SUCCESS
        assert core.last[:2] == ("GET", "/v1/extensions")

    def test_list_shows_core_state_vocabulary(self, handler, core, capsys) -> None:
        core.payload = {
            "extensions": [
                _item(id="a", state="AVAILABLE", enabled=False),
                _item(id="b", state="INSTALLING"),
                _item(id="c", state="INSTALLED"),
                _item(id="d", state="ENABLED"),
                _item(id="e", state="DISABLED", enabled=False),
                _item(id="f", state="ERROR", enabled=False, last_error="boom"),
            ]
        }
        handler(["list"])
        out = capsys.readouterr().out
        for state in ("AVAILABLE", "INSTALLING", "INSTALLED", "ENABLED", "DISABLED", "ERROR"):
            assert state in out

    def test_list_kind_is_passed_to_core(self, handler, core) -> None:
        core.payload = {"extensions": []}
        handler(["list", "--kind", "cookbook"])
        assert core.last[1] == "/v1/extensions?kind=cookbook"

    def test_list_state_filter_selects_on_core_field(self, handler, core, capsys) -> None:
        core.payload = {
            "extensions": [
                _item(id="enabled-one", state="ENABLED"),
                _item(id="disabled-one", state="DISABLED", enabled=False),
            ]
        }
        handler(["list", "--state", "disabled"])
        out = capsys.readouterr().out
        assert "disabled-one" in out
        assert "enabled-one" not in out

    def test_list_query_filters_id_kind_state(self, handler, core, capsys) -> None:
        core.payload = {
            "extensions": [
                _item(id="cook-book", kind="cookbook"),
                _item(id="cap-demo", kind="capability"),
            ]
        }
        handler(["list", "--query", "cookbook"])
        out = capsys.readouterr().out
        assert "cook-book" in out
        assert "cap-demo" not in out

    def test_list_empty_prints_label(self, handler, core, capsys) -> None:
        core.payload = {"extensions": []}
        handler(["list"])
        assert "no extension" in capsys.readouterr().out


# ── info ──────────────────────────────────────────────────────────────────────


class TestInfo:
    def test_info_calls_extension_route(self, handler, core, capsys) -> None:
        core.payload = _item()
        assert handler(["info", "cap-demo"]) == ExitCode.SUCCESS
        assert core.last[:2] == ("GET", "/v1/extensions/cap-demo")
        out = capsys.readouterr().out
        assert "state" in out
        assert "ENABLED" in out

    def test_show_is_explicit_synonym_of_info(self, handler, core) -> None:
        core.payload = _item()
        handler(["show", "cap-demo"])
        assert core.last[:2] == ("GET", "/v1/extensions/cap-demo")

    def test_plan_and_logs_use_subroutes(self, handler, core) -> None:
        core.payload = {}
        handler(["plan", "cap-demo"])
        handler(["logs", "cap-demo"])
        assert core.calls[0][1] == "/v1/extensions/cap-demo/plan"
        assert core.calls[1][1] == "/v1/extensions/cap-demo/logs"

    def test_info_json_is_payload_untouched(self, handler, core, capsys) -> None:
        set_context(CLIContext(output="json", color=False))
        core.payload = _item()
        handler(["info", "cap-demo"])
        assert json.loads(capsys.readouterr().out) == _item()

    def test_missing_id_is_usage_error(self, handler, core) -> None:
        with pytest.raises(CLIError) as excinfo:
            handler(["info"])
        assert excinfo.value.exit_code == ExitCode.USAGE
        assert core.calls == []


# ── install: async lifecycle, progress, real errors ───────────────────────────


class TestInstall:
    def test_install_posts_then_polls_until_success(self, ext, handler, core) -> None:
        core.payloads = [{"operation_id": "opx_1"}]
        core.payload = _op()
        with mock.patch.object(ext, "POLL_INTERVAL", 0):
            assert handler(["install", "cap-demo"]) == ExitCode.SUCCESS
        assert core.calls[0][:2] == ("POST", "/v1/extensions/cap-demo/install")
        assert core.calls[1][:2] == ("GET", "/v1/extensions/operations/opx_1")

    def test_install_streams_progress_on_stderr_only(self, ext, handler, core, capsys) -> None:
        core.payloads = [
            {"operation_id": "opx_1"},
            _op(status="RUNNING", progress=40, done=False),
        ]
        core.payload = _op()
        with mock.patch.object(ext, "POLL_INTERVAL", 0):
            assert handler(["install", "cap-demo"]) == ExitCode.SUCCESS
        captured = capsys.readouterr()
        # La progression (champ `progress` du Core) vit sur stderr, pas stdout.
        assert "40%" in captured.err
        assert "RUNNING" in captured.err
        assert "accepted" in captured.err
        assert "opx_1" in captured.err
        # stdout reste le document final, sans décoration (§4.2).
        assert json.loads(captured.out)["status"] == "SUCCESS"

    def test_install_no_wait_returns_operation_immediately(self, handler, core, capsys) -> None:
        core.payload = {"operation_id": "opx_1", "extension_id": "cap-demo"}
        assert handler(["install", "cap-demo", "--no-wait"]) == ExitCode.SUCCESS
        assert len(core.calls) == 1
        out = capsys.readouterr()
        assert json.loads(out.out)["operation_id"] == "opx_1"
        assert "operation opx_1 accepted" in out.err

    @pytest.mark.parametrize("status", ["ERROR", "CANCELLED"])
    def test_failed_operation_is_exit_1_with_real_error(
        self, ext, handler, core, capsys, status
    ) -> None:
        core.payloads = [{"operation_id": "opx_1"}]
        core.payload = _op(status=status, error="pull failed: no space left")
        with mock.patch.object(ext, "POLL_INTERVAL", 0):
            assert handler(["install", "cap-demo"]) == ExitCode.OPERATION_FAILED
        captured = capsys.readouterr()
        # L'erreur réelle du Core est affichée, jamais réécrite.
        assert "pull failed: no space left" in captured.out
        assert "failed" in captured.err

    def test_operation_level_timeout_status_is_exit_7(self, ext, handler, core) -> None:
        core.payloads = [{"operation_id": "opx_1"}]
        core.payload = _op(status="TIMEOUT", error="Core deadline dépassé")
        with mock.patch.object(ext, "POLL_INTERVAL", 0):
            assert handler(["install", "cap-demo"]) == ExitCode.TIMEOUT

    def test_wait_timeout_is_exit_7_with_recovery_hint(self, ext, handler, core) -> None:
        core.payloads = [{"operation_id": "opx_1"}]
        core.payload = _op(status="RUNNING", progress=10, done=False)
        with mock.patch.object(ext, "POLL_INTERVAL", 0):
            with pytest.raises(CLIError) as excinfo:
                handler(["install", "cap-demo", "--wait-timeout", "0.05"])
        assert excinfo.value.exit_code == ExitCode.TIMEOUT
        message = f"{excinfo.value} {getattr(excinfo.value, 'hint', '')}"
        assert "opx_1" in message

    def test_interrupt_returns_130_with_recovery_hint(self, handler, core, capsys) -> None:
        # Ctrl+C pendant l'attente : le terminal peut se fermer, l'opération
        # Core, elle, continue côté serveur.
        core.payloads = [{"operation_id": "opx_1"}, KeyboardInterrupt()]
        assert handler(["install", "cap-demo"]) == ExitCode.INTERRUPTED
        err = capsys.readouterr().err
        assert "keeps running on the Core" in err
        assert "operation opx_1" in err


# ── enable / disable / update ─────────────────────────────────────────────────


class TestToggleAndUpdate:
    @pytest.mark.parametrize("verb", ["enable", "disable", "update"])
    def test_lifecycle_verbs_hit_their_route(self, ext, handler, core, verb) -> None:
        core.payloads = [{"operation_id": "opx_1"}]
        core.payload = _op(operation=verb)
        with mock.patch.object(ext, "POLL_INTERVAL", 0):
            assert handler([verb, "cap-demo"]) == ExitCode.SUCCESS
        assert core.calls[0][:2] == ("POST", f"/v1/extensions/cap-demo/{verb}")
        assert core.calls[1][:2] == ("GET", "/v1/extensions/operations/opx_1")


# ── uninstall: destructive guard (contract T8) ────────────────────────────────


class TestUninstallGuard:
    def test_uninstall_without_confirmation_is_usage_error(self, handler, core) -> None:
        # Pas de TTY, pas de --yes : exit 2 et AUCUN appel réseau (T8).
        with mock.patch("sys.stdin") as fake_stdin:
            fake_stdin.isatty.return_value = False
            with pytest.raises(CLIError) as excinfo:
                handler(["uninstall", "cap-demo"])
        assert excinfo.value.exit_code == ExitCode.USAGE
        assert core.calls == []

    def test_uninstall_with_assume_yes_proceeds(self, ext, handler, core) -> None:
        set_context(CLIContext(output="human", timeout=5.0, assume_yes=True))
        core.payloads = [{"operation_id": "opx_1"}]
        core.payload = _op(operation="uninstall")
        with mock.patch.object(ext, "POLL_INTERVAL", 0):
            assert handler(["uninstall", "cap-demo"]) == ExitCode.SUCCESS
        assert core.calls[0][:2] == ("POST", "/v1/extensions/cap-demo/uninstall")

    def test_uninstall_with_yes_flag_in_args_proceeds(self, ext, handler, core) -> None:
        core.payloads = [{"operation_id": "opx_1"}]
        core.payload = _op(operation="uninstall")
        with mock.patch.object(ext, "POLL_INTERVAL", 0):
            assert handler(["uninstall", "cap-demo", "--yes"]) == ExitCode.SUCCESS
        assert core.calls[0][:2] == ("POST", "/v1/extensions/cap-demo/uninstall")

    def test_uninstall_interactive_decline_is_usage_error(self, handler, core) -> None:
        # TTY présent, l'utilisateur refuse → rien d'exécuté, exit 2.
        with (
            mock.patch("sys.stdin") as fake_stdin,
            mock.patch("builtins.input", return_value="n"),
        ):
            fake_stdin.isatty.return_value = True
            with pytest.raises(CLIError) as excinfo:
                handler(["uninstall", "cap-demo"])
        assert excinfo.value.exit_code == ExitCode.USAGE
        assert core.calls == []

    def test_uninstall_interactive_accept_proceeds(self, ext, handler, core) -> None:
        core.payloads = [{"operation_id": "opx_1"}]
        core.payload = _op(operation="uninstall")
        with (
            mock.patch("sys.stdin") as fake_stdin,
            mock.patch("builtins.input", return_value="y"),
        ):
            fake_stdin.isatty.return_value = True
            with mock.patch.object(ext, "POLL_INTERVAL", 0):
                assert handler(["uninstall", "cap-demo"]) == ExitCode.SUCCESS
        assert core.calls[0][:2] == ("POST", "/v1/extensions/cap-demo/uninstall")


# ── persistence / restart: the Core keeps the state, the CLI has none ─────────


class TestPersistenceAndRestart:
    def test_operations_lists_in_flight_and_settled(self, handler, core, capsys) -> None:
        core.payload = {
            "operations": [
                _op(),
                _op(operation_id="opx_2", status="RUNNING", progress=30, done=False),
            ]
        }
        assert handler(["operations"]) == ExitCode.SUCCESS
        assert core.last[:2] == ("GET", "/v1/extensions/operations")
        out = capsys.readouterr().out
        assert "opx_1" in out
        assert "opx_2" in out
        assert "RUNNING" in out

    def test_new_session_recovers_operation_state(self, handler, core) -> None:
        # Nouveau contexte = nouvelle session : aucune mémoire locale, l'état
        # vient uniquement du Core.
        set_context(CLIContext(output="json", color=False, timeout=5.0))
        core.payload = _op(status="RUNNING", progress=55, done=False)
        assert handler(["operation", "opx_1"]) == ExitCode.SUCCESS
        assert core.last[:2] == ("GET", "/v1/extensions/operations/opx_1")

    def test_restart_interrupted_install_is_still_retrievable(self, ext, handler, core) -> None:
        # 1) terminal fermé pendant l'installation → exit 130.
        core.payloads = [{"operation_id": "opx_1"}, KeyboardInterrupt()]
        assert handler(["install", "cap-demo"]) == ExitCode.INTERRUPTED
        # 2) nouvelle session : l'opération tourne toujours côté Core.
        core.payload = _op(status="RUNNING", progress=80, done=False)
        assert handler(["operation", "opx_1"]) == ExitCode.SUCCESS
        # 3) l'aboutissement est lui aussi recouvrable.
        core.payload = _op()
        assert handler(["operation", "opx_1"]) == ExitCode.SUCCESS

    def test_cancel_posts_to_operation_cancel(self, handler, core) -> None:
        core.payload = _op(status="CANCELLED")
        assert handler(["cancel", "opx_1"]) == ExitCode.SUCCESS
        assert core.last[:2] == ("POST", "/v1/extensions/operations/opx_1/cancel")


# ── permissions: the Core enforces, the CLI never bypasses (§7) ───────────────


class TestPermissionsAndExitCodes:
    @pytest.mark.parametrize(
        ("status", "expected"),
        [
            (401, ExitCode.AUTH),
            (403, ExitCode.FORBIDDEN),
            (404, ExitCode.NOT_FOUND),
            (409, ExitCode.CONFLICT),
        ],
    )
    def test_http_status_is_frozen_exit_code(self, handler, core, status, expected) -> None:
        from interfaces.cli.core.client import APIError

        # Le Core refuse (RBAC / état) → le CLI traduit le STATUT, jamais le
        # contrôle lui-même : aucune décision d'autorisation locale.
        core.payload = APIError(status, "core refused")
        with pytest.raises(CLIError) as excinfo:
            handler(["install", "cap-demo"])
        assert excinfo.value.exit_code == expected

    def test_every_route_stays_under_v1_extensions(self, handler, core) -> None:
        # Un SEUL périmètre : pas de gestionnaire CLI par kind, pas d'endpoint
        # inventé (capability/plugin/cookbook passent tous par /v1/extensions).
        core.payload = {"extensions": [], "operations": []}
        for argv in (["list"], ["operations"], ["info", "x"], ["plan", "x"], ["logs", "x"]):
            handler(argv)
        assert core.calls
        for _, path, _ in core.calls:
            assert path.startswith("/v1/extensions")


# ── JSON output (§4.2 / T6) ───────────────────────────────────────────────────


class TestJsonOutput:
    def test_list_json_is_payload_untouched(self, handler, core, capsys) -> None:
        set_context(CLIContext(output="json", color=False))
        payload = {"extensions": [_item(extra_core_field={"keep": True})]}
        core.payload = payload
        handler(["list"])
        assert json.loads(capsys.readouterr().out) == payload

    def test_install_wait_json_is_single_document_on_stdout(
        self, ext, handler, core, capsys
    ) -> None:
        set_context(CLIContext(output="json", color=False))
        core.payloads = [
            {"operation_id": "opx_1"},
            _op(status="RUNNING", progress=10, done=False),
        ]
        core.payload = _op()
        with mock.patch.object(ext, "POLL_INTERVAL", 0):
            assert handler(["install", "cap-demo"]) == ExitCode.SUCCESS
        captured = capsys.readouterr()
        assert json.loads(captured.out) == _op()
        assert "\033[" not in captured.out
        # La progression ne peut vivre que sur stderr.
        assert "RUNNING" in captured.err

    def test_uninstall_json_has_no_colour_or_prompt(self, handler, core, capsys) -> None:
        set_context(CLIContext(output="json", color=False, assume_yes=True))
        core.payloads = [{"operation_id": "opx_1"}]
        core.payload = _op(operation="uninstall")
        assert handler(["uninstall", "cap-demo"]) == ExitCode.SUCCESS
        out = capsys.readouterr().out
        assert "\033[" not in out
        assert json.loads(out)["operation_id"] == "opx_1"


# ── usage errors before any network call (T5) ─────────────────────────────────


class TestUsageBeforeNetwork:
    def test_unknown_verb_is_usage_error(self, handler, core) -> None:
        with pytest.raises(CLIError) as excinfo:
            handler(["definitely-not-a-verb"])
        assert excinfo.value.exit_code == ExitCode.USAGE
        assert core.calls == []

    def test_missing_option_value_is_usage_error(self, handler, core) -> None:
        with pytest.raises(CLIError) as excinfo:
            handler(["list", "--kind"])
        assert excinfo.value.exit_code == ExitCode.USAGE
        assert core.calls == []

    def test_invalid_state_filter_is_usage_error_before_network(self, handler, core) -> None:
        with pytest.raises(CLIError) as excinfo:
            handler(["list", "--state"])
        assert excinfo.value.exit_code == ExitCode.USAGE
        assert core.calls == []

    def test_invalid_wait_timeout_is_usage_error_before_network(self, handler, core) -> None:
        with pytest.raises(CLIError) as excinfo:
            handler(["install", "cap-demo", "--wait-timeout", "abc"])
        assert excinfo.value.exit_code == ExitCode.USAGE
        assert core.calls == []
