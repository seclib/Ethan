"""Tests for cli/core/client.py — HTTP client."""

from __future__ import annotations

from unittest import mock

import pytest


class TestAlive:
    """alive() tests."""

    def test_alive_returns_true_on_200(self, mock_api_server) -> None:
        from cli.core.client import alive

        assert alive() is True

    def test_alive_returns_false_on_error(self, mock_api_server) -> None:
        from cli.core.client import alive

        mock_api_server["state_200"] = False
        assert alive() is False

    def test_alive_returns_false_on_exception(self, mock_api_server) -> None:
        from urllib.error import URLError

        from cli.core.client import alive

        mock_api_server["raise_on"] = ("state", URLError("Connection refused"))
        assert alive() is False


class TestSend:
    """send() tests."""

    def test_send_returns_response(self, mock_api_server) -> None:
        from cli.core.client import send

        text, latency = send("Hello")
        assert text == "Hello from Ethan"
        assert isinstance(latency, int)

    def test_send_with_session_id(self, mock_api_server) -> None:
        from cli.core.client import send

        text, latency = send("Hello", session_id="test-session-123")
        assert text == "Hello from Ethan"

    def test_send_handles_error_response(self, mock_api_server) -> None:
        from cli.core.client import send

        mock_api_server["message_response"] = {"error": "something went wrong"}
        text, latency = send("Hello")
        assert "something went wrong" in text

    def test_send_handles_missing_fields(self, mock_api_server) -> None:
        from cli.core.client import send

        mock_api_server["message_response"] = {}
        text, latency = send("Hello")
        assert text == "no response"

    def test_send_propagates_timeout(self) -> None:
        """send should let urlopen timeout propagate."""
        from urllib.error import URLError

        from cli.core.client import send

        def _timeout_side_effect(url, *_args, **_kwargs):
            raise URLError("timed out")

        with mock.patch("cli.core.client.urlopen", side_effect=_timeout_side_effect):
            with pytest.raises(Exception):
                send("Hello")


class TestGetState:
    """get_state() tests."""

    def test_get_state_returns_dict(self, mock_api_server) -> None:
        from cli.core.client import get_state

        state = get_state()
        assert isinstance(state, dict)
        assert state["mode"] == "running"

    def test_get_state_returns_none_on_error(self, mock_api_server) -> None:
        from cli.core.client import get_state

        mock_api_server["state_200"] = False
        assert get_state() is None

    def test_get_state_returns_none_on_exception(self, mock_api_server) -> None:
        from urllib.error import URLError

        from cli.core.client import get_state

        mock_api_server["raise_on"] = ("state", URLError("Connection refused"))
        assert get_state() is None


# ── get_timeout(): priority ``--timeout`` > env > profile > default ────────


