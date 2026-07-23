"""Integration tests for all failure modes."""
from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

import pytest


class TestAPIUnreachable:
    """All commands handle API unreachable gracefully."""

    def test_chat_api_unreachable(self) -> None:
        from cli.commands.chat import cmd_chat
        with mock.patch("cli.commands.chat.alive", return_value=False):
            result = cmd_chat([])
            assert result == 1

    def test_status_api_unreachable(self, capsys) -> None:
        from cli.commands.status import cmd_status
        with mock.patch("cli.commands.status.alive", return_value=False):
            result = cmd_status([])
            captured = capsys.readouterr()
            assert result == 0
            assert "OFFLINE" in captured.out

    def test_daemon_fetch_state_handles_refused(self) -> None:
        from cli.core.daemon import _fetch_state
        from urllib.error import URLError

        def _refused(*_args, **_kwargs):
            raise URLError("Connection refused")

        with mock.patch("cli.core.daemon.urlopen", side_effect=_refused):
            assert _fetch_state() is None


class TestCorruptConfig:
    """Corrupt configuration file handling."""

    def test_corrupt_config_file(self) -> None:
        from cli.core.config import CONFIG_FILE, load
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            f.write("not valid json {")
        config = load()
        # Should fallback to defaults
        assert config["api"]["base_url"] == "http://localhost:8000"

    def test_corrupt_local_config(self) -> None:
        from cli.core.config import CONFIG_FILE, CONFIG_LOCAL_FILE, load
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump({"api": {"base_url": "http://valid"}}, f)
        with open(CONFIG_LOCAL_FILE, "w") as f:
            f.write("corrupt json")
        config = load()
        assert config["api"]["base_url"] == "http://valid"


class TestCorruptMemory:
    """Corrupt memory file handling."""

    def test_corrupt_memory_file(self) -> None:
        from cli.core.memory import MEM_FILE, _load
        MEM_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(MEM_FILE, "w") as f:
            f.write("corrupt json")
        entries = _load()
        assert entries == []

    def test_corrupt_log_file(self) -> None:
        from cli.core.logging import LOG_FILE, _load
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "w") as f:
            f.write("corrupt json")
        entries = _load()
        assert entries == []


class TestPermissionDenied:
    """Permission error handling tests."""

    def test_permission_error_constructor(self) -> None:
        from cli.core.errors import permission_denied, EthanError
        err = permission_denied("no write access", "root")
        assert isinstance(err, EthanError)
        assert "no write access" in err.context

    def test_permission_error_format(self) -> None:
        from cli.core.errors import permission_denied, format_error
        err = permission_denied("disk full")
        result = format_error(err)
        assert "Permission denied" in result
        assert "SYS-003" in result


class TestEmptyState:
    """Empty state response handling."""

    def test_empty_state_from_api(self) -> None:
        from cli.commands.status import cmd_status
        with mock.patch("cli.commands.status.alive", return_value=True):
            with mock.patch("cli.commands.status.get_state", return_value=None):
                result = cmd_status([])
                assert result == 0

    def test_incomplete_state_response(self) -> None:
        from cli.commands.status import cmd_status
        with mock.patch("cli.commands.status.alive", return_value=True):
            with mock.patch("cli.commands.status.get_state", return_value={}):
                result = cmd_status([])
                assert result == 0


class TestPluginLoadFailure:
    """Plugin load failure handling."""

    def test_load_broken_plugin(self, tmp_path: Path) -> None:
        from cli.registry import _load_module, COMMANDS

        plugin_dir = tmp_path / "plugins" / "broken"
        plugin_dir.mkdir(parents=True)
        plugin_file = plugin_dir / "plugin.py"
        plugin_file.write_text("""
THIS IS NOT VALID PYTHON @@@@
""")
        result = _load_module(plugin_dir)
        assert result is None


class TestDaemonFailure:
    """Daemon failure handling."""

    def test_daemon_pid_corrupt(self) -> None:
        from cli.core.daemon import _pid_read, PID_FILE
        PID_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PID_FILE, "w") as f:
            f.write("not an integer")
        pid = _pid_read()
        assert pid is None

    def test_daemon_cache_corrupt(self) -> None:
        from cli.core.daemon import _cache_read, CACHE_FILE
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, "w") as f:
            f.write("corrupt json")
        cached = _cache_read()
        assert cached is None