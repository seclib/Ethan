"""Tests for cli/commands/chat.py — ethan chat.

The chat command is a pure pass-through to the Core ChatPipeline
(``POST /v1/chat/completions`` + SSE stream + ``GET /v1/chat/history``):
these tests mock the single HTTP boundary and assert that

- the answer alone reaches stdout (decorations live on stderr — §4);
- `-o json` emits exactly one Core document untouched (§4.2);
- model/provider/agent/chat_id are INTENTS forwarded to the Core;
- streaming, errors, interruption and deadlines map to frozen exit codes.

No socket is ever opened.
"""

from __future__ import annotations

import json
from unittest import mock

import pytest
from interfaces.cli.core.client import APIError
from interfaces.cli.core.context import CLIContext, set_context
from interfaces.cli.core.errors import CLIError, connection_error, timeout_error
from interfaces.cli.core.exit_codes import ExitCode


@pytest.fixture(autouse=True)
def _clean_context():
    set_context(CLIContext(output="human", timeout=5.0))
    yield
    set_context(CLIContext(output="human", timeout=5.0))


@pytest.fixture(autouse=True)
def _stable_deadline(monkeypatch):
    """Deadline resolution must not depend on the host profile/env."""
    monkeypatch.delenv("ETHAN_TIMEOUT", raising=False)
    with mock.patch("cli.core.config.get_profile", return_value={}):
        yield


_ANSWER = {
    "id": "msg-1",
    "chat_id": "c42",
    "message": "hi there",
    "role": "assistant",
    "metadata": {"provider": "ollama", "model": "llama3"},
}


class FakeSSE:
    """Replaces `client.stream_sse`: records calls, replays scripted events.

    An Exception element in `events` is raised mid-iteration (interrupt,
    transport failure…).
    """

    def __init__(self, events=()):
        self.events = list(events)
        self.calls: list[tuple[str, dict, dict]] = []

    def __call__(self, path, payload, **kwargs):
        self.calls.append((path, payload, kwargs))
        events = list(self.events)

        def _gen():
            for event in events:
                if isinstance(event, BaseException):
                    raise event
                yield event

        return _gen()


def _chat():
    from cli.commands.chat import cmd_chat

    return cmd_chat


# ── One-shot: `ethan chat "question"` ──────────────────────────────────────


class TestOneShot:
    def test_answer_alone_reaches_stdout(self, core, capsys) -> None:
        core.payload = dict(_ANSWER)
        assert _chat()(["hello"]) == ExitCode.SUCCESS
        assert core.last[:2] == ("POST", "/v1/chat/completions")
        assert core.last[2] == {"message": "hello"}
        captured = capsys.readouterr()
        assert captured.out == "hi there\n"
        # metadata/footer is stderr-only: stdout stays pipeable (§4)
        assert "c42" not in captured.out
        assert "c42" in captured.err

    def test_json_mode_emits_core_document_untouched(self, core, capsys) -> None:
        set_context(CLIContext(output="json"))
        core.payload = dict(_ANSWER)
        assert _chat()(["hello"]) == ExitCode.SUCCESS
        assert json.loads(capsys.readouterr().out) == _ANSWER

    def test_json_mode_without_message_is_usage_error(self, core) -> None:
        set_context(CLIContext(output="json"))
        with pytest.raises(CLIError) as excinfo:
            _chat()([])
        assert excinfo.value.exit_code == ExitCode.USAGE
        assert core.calls == []

    def test_routing_options_are_forwarded_not_decided(self, core, capsys) -> None:
        core.payload = dict(_ANSWER)
        _chat()(
            [
                "--model",
                "llama3",
                "--provider",
                "ollama",
                "--agent",
                "a1",
                "--session",
                "c9",
                "hi",
            ]
        )
        assert core.last[2] == {
            "message": "hi",
            "chat_id": "c9",
            "model": "llama3",
            "provider_id": "ollama",
            "agent_id": "a1",
        }

    def test_resume_reads_the_latest_chat_from_core(self, core, capsys) -> None:
        core.payload = [{"chat_id": "c-previous", "role": "assistant"}]
        _chat()(["--resume", "again"])
        assert core.calls[0][1] == "/v1/chat/history?limit=1"
        assert core.calls[1][:2] == ("POST", "/v1/chat/completions")
        assert core.calls[1][2]["chat_id"] == "c-previous"

    def test_unknown_option_is_usage_error(self, core) -> None:
        with pytest.raises(CLIError) as excinfo:
            _chat()(["--temperature", "0.5", "hi"])
        assert excinfo.value.exit_code == ExitCode.USAGE
        assert core.calls == []

    def test_option_without_value_is_usage_error(self, core) -> None:
        with pytest.raises(CLIError) as excinfo:
            _chat()(["--model"])
        assert excinfo.value.exit_code == ExitCode.USAGE

    def test_api_unavailable_is_exit_5(self, core) -> None:
        core.payload = connection_error("connection refused")
        with pytest.raises(CLIError) as excinfo:
            _chat()(["hello"])
        assert excinfo.value.exit_code == ExitCode.UNAVAILABLE

    def test_unknown_model_is_exit_6(self, core) -> None:
        core.payload = APIError(404, "model not found")
        with pytest.raises(CLIError) as excinfo:
            _chat()(["--model", "ghost-model", "hi"])
        assert excinfo.value.exit_code == ExitCode.NOT_FOUND

    def test_provider_unavailable_is_exit_5(self, core) -> None:
        core.payload = APIError(502, "Provider unavailable: ollama down")
        with pytest.raises(CLIError) as excinfo:
            _chat()(["hi"])
        assert excinfo.value.exit_code == ExitCode.UNAVAILABLE

    def test_timeout_is_exit_7(self, core) -> None:
        core.payload = timeout_error(120.0)
        with pytest.raises(CLIError) as excinfo:
            _chat()(["hi"])
        assert excinfo.value.exit_code == ExitCode.TIMEOUT

    def test_internal_llm_error_is_exit_1(self, core) -> None:
        core.payload = APIError(500, "boom")
        with pytest.raises(CLIError) as excinfo:
            _chat()(["hi"])
        assert excinfo.value.exit_code == ExitCode.OPERATION_FAILED

    def test_deadline_defaults_to_llm_budget(self, core) -> None:
        core.payload = dict(_ANSWER)
        _chat()(["hi"])
        assert core.last_kwargs["timeout"] == pytest.approx(120.0)

    def test_explicit_timeout_wins_over_llm_budget(self, core) -> None:
        set_context(CLIContext(timeout=9.0, timeout_explicit=True))
        core.payload = dict(_ANSWER)
        _chat()(["hi"])
        assert core.last_kwargs["timeout"] == pytest.approx(9.0)


