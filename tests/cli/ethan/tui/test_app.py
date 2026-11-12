"""Tests de l'application TUI ETHAN."""

from __future__ import annotations

import pytest

from interfaces.cli.tui.app import TuiApp
from interfaces.cli.tui.models import PanelKind, Message


def test_initial_load(tui_app, fake_client):
    tui_app._load_initial()
    assert tui_app.state.connection.value == "connected"
    assert len(tui_app.state.agents) == 1
    assert len(tui_app.state.models) == 1
    assert len(tui_app.state.chats) == 1
    # La session la plus récente est reprise
    assert tui_app.state.current_chat_id == "chat-1"


def test_render_returns_frame(tui_app):
    tui_app._load_initial()
    frame = tui_app._render(80, 24)
    assert isinstance(frame, str)
    assert "ETHAN TUI" in frame
    assert len(frame.split("\n")) == 24


def test_render_wide_shows_sidebar(tui_app):
    tui_app._load_initial()
    frame = tui_app._render(140, 30)
    assert isinstance(frame, str)
    assert "ETHAN TUI" in frame
    assert "SESSION" in frame
    assert "AGENT" in frame
    assert "MODEL" in frame
    assert "PROVIDER" in frame
    assert "TOOLS" in frame
    assert "HROT" in frame
    assert len(frame.split("\n")) == 30


def test_render_narrow_hides_sidebar(tui_app):
    tui_app._load_initial()
    frame = tui_app._render(80, 24)
    assert "SESSION" not in frame


def test_sidebar_focus_toggle(tui_app):
    from interfaces.cli.tui.models import Keypress, KeyKind
    tui_app._load_initial()
    # Simulate wide terminal
    tui_app._terminal.size = lambda: (140, 30)
    # Tab with empty input focuses sidebar
    tui_app.state.input = ""
    tui_app._handle_keypress(Keypress(KeyKind.TAB))
    assert tui_app.state.sidebar_focus is True
    assert tui_app.state.sidebar_index == 0
    # Down moves
    tui_app._handle_keypress(Keypress(KeyKind.DOWN))
    assert tui_app.state.sidebar_index == 1
    # Enter opens panel
    tui_app._handle_keypress(Keypress(KeyKind.ENTER))
    assert tui_app.state.sidebar_focus is False
    from interfaces.cli.tui.models import PanelKind
    assert tui_app.state.active_panel == PanelKind.AGENTS
    # Esc closes panel
    tui_app._handle_keypress(Keypress(KeyKind.ESCAPE))
    assert tui_app.state.active_panel == PanelKind.NONE


def test_sidebar_focus_disabled_narrow(tui_app):
    from interfaces.cli.tui.models import Keypress, KeyKind
    tui_app._load_initial()
    tui_app.state.input = ""
    # Simulate narrow: sidebar_focus should not activate via Tab
    # (Tab falls through to autocomplete)
    tui_app._handle_keypress(Keypress(KeyKind.TAB))
    # In test env terminal is not wide, so sidebar_focus stays False
    assert tui_app.state.sidebar_focus is False


def test_keypress_slash_panel(tui_app):
    tui_app._load_initial()
    from interfaces.cli.tui.models import Keypress, KeyKind
    tui_app._handle_keypress(Keypress(KeyKind.CHARACTER, "/"))
    # typing /help
    for ch in "help":
        tui_app._handle_keypress(Keypress(KeyKind.CHARACTER, ch))
    assert tui_app.state.input == "/help"
    tui_app._handle_keypress(Keypress(KeyKind.ENTER))
    assert tui_app.state.active_panel == PanelKind.HELP


def test_panel_navigation(tui_app, fake_client):
    tui_app._load_initial()
    tui_app._cmd_sessions([])
    assert tui_app.state.active_panel == PanelKind.SESSIONS
    from interfaces.cli.tui.models import Keypress, KeyKind
    # Esc ferme
    tui_app._handle_keypress(Keypress(KeyKind.ESCAPE))
    assert tui_app.state.active_panel == PanelKind.NONE


def test_resume_chat(tui_app, fake_client):
    from interfaces.cli.tui.models import ChatMessage
    fake_client.messages["chat-1"] = [
        ChatMessage(id="m1", role="user", content="salut", status="done"),
        ChatMessage(id="m2", role="assistant", content="bonjour", status="done"),
    ]
    tui_app._load_initial()
    assert tui_app.state.current_chat_id == "chat-1"
    assert len(tui_app.state.messages) == 2
    assert tui_app.state.messages[0].content == "salut"


def test_agent_selection(tui_app):
    tui_app._load_initial()
    tui_app._cmd_agent(["agent-1"])
    assert tui_app.state.selected_agent_id == "agent-1"
    assert tui_app.state.selected_provider_id == "ollama"
    assert tui_app.state.selected_model_id == "m1"


def test_model_selection(tui_app):
    tui_app._load_initial()
    tui_app._cmd_model(["m1"])
    assert tui_app.state.selected_model_id == "m1"


def test_provider_selection(tui_app):
    tui_app._load_initial()
    tui_app._cmd_provider(["ollama"])
    assert tui_app.state.selected_provider_id == "ollama"
    assert tui_app.state.selected_agent_id is None


def test_tools_toggle(tui_app):
    tui_app._load_initial()
    tui_app._cmd_tools([])
    assert tui_app.state.active_panel == PanelKind.TOOLS
    # Sélectionner le premier outil
    tui_app._panel_activate()
    assert "t1" in tui_app.state.selected_tool_ids


def test_approve_panel(tui_app, fake_client):
    from interfaces.cli.tui.models import ApprovalItem
    fake_client.pending_approvals = [ApprovalItem(id="ap1", kind="approval", title="Test", category="file_write", status="pending")]
    tui_app._load_initial()
    tui_app._cmd_approve([])
    assert tui_app.state.active_panel == PanelKind.APPROVALS
    assert len(tui_app.state.approvals) == 1
    # Approuver
    tui_app._approve_selected(True)
    assert len(tui_app.state.approvals) == 0


def test_core_unavailable(tui_app, fake_client):
    fake_client.available = False
    # Forcer les listes à lever
    def boom(*a, **k):
        raise RuntimeError("down")
    fake_client.list_agents = boom  # type: ignore[assignment]
    fake_client.list_models = boom  # type: ignore[assignment]
    fake_client.list_providers = boom  # type: ignore[assignment]
    fake_client.list_tools = boom  # type: ignore[assignment]
    fake_client.list_chats = boom  # type: ignore[assignment]
    tui_app._load_initial()
    assert tui_app.state.connection.value == "error"
    assert tui_app.state.error is not None


def test_new_command(tui_app):
    tui_app._load_initial()
    tui_app._cmd_new([])
    assert tui_app.state.current_chat_id is None
    assert any(m.role == "system" for m in tui_app.state.messages)


def test_autocomplete(tui_app):
    tui_app.state.input = "/he"
    tui_app._autocomplete()
    assert tui_app.state.input == "/help "
    assert tui_app.state.cursor == len("/help ")
