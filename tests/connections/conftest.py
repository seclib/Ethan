"""Fixtures partagées des tests Connections (aucun réseau réel)."""

from __future__ import annotations

from typing import Any

import pytest


class FakeBus:
    """EventBus de test : enregistre les publications."""

    def __init__(self) -> None:
        self.events: list[tuple[str, Any]] = []

    async def publish(self, subject: str, event: Any) -> None:
        self.events.append((subject, event))


class FakeSecrets:
    """SecretManager de test : valeurs injectées, jamais d'env réel."""

    def __init__(self, values: dict[str, str] | None = None) -> None:
        self._values = dict(values or {})

    def get_or_none(self, name: str, default: str | None = None) -> str | None:
        return self._values.get(name, default)


class FakeResponse:
    def __init__(
        self,
        status_code: int = 200,
        json_data: Any = None,
        text: str = "",
    ) -> None:
        self.status_code = status_code
        self._json = json_data
        self.text = text

    def json(self) -> Any:
        if self._json is None:
            raise ValueError("no json payload")
        return self._json


class FakeHttp:
    """Client type-httpx : routes (method, fragment d'URL) → réponses."""

    def __init__(self) -> None:
        self._routes: dict[tuple[str, str], list[FakeResponse]] = []
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    def queue(self, method: str, url_fragment: str, response: FakeResponse) -> None:
        self._routes.append((method.upper(), url_fragment, [response]))

    def queue_many(self, method: str, url_fragment: str, responses: list[FakeResponse]) -> None:
        self._routes.append((method.upper(), url_fragment, list(responses)))

    def _respond(self, method: str, url: str) -> FakeResponse:
        for route_method, fragment, queue in self._routes:
            if route_method == method and fragment in url and queue:
                return queue.pop(0)
        return FakeResponse(599, None, f"unexpected {method} {url}")

    async def get(self, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append(("GET", url, kwargs))
        return self._respond("GET", url)

    async def post(self, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append(("POST", url, kwargs))
        return self._respond("POST", url)

    async def patch(self, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append(("PATCH", url, kwargs))
        return self._respond("PATCH", url)

    async def delete(self, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append(("DELETE", url, kwargs))
        return self._respond("DELETE", url)

    async def __aenter__(self) -> "FakeHttp":
        return self

    async def __aexit__(self, *exc: Any) -> bool:
        return False


@pytest.fixture
def fake_bus() -> FakeBus:
    return FakeBus()


@pytest.fixture
def oauth_secrets() -> FakeSecrets:
    return FakeSecrets(
        {
            "CONN_GITHUB_CLIENT_ID": "gh-id-test",
            "CONN_GITHUB_CLIENT_SECRET": "gh-secret-test",
            "CONN_EMAIL_CLIENT_ID": "google-id-test",
            "CONN_EMAIL_CLIENT_SECRET": "google-secret-test",
            "CONN_MEDIUM_CLIENT_ID": "medium-id-test",
            "CONN_MEDIUM_CLIENT_SECRET": "medium-secret-test",
            "CONN_NOTION_CLIENT_ID": "notion-id-test",
            "CONN_NOTION_CLIENT_SECRET": "notion-secret-test",
        }
    )


def make_manager(
    *,
    bus: Any = None,
    secrets: Any = None,
    http: FakeHttp | None = None,
    base_url: str = "https://ethan.test",
) -> Any:
    """ConnectionManager prêt à l'emploi (store mémoire, HTTP fictif)."""
    from core.integrations.connections import ConnectionManager
    from core.state.record_store import CoreRecordStore

    return ConnectionManager(
        store=CoreRecordStore(),
        event_bus=bus,
        secrets=secrets or FakeSecrets({}),
        http_factory=lambda: http if http is not None else FakeHttp(),
        base_url=base_url,
    )
