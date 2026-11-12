"""Tests for the Core-backed CLI families built on top of the socle.

Covers, for `model`, `provider`, `agent`, `skill`, `knowledge`, `extension`,
`mcp`, `mission` and `document`:

- the exact Core route each verb calls (no invented endpoint);
- `-o json` passing the Core payload through untouched (§4.2);
- usage errors mapping to exit 2 and HTTP failures to frozen codes (§5);
- secrets never reaching stdout (§6.4).

The HTTP boundary is always mocked: these tests never open a socket.
"""

from __future__ import annotations

import importlib
import json

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


def _handler(command: str):
    """Return the handler of a command family."""
    module = importlib.import_module(f"interfaces.cli.commands.{command}")
    return getattr(module, f"cmd_{command}")


# ── Routes: the CLI calls Core, it does not reimplement it ──────────────────


class TestRoutes:
    def test_model_list_calls_get_models(self, core) -> None:
        core.payload = []
        assert _handler("model")(["list"]) == ExitCode.SUCCESS
        assert core.last[:2] == ("GET", "/models")

    def test_model_pull_posts_model_id(self, core) -> None:
        core.payload = {"operation_id": "op-1"}
        _handler("model")(["pull", "llama3"])
        assert core.last[:2] == ("POST", "/models/pull")
        assert core.last[2] == {"model_id": "llama3"}

    def test_provider_list_calls_get_providers(self, core) -> None:
        core.payload = []
        _handler("provider")(["list"])
        assert core.last[:2] == ("GET", "/providers")

    def test_provider_catalog_calls_catalog_route(self, core) -> None:
        core.payload = {"types": []}
        _handler("provider")(["catalog"])
        assert core.last[1] == "/providers/catalog"

    def test_agent_show_calls_agent_route(self, core) -> None:
        core.payload = {"id": "a1"}
        _handler("agent")(["show", "a1"])
        assert core.last[:2] == ("GET", "/v1/agents/a1")

    def test_agents_is_an_alias_of_agent(self, core) -> None:
        from interfaces.cli.commands.agent import cmd_agent, cmd_agents

        core.payload = []
        cmd_agents(["list"])
        cmd_agent(["list"])
        assert core.calls[0][1] == core.calls[1][1] == "/v1/agents"

    def test_skill_list_calls_v1_skills(self, core) -> None:
        core.payload = []
        _handler("skill")(["list"])
        assert core.last[1] == "/v1/skills"

    def test_knowledge_list_calls_v1_knowledge(self, core) -> None:
        core.payload = []
        _handler("knowledge")(["list"])
        assert core.last[1] == "/v1/knowledge"

    def test_knowledge_documents_use_collection_route(self, core) -> None:
        core.payload = {"documents": []}
        _handler("knowledge")(["documents", "c1"])
        assert core.last[1] == "/v1/knowledge/collections/c1/documents"

    def test_extension_list_calls_v1_extensions(self, core) -> None:
        core.payload = {"extensions": []}


# ── JSON pass-through: the CLI renames nothing (§4.2) ───────────────────────


class TestJsonPassthrough:
    def test_json_mode_emits_core_payload_untouched(self, core, capsys) -> None:
        set_context(CLIContext(output="json"))
        payload = [{"id": "m1", "context_length": 8192, "extra_core_field": True}]
        core.payload = payload
        _handler("model")(["list"])
        assert json.loads(capsys.readouterr().out) == payload

    def test_json_mode_emits_one_document_only(self, core, capsys) -> None:
        set_context(CLIContext(output="json"))
        core.payload = [{"id": "p1"}]
        _handler("provider")(["list"])
        assert len(json.loads(capsys.readouterr().out)) == 1

    def test_quiet_prints_nothing_in_human_mode(self, core, capsys) -> None:
        set_context(CLIContext(output="human", quiet=True))
        core.payload = []
        assert _handler("skill")(["list"]) == ExitCode.SUCCESS
        assert capsys.readouterr().out == ""

    def test_no_colour_in_json_output(self, core, capsys) -> None:
        set_context(CLIContext(output="json", color=False))
        core.payload = []
        _handler("agent")(["list"])
        assert "\033[" not in capsys.readouterr().out