class TestGetTimeout:
    """Priority of the deadline resolution (client.py docstring)."""

    @staticmethod
    def _config_module():
        import sys

        return sys.modules.get("interfaces.cli.core.config") or sys.modules.get("cli.core.config")

    @staticmethod
    def _fresh_context(**kwargs) -> None:
        from interfaces.cli.core.context import CLIContext, set_context

        set_context(CLIContext(**kwargs))

    def test_default_wins_when_nothing_is_set(self, monkeypatch) -> None:
        from cli.core.client import get_timeout

        self._fresh_context()
        monkeypatch.delenv("ETHAN_TIMEOUT", raising=False)
        with mock.patch.object(self._config_module(), "get_profile", return_value={}):
            assert get_timeout(default=42.0) == 42.0

    def test_profile_timeout_beats_default(self, monkeypatch) -> None:
        from cli.core.client import get_timeout

        self._fresh_context()
        monkeypatch.delenv("ETHAN_TIMEOUT", raising=False)
        with mock.patch.object(self._config_module(), "get_profile", return_value={"timeout": 3.5}):
            assert get_timeout(default=42.0) == 3.5

    def test_env_beats_profile(self, monkeypatch) -> None:
        from cli.core.client import get_timeout

        self._fresh_context()
        monkeypatch.setenv("ETHAN_TIMEOUT", "7")
        with mock.patch.object(self._config_module(), "get_profile", return_value={"timeout": 3.5}):
            assert get_timeout(default=42.0) == 7.0

    def test_explicit_timeout_beats_everything(self, monkeypatch) -> None:
        from cli.core.client import get_timeout

        self._fresh_context(timeout=9.0, timeout_explicit=True)
        monkeypatch.setenv("ETHAN_TIMEOUT", "7")
        with mock.patch.object(self._config_module(), "get_profile", return_value={"timeout": 3.5}):
            assert get_timeout(default=42.0) == 9.0

    def test_non_explicit_context_timeout_is_ignored(self, monkeypatch) -> None:
        """A default context timeout must not shadow env/profile/default."""
        from cli.core.client import get_timeout

        self._fresh_context(timeout=9.0, timeout_explicit=False)
        monkeypatch.delenv("ETHAN_TIMEOUT", raising=False)
        with mock.patch.object(self._config_module(), "get_profile", return_value={"timeout": 3.5}):
            assert get_timeout(default=42.0) == 3.5

    def test_invalid_env_falls_through_to_profile(self, monkeypatch) -> None:
        from cli.core.client import get_timeout

        self._fresh_context()
        monkeypatch.setenv("ETHAN_TIMEOUT", "not-a-number")
        with mock.patch.object(self._config_module(), "get_profile", return_value={"timeout": 3.5}):
            assert get_timeout(default=42.0) == 3.5

    def test_llm_default_of_120_s_is_returned(self, monkeypatch) -> None:
        """`chat` passes 120 s; nothing else set → the LLM budget stands."""
        from cli.core.client import get_timeout

        self._fresh_context()
        monkeypatch.delenv("ETHAN_TIMEOUT", raising=False)
        with mock.patch.object(self._config_module(), "get_profile", return_value={}):
            assert get_timeout(default=120.0) == 120.0


# ── stream_sse(): the single SSE transport boundary ────────────────────────


class _FakeStreamResponse:
    """Minimal context-manager response iterating raw SSE lines."""

    def __init__(self, lines: list[bytes]) -> None:
        self._lines = lines

    def __enter__(self):  # noqa: ANN201
        return self

    def __exit__(self, *exc) -> bool:
        return False

    def __iter__(self):  # noqa: ANN201
        return iter(self._lines)


