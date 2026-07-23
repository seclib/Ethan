"""Integration tests for API interaction patterns."""
from __future__ import annotations

import json
from unittest import mock

import pytest


class TestSendAPIIntegration:
    """send() with mocked HTTP — full request/response cycle."""

    def test_send_success_flow(self, mock_api_server) -> None:
        from cli.core.client import send
        text, latency = send("Hello")
        assert text == "Hello from Ethan"
        assert isinstance(latency, int)
        assert latency >= 0

    def test_send_with_session_id_passthrough(self, mock_api_server) -> None:
        from cli.core.client import send
        text, latency = send("Hello", session_id="session-abc-123")
        assert text == "Hello from Ethan"

    def test_send_handles_http_400(self) -> None:
        from cli.core.client import send
        from urllib.error import HTTPError

        def _error_side_effect(url, *_args, **_kwargs):
            raise HTTPError(url, 400, "Bad Request", {}, None)

        with mock.patch("cli.core.client.urlopen", side_effect=_error_side_effect):
            with pytest.raises(Exception):
                send("Hello")

    def test_send_handles_http_500(self) -> None:
        from cli.core.client import send
        from urllib.error import HTTPError

        def _error_side_effect(url, *_args, **_kwargs):
            raise HTTPError(url, 500, "Server Error", {}, None)

        with mock.patch("cli.core.client.urlopen", side_effect=_error_side_effect):
            with pytest.raises(Exception):
                send("Hello")

    def test_send_connection_refused(self) -> None:
        from cli.core.client import send
        from urllib.error import URLError

        def _refused(url, *_args, **_kwargs):
            raise URLError("Connection refused")

        with mock.patch("cli.core.client.urlopen", side_effect=_refused):
            with pytest.raises(Exception):
                send("Hello")


class TestAliveAPIIntegration:
    """alive() integration tests."""

    def test_alive_200(self, mock_api_server) -> None:
        from cli.core.client import alive
        assert alive() is True

    def test_alive_404(self) -> None:
        from cli.core.client import alive
        from urllib.error import HTTPError

        def _404(url, *_args, **_kwargs):
            raise HTTPError(url, 404, "Not Found", {}, None)

        with mock.patch("cli.core.client.urlopen", side_effect=_404):
            assert alive() is False

    def test_alive_500(self) -> None:
        from cli.core.client import alive
        from urllib.error import HTTPError

        def _500(url, *_args, **_kwargs):
            raise HTTPError(url, 500, "Server Error", {}, None)

        with mock.patch("cli.core.client.urlopen", side_effect=_500):
            assert alive() is False

    def test_alive_connection_refused(self) -> None:
        from cli.core.client import alive
        from urllib.error import URLError

        def _refused(url, *_args, **_kwargs):
            raise URLError("Connection refused")

        with mock.patch("cli.core.client.urlopen", side_effect=_refused):
            assert alive() is False


class TestStateAPIIntegration:
    """get_state() integration tests."""

    def test_get_state_returns_dict(self, mock_api_server) -> None:
        from cli.core.client import get_state
        state = get_state()
        assert state["mode"] == "running"
        assert state["active_goal"] == "test"
        assert state["running_tasks"] == 0

    def test_get_state_error_response(self) -> None:
        from cli.core.client import get_state
        from urllib.error import HTTPError

        def _error(url, *_args, **_kwargs):
            raise HTTPError(url, 500, "Error", {}, None)

        with mock.patch("cli.core.client.urlopen", side_effect=_error):
            assert get_state() is None


class TestBaseURLEnvironment:
    """Base URL from environment tests."""

    def test_base_url_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ETHAN_API", "http://custom:9000")
        import importlib
        import cli.core.client
        importlib.reload(cli.core.client)
        assert cli.core.client.BASE == "http://custom:9000"

    def test_base_url_default(self) -> None:
        import cli.core.client
        assert cli.core.client.BASE == "http://localhost:8000"