# ── Exit codes: frozen, never ad hoc (§5) ───────────────────────────────────


class TestExitCodes:
    @pytest.mark.parametrize(
        "command",
        ["model", "provider", "agent", "skill", "knowledge", "extension", "mcp"],
    )
    def test_unknown_verb_is_usage_error(self, command, core) -> None:
        with pytest.raises(CLIError) as excinfo:
            _handler(command)(["definitely-not-a-verb"])
        assert excinfo.value.exit_code == ExitCode.USAGE

    def test_missing_identifier_is_usage_error(self, core) -> None:
        with pytest.raises(CLIError) as excinfo:
            _handler("agent")(["show"])
        assert excinfo.value.exit_code == ExitCode.USAGE

    @pytest.mark.parametrize(
        ("status", "expected"),
        [
            (401, ExitCode.AUTH),
            (403, ExitCode.FORBIDDEN),
            (404, ExitCode.NOT_FOUND),
            (409, ExitCode.CONFLICT),
        ],
    )
    def test_http_status_maps_to_frozen_exit_code(self, status, expected) -> None:
        from interfaces.cli.core.client import APIError

        assert APIError(status, "nope").exit_code == expected

    def test_unmapped_status_is_operation_failure(self) -> None:
        from interfaces.cli.core.client import APIError

        assert APIError(500, "boom").exit_code == ExitCode.OPERATION_FAILED

    def test_unreachable_core_is_exit_5(self) -> None:
        from interfaces.cli.core.errors import connection_error

        assert connection_error("refused").exit_code == ExitCode.UNAVAILABLE

    def test_timeout_is_exit_7(self) -> None:
        from interfaces.cli.core.errors import timeout_error

        assert timeout_error(5).exit_code == ExitCode.TIMEOUT


# ── Secrets: never printed (§6.4) ───────────────────────────────────────────


class TestNoSecretLeak:
    def test_provider_list_never_prints_api_key(self, core, capsys) -> None:
        core.payload = [
            {
                "id": "openai",
                "name": "OpenAI",
                "type": "openai",
                "enabled": True,
                "status": "connected",
                "has_api_key": True,
                "api_key": "sk-must-never-appear",
            }
        ]
        _handler("provider")(["list"])
        assert "sk-must-never-appear" not in capsys.readouterr().out


# ── Help metadata: every command documents itself (§8.18) ──────────────────


class TestMetadata:
    @pytest.mark.parametrize(
        "name",
        [
            "model",
            "provider",
            "agent",
            "agents",
            "skill",
            "knowledge",
            "extension",
            "mcp",
            "mission",
            "missions",
            "document",
            "documents",
        ],
    )
    def test_command_has_help_metadata(self, name, core) -> None:
        from interfaces.cli.registry import COMMAND_HANDLERS, discover_commands

        # `core` keeps discovery offline: loading a command module must never
        # reach the network (a CLI that calls out at import time is a bug).
        discover_commands()
        meta = getattr(COMMAND_HANDLERS[name], "__meta__", None)
        assert meta, f"{name} has no __meta__"
        assert meta["description"]
        assert meta["usage"]
        assert meta["group"] in ("core", "infra", "system")
        _handler("extension")(["list"])
        assert core.last[1] == "/v1/extensions"

    def test_mcp_list_calls_tool_servers(self, core) -> None:
        core.payload = {"servers": []}
        _handler("mcp")(["list"])
        assert core.last[1] == "/v1/tools/servers"

    def test_mcp_enable_puts_status(self, core) -> None:
        core.payload = {}
        _handler("mcp")(["enable", "srv-1"])
        assert core.last[:2] == ("PUT", "/v1/tools/servers/srv-1/status")
        assert core.last[2] == {"enabled": True}

    def test_mission_verify_uses_step_route(self, core) -> None:
        core.payload = {"result": "verified"}
        assert _handler("mission")(["verify", "m1", "s1"]) == ExitCode.SUCCESS
        assert core.last[1] == "/v1/missions/m1/steps/s1/verify"

    def test_mission_rejected_step_is_operation_failure(self, core) -> None:
        core.payload = {"result": "rejected"}
        assert _handler("mission")(["approve", "m1", "s1"]) == ExitCode.OPERATION_FAILED

    def test_document_retrieve_posts_query(self, core) -> None:
        core.payload = {"matches": []}
        _handler("document")(["retrieve", "how", "to", "cook"])
        assert core.last[:2] == ("POST", "/v1/rag/retrieve")
        assert core.last[2] == {"query": "how to cook"}


