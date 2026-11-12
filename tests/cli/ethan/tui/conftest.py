"""Fixtures pour les tests du TUI ETHAN."""

from __future__ import annotations

import queue
import threading
from typing import Any

import pytest

from interfaces.cli.tui.core_client import TuiCoreClient
from interfaces.cli.tui.models import (
    Agent,
    ChatSummary,
    ConnectionStatus,
    Model,
    Provider,
    Tool,
)
from interfaces.cli.tui.terminal import Terminal


class FakeCoreClient(TuiCoreClient):
    """Client Core factice pour les tests (pas de réseau)."""

    def __init__(self) -> None:
        super().__init__(timeout=1.0, abort_event=threading.Event())
        self.agents: list[Agent] = [Agent(id="agent-1", name="Atreus", model="m1", provider="ollama", tool_ids=("t1",))]
        self.models: list[Model] = [Model(id="m1", name="m1", provider="ollama", context_length=4096)]
        self.providers: list[Provider] = [Provider(id="ollama", name="Ollama", type="ollama", enabled=True, status="connected", is_default=True, default_model="m1")]
        self.tools: list[Tool] = [Tool(id="t1", name="web_search", description="search", category="search", provider="builtin", risk_level="low")]
        self.chats: list[ChatSummary] = [ChatSummary(id="chat-1", title="Conv 1", updated_at="2026-11-10T00:00:00")]
        self.messages: dict[str, list[Any]] = {"chat-1": []}
        self.state: dict[str, Any] = {"mode": "idle"}
        self.available: bool = True
        self.pending_approvals: list[Any] = []
        self.pending_hrot: list[Any] = []
        self.stream_events: list[Any] = []
        self.stream_error: Exception | None = None
        self.calls: list[tuple[str, str, Any]] = []

    # Overrides
    def is_available(self) -> bool:
        return self.available

    def get_state(self) -> dict[str, Any]:
        self.calls.append(("GET", "/v1/state", None))
        return self.state

    def list_agents(self) -> list[Agent]:
        self.calls.append(("GET", "/v1/agents", None))
        return list(self.agents)

    def list_models(self) -> list[Model]:
        self.calls.append(("GET", "/models", None))
        return list(self.models)

    def list_providers(self) -> list[Provider]:
        self.calls.append(("GET", "/providers", None))
        return list(self.providers)

    def list_tools(self) -> list[Tool]:
        self.calls.append(("GET", "/v1/tools", None))
        return list(self.tools)

    def list_chats(self) -> list[ChatSummary]:
        self.calls.append(("GET", "/chats", None))
        return list(self.chats)

    def get_chat_messages(self, chat_id: str) -> list[Any]:
        self.calls.append(("GET", f"/chats/{chat_id}/messages", None))
        from interfaces.cli.tui.models import ChatMessage
        result = []
        for m in self.messages.get(chat_id, []):
            result.append(m)
        return result

    def create_chat(self, title: str) -> ChatSummary:
        self.calls.append(("POST", "/chats", title))
        new = ChatSummary(id="chat-new", title=title, updated_at="2026-11-10T00:00:01")
        self.chats.insert(0, new)
        self.messages[new.id] = []
        return new

    def list_pending_approvals(self) -> list[Any]:
        self.calls.append(("GET", "/internal/approval/pending", None))
        return list(self.pending_approvals)

    def resolve_approval(self, request_id: str, approved: bool, reason: str = "") -> bool:
        self.calls.append(("POST", "/internal/approval/resolve", (request_id, approved)))
        return True

    def list_pending_hrot(self) -> list[Any]:
        self.calls.append(("GET", "/internal/hrot/pending", None))
        return list(self.pending_hrot)

    def resolve_hrot(self, approval_id: str, approved: bool, reason: str = "") -> bool:
        self.calls.append(("POST", "/internal/hrot/resolve", (approval_id, approved)))
        return True

    def send_stream(self, payload: dict[str, Any]) -> Any:
        self.calls.append(("STREAM", "/v1/chat/completions/stream", payload))
        if self.stream_error is not None:
            raise self.stream_error
        # Yield from a list
        def _gen():
            for ev in self.stream_events:
                yield ev
        return _gen()

    def abort_stream(self) -> None:
        self.calls.append(("ABORT", "", None))

    def reset_abort(self) -> None:
        pass


@pytest.fixture
def fake_client() -> FakeCoreClient:
    return FakeCoreClient()


@pytest.fixture
def tui_app(fake_client):
    from interfaces.cli.tui.app import TuiApp
    from rich.console import Console

    term = Terminal()
    app = TuiApp(client=fake_client, console=Console(force_terminal=True, width=80, height=24, no_color=True), terminal=term, color=False)
    return app
