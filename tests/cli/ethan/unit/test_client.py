"""Tests for cli/core/client.py — HTTP client."""
from __future__ import annotations

import json
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
        from cli.core.client import alive
        from urllib.error import URLError
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
        from cli.core.client import send
        from urllib.error import URLError

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
        from cli.core.client import get_state
        from urllib.error import URLError
        mock_api_server["raise_on"] = ("state", URLError("Connection refused"))
        assert get_state() is None