# ── Global option parsing (§3.1) ───────────────────────────────────────────


class TestGlobalOptions:
    @pytest.mark.parametrize(
        "argv",
        [
            ["--timeout", "abc", "status"],
            ["--timeout", "0", "status"],
            ["--output", "xml", "status"],
            ["--profile"],
            ["-o"],
        ],
    )
    def test_malformed_option_is_usage_error(self, argv) -> None:
        """A bad global option is exit 2, never a traceback (§5)."""
        from interfaces.cli.core.context import parse_global_options

        with pytest.raises(CLIError) as excinfo:
            parse_global_options(argv)
        assert excinfo.value.exit_code == ExitCode.USAGE

    @pytest.mark.parametrize(
        ("argv", "command", "expected_args"),
        [
            (["-o", "json", "status", "--watch"], "status", ["--watch"]),
            (["status", "-o", "json"], "status", []),
            (["--output=json", "-vv", "model", "list"], "model", ["list"]),
            (["-vq", "status"], "status", []),
        ],
    )
    def test_options_accepted_before_or_after_the_family(
        self, argv, command, expected_args
    ) -> None:
        from interfaces.cli.core.context import parse_global_options

        ctx = parse_global_options(argv)
        assert ctx.command == command
        assert ctx.args == expected_args

    def test_dry_run_is_recorded_not_silently_ignored(self) -> None:
        from interfaces.cli.core.context import parse_global_options

        assert parse_global_options(["--dry-run", "status"]).dry_run is True

    def test_clustered_verbose_flags(self) -> None:
        from interfaces.cli.core.context import parse_global_options

        assert parse_global_options(["-vv", "status"]).verbose == 2

    def test_version_flag_sets_is_version(self) -> None:
        from interfaces.cli.core.context import parse_global_options

        assert parse_global_options(["-V"]).is_version is True

    def test_token_flag_warns_on_stderr(self, capsys) -> None:
        from interfaces.cli.core.context import parse_global_options

        parse_global_options(["--token", "jwt-abc", "status"])
        assert "process list" in capsys.readouterr().err


# ── doctor: the verdict comes from the Core, mapped not invented (§8.15) ────


