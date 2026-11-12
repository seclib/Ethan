"""Tests du client TUI ETHAN (projection des contrats Core)."""

from __future__ import annotations

import pytest

from interfaces.cli.tui.core_client import TuiCoreClient, parse_stream_event
from interfaces.cli.tui.models import (
    ContentEvent,
    DoneEvent,
    ErrorEvent,
    ToolCallEvent,
    ToolResultEvent,
)


def test_parse_stream_event_content():
    ev = parse_stream_event({"type": "content", "chat_id": "c1", "content": "hi"})
    assert isinstance(ev, ContentEvent)
    assert ev.content == "hi"
    assert ev.chat_id == "c1"


def test_parse_stream_event_tool_call():
    ev = parse_stream_event({"type": "tool_call", "chat_id": "c1", "tool": "web_search", "params": {"query": "q"}})
    assert isinstance(ev, ToolCallEvent)
    assert ev.tool == "web_search"
    assert ev.params == {"query": "q"}


def test_parse_stream_event_tool_result():
    ev = parse_stream_event({"type": "tool_result", "chat_id": "c1", "tool": "web_search", "status": "rejected", "output": "denied"})
    assert isinstance(ev, ToolResultEvent)
    assert ev.status == "rejected"
    assert ev.output == "denied"


def test_parse_stream_event_done():
    ev = parse_stream_event({"type": "done", "chat_id": "c1", "message_id": "m1"})
    assert isinstance(ev, DoneEvent)
    assert ev.message_id == "m1"


def test_parse_stream_event_error():
    ev = parse_stream_event({"type": "error", "error": "boom"})
    assert isinstance(ev, ErrorEvent)
    assert ev.error == "boom"


def test_parse_stream_event_unknown_returns_none():
    assert parse_stream_event({"type": "foo"}) is None
    assert parse_stream_event("not a dict") is None


def _patch_recorder(monkeypatch, recorder):
    import cli.tui.core_client as mod
    monkeypatch.setattr(mod, "request_json", recorder)
    # stream_sse stays real-ish; not used here


def test_list_agents(monkeypatch):
    recorder = lambda method, path, *a, **k: [{"id": "a1", "name": "A", "model": "m", "provider": "p", "tool_ids": ["t"]}]
    _patch_recorder(monkeypatch, recorder)
    client = TuiCoreClient(timeout=1.0)
    agents = client.list_agents()
    assert len(agents) == 1
    assert agents[0].id == "a1"
    assert agents[0].tool_ids == ("t",)


def test_list_models(monkeypatch):
    recorder = lambda method, path, *a, **k: [{"id": "m1", "name": "m1", "provider": "ollama", "context_length": 4096, "is_available": True, "capabilities": ["chat"]}]
    _patch_recorder(monkeypatch, recorder)
    client = TuiCoreClient(timeout=1.0)
    models = client.list_models()
    assert models[0].id == "m1"
    assert models[0].capabilities == ("chat",)


def test_list_providers(monkeypatch):
    recorder = lambda method, path, *a, **k: [{"id": "ollama", "name": "Ollama", "type": "ollama", "enabled": True, "status": "connected", "is_default": True, "default_model": "m1", "models": ["m1"]}]
    _patch_recorder(monkeypatch, recorder)
    client = TuiCoreClient(timeout=1.0)
    providers = client.list_providers()
    assert providers[0].id == "ollama"
    assert providers[0].is_default is True


def test_list_tools(monkeypatch):
    recorder = lambda method, path, *a, **k: [{"id": "t1", "name": "web_search", "description": "d", "category": "search", "provider": "builtin", "risk_level": "low", "is_available": True, "parameters": {"q": 1}}]
    _patch_recorder(monkeypatch, recorder)
    client = TuiCoreClient(timeout=1.0)
    tools = client.list_tools()
    assert tools[0].id == "t1"
    assert tools[0].parameters == {"q": 1}


def test_list_chats(monkeypatch):
    recorder = lambda method, path, *a, **k: [{"id": "c1", "title": "T", "updated_at": "2026-11-10", "created_at": "2026-11-09", "messages": [1, 2]}]
    _patch_recorder(monkeypatch, recorder)
    client = TuiCoreClient(timeout=1.0)
    chats = client.list_chats()
    assert chats[0].id == "c1"
    assert chats[0].message_count == 2


def test_is_available_false_on_error(monkeypatch):
    def recorder(method, path, *a, **k):
        raise RuntimeError("down")
    _patch_recorder(monkeypatch, recorder)
    client = TuiCoreClient(timeout=1.0)
    assert client.is_available() is False


def test_list_pending_approvals_empty_on_error(monkeypatch):
    from interfaces.cli.core.errors import connection_error

    def recorder(method, path, *a, **k):
        raise connection_error("down")
    _patch_recorder(monkeypatch, recorder)
    client = TuiCoreClient(timeout=1.0)
    assert client.list_pending_approvals() == []
    assert client.list_pending_hrot() == []


def test_get_chat_messages(monkeypatch):
    recorder = lambda method, path, *a, **k: [{"id": "m1", "role": "user", "content": "hi", "status": "done"}]
    _patch_recorder(monkeypatch, recorder)
    client = TuiCoreClient(timeout=1.0)
    msgs = client.get_chat_messages("c1")
    assert len(msgs) == 1
    assert msgs[0].content == "hi"
