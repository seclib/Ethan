"""Integration tests for timeout scenarios."""
from __future__ import annotations

import time
from unittest import mock

import pytest


class TestClientTimeout:
    """Timeout handling in HTTP client operations."""

    def test_send_timeout(self) -> None:
        from cli.core.client import send
        from urllib.error import URLError

        def _timeout(*_args, **_kwargs):
            raise URLError("timed out")

        with mock.patch("cli.core.client.urlopen", side_effect=_timeout):
            with pytest.raises(Exception):
                send("Hello")

    def test_alive_timeout(self) -> None:
        from cli.core.client import alive
        from urllib.error import URLError

        def _timeout(*_args, **_kwargs):
            raise URLError("timed out")

        with mock.patch("cli.core.client.urlopen", side_effect=_timeout):
            assert alive() is False

    def test_get_state_timeout(self) -> None:
        from cli.core.client import get_state
        from urllib.error import URLError

        def _timeout(*_args, **_kwargs):
            raise URLError("timed out")

        with mock.patch("cli.core.client.urlopen", side_effect=_timeout):
            assert get_state() is None


class TestDaemonTimeout:
    """Timeout handling in daemon state fetching."""

    def test_fetch_state_timeout(self) -> None:
        from cli.core.daemon import _fetch_state
        from urllib.error import URLError

        def _timeout(*_args, **_kwargs):
            raise URLError("timed out")

        with mock.patch("cli.core.daemon.urlopen", side_effect=_timeout):
            assert _fetch_state() is None

    def test_fetch_state_slow_response(self) -> None:
        from cli.core.daemon import _fetch_state

        def _slow(*_args, **_kwargs):
            time.sleep(0.5)
            raise TimeoutError("timed out after 0.5s")

        with mock.patch("cli.core.daemon.urlopen", side_effect=_slow):
            result = _fetch_state()
            assert result is None


class TestTimeoutErrorFormatting:
    """Timeout error formatting tests."""

    def test_timeout_error_constructor(self) -> None:
        from cli.core.errors import timeout, EthanError
        err = timeout(10)
        assert isinstance(err, EthanError)
        assert err.code == "SYS-002"
        assert "10s" in err.title or "10" in err.title

    def test_timeout_error_format(self) -> None:
        from cli.core.errors import timeout, format_error
        err = timeout(30)
        result = format_error(err)
        assert "SYS-002" in result
        assert "Timeout" in result

    def test_configurable_timeout(self) -> None:
        from cli.core.config import get
        timeout_val = get("api.timeout")
        assert timeout_val == 10


class TestStreamingTimeout:
    """Timeout in streaming operations."""

    def test_streaming_no_block(self) -> None:
        from cli.core.streaming import Streamer
        streamer = Streamer()
        streamer.start()
        streamer.write("fast response")
        streamer.done()
        assert "fast response" in streamer.text