class TestDoctor:
    def test_run_calls_diagnostics_route(self, core) -> None:
        core.payload = {"summary": {"counts": {}}, "components": {}}
        assert _handler("doctor")(["run"]) == ExitCode.SUCCESS
        assert core.last[:2] == ("GET", "/diagnostics")

    def test_default_verb_is_run(self, core) -> None:
        core.payload = {"summary": {"counts": {}}, "components": {}}
        _handler("doctor")([])
        assert core.last[1] == "/diagnostics"

    def test_components_option_is_forwarded_as_params(self, core) -> None:
        core.payload = {"summary": {"counts": {}}, "components": {}}
        _handler("doctor")(["run", "--components", "postgres,nats"])
        assert core.last[1] == "/diagnostics"
        assert core.last_kwargs.get("params") == {"components": "postgres,nats"}

    def test_error_count_maps_to_exit_1(self, core) -> None:
        core.payload = {"summary": {"counts": {"error": 2}}, "components": {}}
        assert _handler("doctor")([]) == ExitCode.OPERATION_FAILED

    def test_healthy_report_maps_to_exit_0(self, core) -> None:
        core.payload = {"summary": {"counts": {"ok": 5}}, "components": {}}
        assert _handler("doctor")([]) == ExitCode.SUCCESS

    def test_json_returns_core_report_untouched(self, core, capsys) -> None:
        set_context(CLIContext(output="json"))
        payload = {"summary": {"counts": {"ok": 1}}, "components": {"kernel": {}}}
        core.payload = payload
        _handler("doctor")([])
        assert json.loads(capsys.readouterr().out) == payload

    def test_unreachable_core_in_json_is_error_document(self, core, capsys) -> None:
        from interfaces.cli.core.errors import connection_error

        set_context(CLIContext(output="json"))
        core.payload = connection_error("refused")
        assert _handler("doctor")([]) == ExitCode.OPERATION_FAILED
        document = json.loads(capsys.readouterr().out)
        assert document["error"]["code"] == "unavailable"

    def test_unknown_verb_is_usage_error(self, core) -> None:
        with pytest.raises(CLIError) as excinfo:
            _handler("doctor")(["not-a-verb"])
        assert excinfo.value.exit_code == ExitCode.USAGE

    @pytest.mark.parametrize(
        ("status", "label"),
        [
            ("ok", "PASS"),
            ("warning", "WARN"),
            ("unavailable", "WARN"),
            ("error", "FAIL"),
        ],
    )
    def test_core_status_maps_to_verdict(self, status, label) -> None:
        from interfaces.cli.commands.doctor import verdict_of

        assert verdict_of(status)[0] == label


# ── config: local keys are strict, Core domains belong to the Core (§8.12) ─


def _config(args: list[str]):
    from interfaces.cli.commands.cfg import cmd_config

    return cmd_config(args)


class TestConfig:
    def test_domains_calls_get_config(self, core) -> None:
        core.payload = {"domains": []}
        assert _config(["domains"]) == ExitCode.SUCCESS
        assert core.last[:2] == ("GET", "/config")

    def test_schema_calls_get_config_schema(self, core) -> None:
        core.payload = {"properties": {}}
        assert _config(["schema"]) == ExitCode.SUCCESS
        assert core.last[:2] == ("GET", "/config/schema")

    def test_core_get_reads_declared_domain(self, core) -> None:
        core.payload = {"provider": "ollama"}
        assert _config(["core-get", "provider"]) == ExitCode.SUCCESS
        assert core.last[:2] == ("GET", "/config/provider")

    def test_core_get_without_domain_is_usage_error(self, core) -> None:
        with pytest.raises(CLIError) as excinfo:
            _config(["core-get"])
        assert excinfo.value.exit_code == ExitCode.USAGE

    def test_core_set_puts_declared_domain(self, core) -> None:
        core.payload = {"properties": {"provider": {}}, "ok": True}
        _config(["core-set", "provider", "active=ollama", "url=http://x"])
        methods = [(m, p) for m, p, _ in core.calls]
        assert ("GET", "/config/schema") in methods  # domain checked, not invented
        assert core.last[:2] == ("PUT", "/config/provider")
        assert core.last[2] == {"active": "ollama", "url": "http://x"}

    def test_core_set_refuses_unknown_domain(self, core) -> None:
        core.payload = {"properties": {"provider": {}}}
        with pytest.raises(CLIError) as excinfo:
            _config(["core-set", "not-a-domain", "a=b"])
        assert excinfo.value.exit_code == ExitCode.USAGE
        assert all(m != "PUT" for m, _, _ in core.calls)

    def test_core_set_without_equals_is_usage_error(self, core) -> None:
        core.payload = {"properties": {"provider": {}}}
        with pytest.raises(CLIError) as excinfo:
            _config(["core-set", "provider", "malformed"])
        assert excinfo.value.exit_code == ExitCode.USAGE

    def test_get_refuses_secret_keys(self, capsys) -> None:
        with pytest.raises(CLIError) as excinfo:
            _config(["get", "auth_token"])
        assert excinfo.value.exit_code == ExitCode.USAGE
        assert capsys.readouterr().out == ""

    def test_set_refuses_unsupported_key(self) -> None:
        with pytest.raises(CLIError) as excinfo:
            _config(["set", "not.a.key", "x"])
        assert excinfo.value.exit_code == ExitCode.USAGE

    def test_set_then_get_supported_key(self, capsys) -> None:
        assert _config(["set", "api.timeout", "10"]) == ExitCode.SUCCESS
        capsys.readouterr()
        assert _config(["get", "api.timeout"]) == ExitCode.SUCCESS
        assert capsys.readouterr().out.strip() == "10"

    def test_get_missing_key_prints_not_set(self, capsys) -> None:
        _config(["get", "profile"])
        assert "(not set)" in capsys.readouterr().out

    def test_list_masks_secret_values(self, capsys) -> None:
        import sys as _sys
        from unittest import mock as _mock

        module = _sys.modules.get("interfaces.cli.commands.cfg") or _sys.modules.get(
            "cli.commands.cfg"
        )
        with _mock.patch.object(
            module, "load_local", return_value={"api_key": "sk-leak", "output": "human"}
        ):
            _config(["list"])
        out = capsys.readouterr().out
        assert "sk-leak" not in out
        assert "***" in out