# ── Streaming (SSE) ────────────────────────────────────────────────────────


class TestStreaming:
    def test_stream_concatenates_content_events(self, capsys) -> None:
        sse = FakeSSE(
            [
                {"type": "content", "content": "Hel"},
                {"type": "content", "content": "lo"},
                {"type": "done", "chat_id": "c7", "message_id": "m2"},
            ]
        )
        with mock.patch("cli.core.client.stream_sse", sse):
            assert _chat()(["--stream", "hi"]) == ExitCode.SUCCESS
        assert sse.calls[0][0] == "/v1/chat/completions/stream"
        assert sse.calls[0][1] == {"message": "hi"}
        assert capsys.readouterr().out == "Hello\n"

    def test_stream_error_is_exit_1_with_clean_stdout(self, capsys) -> None:
        """Pipe-safety: a mid-stream failure never leaves half an answer."""
        sse = FakeSSE(
            [
                {"type": "content", "content": "partial…"},
                {"type": "error", "error": "provider exploded"},
            ]
        )
        with mock.patch("cli.core.client.stream_sse", sse):
            with pytest.raises(CLIError) as excinfo:
                _chat()(["--stream", "hi"])
        assert excinfo.value.exit_code == ExitCode.OPERATION_FAILED
        assert capsys.readouterr().out == ""

    def test_content_replace_is_authoritative(self, capsys) -> None:
        sse = FakeSSE(
            [
                {"type": "content", "content": "raw draft"},
                {"type": "content_replace", "content": "clean final"},
                {"type": "done", "chat_id": "c7"},
            ]
        )
        with mock.patch("cli.core.client.stream_sse", sse):
            _chat()(["--stream", "hi"])
        assert capsys.readouterr().out == "clean final\n"

    def test_tool_events_go_to_stderr_only(self, capsys) -> None:
        sse = FakeSSE(
            [
                {"type": "tool_call", "tool": "web_search", "params": {}},
                {"type": "tool_result", "tool": "web_search", "status": "ok"},
                {"type": "content", "content": "answer"},
                {"type": "done", "chat_id": "c7"},
            ]
        )
        with mock.patch("cli.core.client.stream_sse", sse):
            _chat()(["--stream", "hi"])
        captured = capsys.readouterr()
        assert captured.out == "answer\n"
        assert "web_search" in captured.err

    def test_interruption_propagates_for_exit_130(self) -> None:
        """Ctrl+C mid-generation must reach main() → exit 130 (§5)."""
        sse = FakeSSE(
            [
                {"type": "content", "content": "half"},
                KeyboardInterrupt(),
            ]
        )
        with mock.patch("cli.core.client.stream_sse", sse):
            with pytest.raises(KeyboardInterrupt):
                _chat()(["--stream", "hi"])

    def test_stream_transport_failure_is_exit_5(self) -> None:
        def _boom(*args, **kwargs):
            raise connection_error("connection refused")

        with mock.patch("cli.core.client.stream_sse", _boom):
            with pytest.raises(CLIError) as excinfo:
                _chat()(["--stream", "hi"])
        assert excinfo.value.exit_code == ExitCode.UNAVAILABLE

    def test_json_mode_never_streams(self, core, capsys) -> None:
        set_context(CLIContext(output="json"))
        sse = FakeSSE([{"type": "content", "content": "nope"}])
        core.payload = dict(_ANSWER)
        with mock.patch("cli.core.client.stream_sse", sse):
            _chat()(["--stream", "hi"])
        assert sse.calls == []
        assert core.last[:2] == ("POST", "/v1/chat/completions")
        assert json.loads(capsys.readouterr().out) == _ANSWER

    def test_live_tty_stream_repaints_on_replace(self, capsys) -> None:
        sse = FakeSSE(
            [
                {"type": "content", "content": "draft"},
                {"type": "content_replace", "content": "final"},
                {"type": "done", "chat_id": "c7"},
            ]
        )
        with mock.patch("cli.core.client.stream_sse", sse):
            with mock.patch("sys.stdout.isatty", return_value=True):
                _chat()(["--stream", "hi"])
        out = capsys.readouterr().out
        assert "\x1b[2K" in out  # repaint happened
        assert out.endswith("final\n")

    def test_stream_carries_the_llm_deadline(self) -> None:
        sse = FakeSSE([{"type": "done", "chat_id": "c7"}])
        with mock.patch("cli.core.client.stream_sse", sse):
            _chat()(["--stream", "hi"])
        assert sse.calls[0][2]["timeout"] == pytest.approx(120.0)


