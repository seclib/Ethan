"""Integration tests for API interaction patterns."""

from __future__ import annotations

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
        from urllib.error import HTTPError

        from cli.core.client import send

        def _error_side_effect(url, *_args, **_kwargs):
            raise HTTPError(url, 400, "Bad Request", {}, None)

        with mock.patch("cli.core.client.urlopen", side_effect=_error_side_effect):
            with pytest.raises(Exception):
                send("Hello")

    def test_send_handles_http_500(self) -> None:
        from urllib.error import HTTPError

        from cli.core.client import send

        def _error_side_effect(url, *_args, **_kwargs):
            raise HTTPError(url, 500, "Server Error", {}, None)

        with mock.patch("cli.core.client.urlopen", side_effect=_error_side_effect):
            with pytest.raises(Exception):
                send("Hello")

    def test_send_connection_refused(self) -> None:
        from urllib.error import URLError

        from cli.core.client import send

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
        from urllib.error import HTTPError

        from cli.core.client import alive

        def _404(url, *_args, **_kwargs):
            raise HTTPError(url, 404, "Not Found", {}, None)

        with mock.patch("cli.core.client.urlopen", side_effect=_404):
            assert alive() is False

    def test_alive_500(self) -> None:
        from urllib.error import HTTPError

        from cli.core.client import alive

        def _500(url, *_args, **_kwargs):
            raise HTTPError(url, 500, "Server Error", {}, None)

        with mock.patch("cli.core.client.urlopen", side_effect=_500):
            assert alive() is False

    def test_alive_connection_refused(self) -> None:
        from urllib.error import URLError

        from cli.core.client import alive

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
        from urllib.error import HTTPError

        from cli.core.client import get_state

        def _error(url, *_args, **_kwargs):
            raise HTTPError(url, 500, "Error", {}, None)

        with mock.patch("cli.core.client.urlopen", side_effect=_error):
            assert get_state() is None


class TestBaseURLEnvironment:
    """BASE est résolu depuis ETHAN_API au chargement du module."""

    @staticmethod
    def _fresh_client():
        """Charge client.py dans un module NEUF (sans passer par reload()).

        `importlib.reload()` réexécute le module via le finder courant : sous
        pytest, les hooks d'alias de modules renvoient un loader statique et le
        reload devient un no-op silencieux (`BASE` gardait sa valeur initiale).
        Exécuter un module frais teste réellement la lecture de l'environnement.
        """
        import importlib.util
        from pathlib import Path

        import cli.core.client as client

        spec = importlib.util.spec_from_file_location(
            "_ethan_client_under_test", Path(client.__file__)
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_base_url_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ETHAN_API", "http://custom:9000")
        assert self._fresh_client().BASE == "http://custom:9000"

    def test_base_url_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ETHAN_API", raising=False)
        assert self._fresh_client().BASE == "http://localhost:8000"