# ── Model: the verbs the task and §8.9 require ─────────────────────────────


class TestModelVerbs:
    def test_info_is_the_documented_alias_of_show(self, core) -> None:
        core.payload = {"id": "llama3"}
        assert _handler("model")(["info", "llama3"]) == ExitCode.SUCCESS
        assert core.last[:2] == ("GET", "/models/llama3")

    def test_search_queries_the_catalogue(self, core) -> None:
        core.payload = [{"id": "llama3"}]
        assert _handler("model")(["search", "llama"]) == ExitCode.SUCCESS
        assert core.last[1] == "/models/search?q=llama"

    def test_search_without_query_is_usage_error(self, core) -> None:
        with pytest.raises(CLIError) as excinfo:
            _handler("model")(["search"])
        assert excinfo.value.exit_code == ExitCode.USAGE
        assert core.calls == []

    def test_unknown_model_is_exit_6(self, core) -> None:
        from interfaces.cli.core.client import APIError

        core.payload = APIError(404, "model not found")
        with pytest.raises(CLIError) as excinfo:
            _handler("model")(["info", "ghost-model"])
        assert excinfo.value.exit_code == ExitCode.NOT_FOUND


# ── Provider: real operations + secrets never in argv, never on stdout ─────


class TestProviderVerbs:
    def test_capabilities_route(self, core) -> None:
        core.payload = {"capabilities": []}
        _handler("provider")(["capabilities", "p1"])
        assert core.last[:2] == ("GET", "/providers/p1/capabilities")

    def test_default_is_a_documented_synonym_of_use(self, core) -> None:
        core.payload = {"id": "p1", "is_default": True}
        _handler("provider")(["default", "p1"])
        assert core.last[:2] == ("PUT", "/providers/p1/default")

    def test_failed_connection_test_is_operation_failure(self, core, capsys) -> None:
        core.payload = {"connected": False, "status": "down", "message": "refused"}
        assert _handler("provider")(["test", "p1"]) == ExitCode.OPERATION_FAILED
        assert core.last[:2] == ("POST", "/providers/p1/test")

    def test_successful_connection_test_is_success(self, core) -> None:
        core.payload = {"connected": True, "status": "ok", "message": "pong"}
        assert _handler("provider")(["test", "p1"]) == ExitCode.SUCCESS

    def test_secret_in_argv_is_refused_without_any_call(self, core) -> None:
        with pytest.raises(CLIError) as excinfo:
            _handler("provider")(["update", "p1", "api_key=sk-must-not-enter"])
        assert excinfo.value.exit_code == ExitCode.USAGE
        assert core.calls == []

    def test_api_key_via_stdin_reaches_core_but_never_stdout(self, core, capsys) -> None:
        from unittest import mock as _mock

        core.payload = {"id": "p1", "api_key": "sk-from-stdin"}
        with _mock.patch("sys.stdin.readline", return_value="sk-real-value\n"):
            code = _handler("provider")(["create", "openai", "OpenAI", "--api-key-stdin"])
        assert code == ExitCode.SUCCESS
        assert core.last[2]["api_key"] == "sk-real-value"  # sent to Core…
        out = capsys.readouterr().out
        assert "sk-real-value" not in out  # …but never displayed
        assert "sk-from-stdin" not in out

    def test_json_output_masks_secret_values(self, core, capsys) -> None:
        set_context(CLIContext(output="json"))
        core.payload = [{"id": "p1", "api_key": "sk-json-leak"}]
        _handler("provider")(["list"])
        out = capsys.readouterr().out
        assert "sk-json-leak" not in out
        assert "***" in out

    def test_has_api_key_boolean_survives_masking(self, core, capsys) -> None:
        set_context(CLIContext(output="json"))
        core.payload = [{"id": "p1", "has_api_key": True}]
        _handler("provider")(["list"])
        assert json.loads(capsys.readouterr().out)[0]["has_api_key"] is True


