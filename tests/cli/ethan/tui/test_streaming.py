"""Tests du flux SSE et de l'application du TUI."""

from __future__ import annotations

import threading
from unittest import mock

import pytest

from interfaces.cli.tui.app import TuiApp
from interfaces.cli.tui.core_client import StreamError, run_stream_worker
from interfaces.cli.tui.models import (
    ContentEvent,
    ContentReplaceEvent,
    DoneEvent,
    ErrorEvent,
    ToolCallEvent,
    ToolResultEvent,
)


def test_run_stream_worker_pushes_events(monkeypatch):
    from interfaces.cli.tui import core_client as cc

    class FakeClient:
        def send_stream(self, payload):
            yield ContentEvent(type="content", chat_id="c1", content="hi")
            yield DoneEvent(type="done", chat_id="c1", message_id="m1")

        def reset_abort(self):
            pass

    q = __import__("queue").Queue()
    run_stream_worker(FakeClient(), {"message": "x"}, q)
    items = []
    while True:
        it = q.get()
        if it is None:
            break
        items.append(it)
    assert len(items) == 2
    assert isinstance(items[0], ContentEvent)
    assert isinstance(items[1], DoneEvent)


def test_run_stream_worker_pushes_error(monkeypatch):
    from interfaces.cli.tui import core_client as cc

    class FakeClient:
        def send_stream(self, payload):
            raise RuntimeError("boom")
            yield  # pragma: no cover

        def reset_abort(self):
            pass

    q = __import__("queue").Queue()
    run_stream_worker(FakeClient(), {"message": "x"}, q)
    items = []
    while True:
        it = q.get()
        if it is None:
            break
        items.append(it)
    assert len(items) == 1
    assert isinstance(items[0], StreamError)
    assert "boom" in items[0].message


def test_apply_event_content(tui_app):
    from interfaces.cli.tui.models import Message
    msg = Message(role="assistant", content="", status="pending")
    tui_app.state.messages.append(msg)
    msg.touch()
    tui_app._apply_event(ContentEvent(type="content", chat_id="c1", content="hello"))
    assert msg.content == "hello"
    assert tui_app.state.current_chat_id == "c1"


def test_apply_event_content_replace(tui_app):
    from interfaces.cli.tui.models import Message
    msg = Message(role="assistant", content="old", status="pending")
    tui_app.state.messages.append(msg)
    msg.touch()
    tui_app._apply_event(ContentReplaceEvent(type="content_replace", chat_id="c1", content="new"))
    assert msg.content == "new"


def test_apply_event_tool_call(tui_app):
    from interfaces.cli.tui.models import Message
    msg = Message(role="assistant", content="", status="pending")
    tui_app.state.messages.append(msg)
    msg.touch()
    tui_app._apply_event(ToolCallEvent(type="tool_call", chat_id="c1", tool="web_search", params={"query": "q"}))
    assert len(msg.tool_calls) == 1
    assert msg.tool_calls[0].name == "web_search"
    assert msg.tool_calls[0].status == "pending"


def test_apply_event_tool_result(tui_app):
    from interfaces.cli.tui.models import Message, ToolCallView
    msg = Message(role="assistant", content="", status="pending")
    msg.tool_calls.append(ToolCallView(name="web_search", params="{}", status="pending"))
    tui_app.state.messages.append(msg)
    msg.touch()
    tui_app._apply_event(ToolResultEvent(type="tool_result", chat_id="c1", tool="web_search", status="rejected", output="denied"))
    assert msg.tool_calls[0].status == "rejected"
    assert msg.tool_calls[0].output == "denied"


def test_apply_event_done(tui_app):
    from interfaces.cli.tui.models import Message
    msg = Message(role="assistant", content="hi", status="pending")
    tui_app.state.messages.append(msg)
    msg.touch()
    tui_app.state.current_chat_id = None
    tui_app._apply_event(DoneEvent(type="done", chat_id="c1", message_id="m1"))
    assert tui_app.state.current_chat_id == "c1"
    assert msg.status == "done"
    assert msg.message_id == "m1"


def test_apply_event_error(tui_app):
    from interfaces.cli.tui.models import Message
    msg = Message(role="assistant", content="", status="pending")
    tui_app.state.messages.append(msg)
    msg.touch()
    tui_app._apply_event(ErrorEvent(type="error", error="boom"))
    assert msg.status == "error"
    assert any(m.role == "system" and "boom" in m.content for m in tui_app.state.messages)


def test_submit_streams(tui_app, fake_client):
    fake_client.stream_events = []  # empty stream
    from interfaces.cli.tui.models import ConnectionStatus
    tui_app.state.connection = ConnectionStatus.CONNECTED
    tui_app.state.input = "hello"
    tui_app._submit()
    assert tui_app.state.input == ""
    assert any(m.role == "user" and m.content == "hello" for m in tui_app.state.messages)
    assert tui_app.state.streaming is True
    # Wait for thread to finish
    if tui_app.state.stream_thread is not None:
        tui_app.state.stream_thread.join(timeout=2.0)
    tui_app._drain_stream_queue()
    assert tui_app.state.streaming is False


def test_submit_slash_command(tui_app):
    tui_app.state.input = "/help"
    tui_app._submit()
    assert tui_app.state.active_panel is not None
    from interfaces.cli.tui.models import PanelKind
    assert tui_app.state.active_panel == PanelKind.HELP


def test_submit_empty_does_nothing(tui_app):
    tui_app.state.input = "   "
    before = len(tui_app.state.messages)
    tui_app._submit()
    assert len(tui_app.state.messages) == before