# ── Interactive (stdin) ────────────────────────────────────────────────────


class TestInteractive:
    def test_eof_exits_zero_without_calling_core(self, core, capsys) -> None:
        with mock.patch("sys.stdin.readline", return_value=""):
            assert _chat()([]) == ExitCode.SUCCESS
        assert core.calls == []

    def test_each_line_is_one_core_exchange(self, core, capsys) -> None:
        core.payload = dict(_ANSWER)
        with mock.patch("sys.stdin.readline", side_effect=["hello\n", ""]):
            assert _chat()([]) == ExitCode.SUCCESS
        assert core.last[:2] == ("POST", "/v1/chat/completions")
        assert core.last[2] == {"message": "hello"}
        assert "hi there" in capsys.readouterr().out

    def test_conversation_keeps_the_core_chat_id(self, core, capsys) -> None:
        """History is the Core ChatStore — the CLI keeps no local state."""
        core.payload = dict(_ANSWER)
        with mock.patch("sys.stdin.readline", side_effect=["one\n", "two\n", ""]):
            _chat()([])
        assert core.calls[0][2].get("chat_id") is None
        assert core.calls[1][2]["chat_id"] == "c42"

    def test_exit_command_stops_without_a_call(self, core) -> None:
        with mock.patch("sys.stdin.readline", side_effect=["/exit\n"]):
            assert _chat()([]) == ExitCode.SUCCESS
        assert core.calls == []

    def test_unknown_slash_is_reported_on_stderr(self, core, capsys) -> None:
        with mock.patch("sys.stdin.readline", side_effect=["/bogus\n", ""]):
            assert _chat()([]) == ExitCode.SUCCESS
        captured = capsys.readouterr()
        assert "unknown command" in captured.err
        assert captured.out == ""

    def test_reset_starts_a_fresh_conversation(self, core) -> None:
        core.payload = dict(_ANSWER)
        lines = ["hi\n", "/reset\n", "again\n", ""]
        with mock.patch("sys.stdin.readline", side_effect=lines):
            _chat()([])
        assert len(core.calls) == 2
        assert core.calls[1][2].get("chat_id") is None

    def test_api_failure_is_reported_and_session_survives(self, core, capsys) -> None:
        core.payload = connection_error("connection refused")
        with mock.patch("sys.stdin.readline", side_effect=["hello\n", "/exit\n"]):
            assert _chat()([]) == ExitCode.SUCCESS
        captured = capsys.readouterr()
        assert captured.out == ""  # nothing but errors: stdout stays clean
        assert captured.err != ""

    def test_ctrl_c_at_prompt_exits_zero(self) -> None:
        with mock.patch("sys.stdin.readline", side_effect=KeyboardInterrupt()):
            assert _chat()([]) == ExitCode.SUCCESS

    def test_tty_session_writes_banner_to_stderr(self, capsys) -> None:
        with mock.patch("sys.stdin.isatty", return_value=True):
            with mock.patch("sys.stdin.readline", return_value=""):
                assert _chat()([]) == ExitCode.SUCCESS
        captured = capsys.readouterr()
        assert "ETHAN chat" in captured.err
        assert captured.out == ""