# ── Agent: info/run/resources, same execute mechanism as the WebUI ─────────


class TestAgentVerbs:
    def test_info_is_the_documented_alias_of_show(self, core) -> None:
        core.payload = {"id": "a1"}
        _handler("agent")(["info", "a1"])
        assert core.last[:2] == ("GET", "/v1/agents/a1")

    def test_run_posts_the_task_to_the_execute_route(self, core) -> None:
        core.payload = {"id": "exec-1", "status": "done"}
        assert _handler("agent")(["run", "a1", "--input", "audit the logs"]) == (ExitCode.SUCCESS)
        assert core.last[:2] == ("POST", "/v1/agents/a1/execute")
        assert core.last[2] == {"task": "audit the logs"}

    def test_execute_synonym_accepts_positional_input(self, core) -> None:
        core.payload = {"id": "exec-1"}
        _handler("agent")(["execute", "a1", "say", "hello"])
        assert core.last[:2] == ("POST", "/v1/agents/a1/execute")
        assert core.last[2] == {"task": "say hello"}

    def test_run_reads_input_file(self, core, tmp_path) -> None:
        payload_file = tmp_path / "task.md"
        payload_file.write_text("contents of the file", encoding="utf-8")
        core.payload = {"id": "exec-1"}
        _handler("agent")(["run", "a1", "--input", f"@{payload_file}"])
        assert core.last[2] == {"task": "contents of the file"}

    def test_run_with_missing_file_is_operation_failure(self, core) -> None:
        core.payload = {}
        with pytest.raises(CLIError) as excinfo:
            _handler("agent")(["run", "a1", "--input", "@/no/such/file.txt"])
        assert excinfo.value.exit_code == ExitCode.OPERATION_FAILED
        assert core.calls == []

    def test_run_without_input_is_usage_error(self, core) -> None:
        with pytest.raises(CLIError) as excinfo:
            _handler("agent")(["run", "a1"])
        assert excinfo.value.exit_code == ExitCode.USAGE
        assert core.calls == []

    def test_resources_route(self, core) -> None:
        core.payload = {"skills": [], "tools": []}
        _handler("agent")(["resources", "a1"])
        assert core.last[:2] == ("GET", "/v1/agents/a1/resources")

    def test_unknown_agent_is_exit_6(self, core) -> None:
        from interfaces.cli.core.client import APIError

        core.payload = APIError(404, "Agent ghost not found")
        with pytest.raises(CLIError) as excinfo:
            _handler("agent")(["info", "ghost"])
        assert excinfo.value.exit_code == ExitCode.NOT_FOUND