class TestStreamSSE:
    """Parsing and §5 error mapping of `stream_sse`."""

    @staticmethod
    def _events(lines: list[bytes]) -> list[dict]:
        from cli.core.client import stream_sse

        with mock.patch("cli.core.client.urlopen", return_value=_FakeStreamResponse(lines)):
            return list(stream_sse("/v1/chat/completions/stream", {"message": "hi"}))

    def test_yields_only_data_events(self) -> None:
        lines = [
            b": keep-alive\n",
            b'data: {"type":"content","content":"a"}\n',
            b"\n",
            b"data: [DONE]\n",
        ]
        assert self._events(lines) == [{"type": "content", "content": "a"}]

    def test_malformed_frames_are_skipped_not_fatal(self) -> None:
        lines = [
            b"data: {oops\n",
            b"data: 123\n",
            b"event: ping\n",
            b'data: {"ok":1}\n',
        ]
        assert self._events(lines) == [{"ok": 1}]

    def test_bearer_token_is_sent(self, monkeypatch) -> None:
        from cli.core.client import stream_sse

        monkeypatch.setenv("ETHAN_TOKEN", "tok-123")
        captured: dict = {}

        def _capture(req, **kwargs):  # noqa: ANN001, ANN202
            captured["req"] = req
            return _FakeStreamResponse([b'data: {"ok":1}\n'])

        with mock.patch("cli.core.client.urlopen", side_effect=_capture):
            list(stream_sse("/x", {}))
        assert captured["req"].get_header("Authorization") == "Bearer tok-123"
        assert captured["req"].get_method() == "POST"

    def test_explicit_timeout_reaches_urlopen(self) -> None:
        from cli.core.client import stream_sse

        captured: dict = {}
        with mock.patch(
            "cli.core.client.urlopen",
            side_effect=lambda req, **kw: (
                captured.update(kw) or _FakeStreamResponse([b'data: {"ok":1}\n'])
            ),
        ):
            list(stream_sse("/x", {}, timeout=9.0))
        assert captured["timeout"] == pytest.approx(9.0)

    def test_profile_timeout_is_the_default_deadline(self, monkeypatch) -> None:
        import sys

        from interfaces.cli.core.context import CLIContext, set_context

        from cli.core.client import stream_sse

        set_context(CLIContext())
        monkeypatch.delenv("ETHAN_TIMEOUT", raising=False)
        config_mod = sys.modules.get("interfaces.cli.core.config") or sys.modules.get(
            "cli.core.config"
        )
        captured: dict = {}
        with mock.patch.object(config_mod, "get_profile", return_value={"timeout": 6.5}):
            with mock.patch(
                "cli.core.client.urlopen",
                side_effect=lambda req, **kw: (
                    captured.update(kw) or _FakeStreamResponse([b'data: {"ok":1}\n'])
                ),
            ):
                list(stream_sse("/x", {}))
        assert captured["timeout"] == pytest.approx(6.5)

    def test_http_503_maps_to_exit_5(self) -> None:
        import io
        from urllib.error import HTTPError

        from interfaces.cli.core.errors import CLIError
        from interfaces.cli.core.exit_codes import ExitCode

        from cli.core.client import stream_sse

        err = HTTPError("http://x", 503, "Service Unavailable", None, io.BytesIO(b'{"detail":"d"}'))
        with mock.patch("cli.core.client.urlopen", side_effect=err):
            with pytest.raises(CLIError) as excinfo:
                list(stream_sse("/x", {}))
        assert excinfo.value.exit_code == ExitCode.UNAVAILABLE

    def test_http_404_is_an_api_error(self) -> None:
        import io
        from urllib.error import HTTPError

        from cli.core.client import APIError, stream_sse

        err = HTTPError("http://x", 404, "Not Found", None, io.BytesIO(b"missing"))
        with mock.patch("cli.core.client.urlopen", side_effect=err):
            with pytest.raises(APIError) as excinfo:
                list(stream_sse("/x", {}))
        assert "404" in str(excinfo.value)

    def test_network_timeout_maps_to_exit_7(self) -> None:
        from urllib.error import URLError

        from interfaces.cli.core.errors import CLIError
        from interfaces.cli.core.exit_codes import ExitCode

        from cli.core.client import stream_sse

        with mock.patch("cli.core.client.urlopen", side_effect=URLError("timed out")):
            with pytest.raises(CLIError) as excinfo:
                list(stream_sse("/x", {}))
        assert excinfo.value.exit_code == ExitCode.TIMEOUT

    def test_connection_refused_maps_to_exit_5(self) -> None:
        from urllib.error import URLError

        from interfaces.cli.core.errors import CLIError
        from interfaces.cli.core.exit_codes import ExitCode

        from cli.core.client import stream_sse

        with mock.patch("cli.core.client.urlopen", side_effect=URLError(ConnectionRefusedError())):
            with pytest.raises(CLIError) as excinfo:
                list(stream_sse("/x", {}))
        assert excinfo.value.exit_code == ExitCode.UNAVAILABLE

    def test_keyboard_interrupt_is_never_swallowed(self) -> None:
        from cli.core.client import stream_sse

        class _Interrupted(_FakeStreamResponse):
            def __iter__(self):  # noqa: ANN201
                raise KeyboardInterrupt

        with mock.patch("cli.core.client.urlopen", return_value=_Interrupted([])):
            with pytest.raises(KeyboardInterrupt):
                list(stream_sse("/x", {}))
