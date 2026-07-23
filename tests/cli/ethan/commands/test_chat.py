"""Tests for cli/commands/chat.py — ethan chat command."""
from __future__ import annotations

from unittest import mock

import pytest


class TestChatCommand:
    """cmd_chat/ethan chat tests."""

    def test_chat_starts_new_session(self, mock_client_alive, mock_client_send) -> None:
        from cli.commands.chat import cmd_chat
        with mock.patch("sys.stdin.readline", side_effect=EOFError):
            result = cmd_chat([])
            # Should exit cleanly on EOF
            assert result == 0

    def test_chat_resume_session(self, mock_client_alive, mock_client_send) -> None:
        from cli.commands.chat import cmd_chat
        with mock.patch("sys.stdin.readline", side_effect=EOFError):
            result = cmd_chat(["--resume"])
            assert result == 0

    def test_chat_resume_short_flag(self, mock_client_alive, mock_client_send) -> None:
        from cli.commands.chat import cmd_chat
        with mock.patch("sys.stdin.readline", side_effect=EOFError):
            result = cmd_chat(["-r"])
            assert result == 0

    def test_chat_exit_slash_command(self, mock_client_alive, mock_client_send) -> None:
        from cli.commands.chat import cmd_chat
        with mock.patch("sys.stdin.readline", side_effect=["/exit"]):
            result = cmd_chat([])
            assert result == 0

    def test_chat_quit_slash_command(self, mock_client_alive, mock_client_send) -> None:
        from cli.commands.chat import cmd_chat
        with mock.patch("sys.stdin.readline", side_effect=["/q"]):
            result = cmd_chat([])
            assert result == 0

    def test_chat_unknown_slash(self, mock_client_alive, mock_client_send) -> None:
        from cli.commands.chat import cmd_chat
        with mock.patch("sys.stdin.readline", side_effect=["/unknown", EOFError]):
            result = cmd_chat([])
            assert result == 0

    def test_chat_api_unreachable(self) -> None:
        from cli.commands.chat import cmd_chat
        with mock.patch("cli.commands.chat.alive", return_value=False):
            result = cmd_chat([])
            assert result == 1

    def test_chat_send_message(self, mock_client_alive, mock_client_send) -> None:
        from cli.commands.chat import cmd_chat
        with mock.patch("sys.stdin.readline", side_effect=["hello", "/exit"]):
            result = cmd_chat([])
            assert result == 0

    def test_chat_slash_history(self, mock_client_alive, mock_client_send) -> None:
        from cli.commands.chat import cmd_chat
        with mock.patch("sys.stdin.readline", side_effect=["/history", "/exit"]):
            result = cmd_chat([])
            assert result == 0

    def test_chat_slash_reset(self, mock_client_alive, mock_client_send) -> None:
        from cli.commands.chat import cmd_chat
        with mock.patch("sys.stdin.readline", side_effect=["/reset", "/exit"]):
            result = cmd_chat([])
            assert result == 0

    def test_chat_slash_new(self, mock_client_alive, mock_client_send) -> None:
        from cli.commands.chat import cmd_chat
        with mock.patch("sys.stdin.readline", side_effect=["/new", "/exit"]):
            result = cmd_chat([])
            assert result == 0

    def test_chat_slash_session(self, mock_client_alive, mock_client_send) -> None:
        from cli.commands.chat import cmd_chat
        with mock.patch("sys.stdin.readline", side_effect=["/session", "/exit"]):
            result = cmd_chat([])
            assert result == 0

    def test_chat_slash_ctx(self, mock_client_alive, mock_client_send) -> None:
        from cli.commands.chat import cmd_chat
        with mock.patch("sys.stdin.readline", side_effect=["/ctx", "/exit"]):
            result = cmd_chat([])
            assert result == 0

    def test_chat_slash_resume(self, mock_client_alive, mock_client_send) -> None:
        from cli.commands.chat import cmd_chat
        with mock.patch("sys.stdin.readline", side_effect=["/resume", "/exit"]):
            result = cmd_chat([])
            assert result == 0