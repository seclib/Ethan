"""Tests for cli/core/daemon.py — daemon lifecycle."""
from __future__ import annotations

import os
from unittest import mock

import pytest
from helpers import patch_os_kill, patch_fork, write_pid_file, write_cache_file


class TestPidManagement:
    """PID file management tests."""

    def test_pid_write(self) -> None:
        from cli.core.daemon import _pid_write, PID_FILE
        _pid_write()  # uses os.getpid()
        with open(PID_FILE) as f:
            assert f.read().strip().isdigit()

    def test_pid_read_nonexistent(self) -> None:
        from cli.core.daemon import _pid_read
        assert _pid_read() is None

    def test_pid_read_existing(self) -> None:
        from cli.core.daemon import _pid_read
        write_pid_file("tests/cli/ethan/unit/test.daemon.pid", 12345)
        with mock.patch("cli.core.daemon.PID_FILE", "tests/cli/ethan/unit/test.daemon.pid"):
            pid = _pid_read()
            assert pid == 12345

    def test_pid_remove_nonexistent(self) -> None:
        from cli.core.daemon import _pid_remove
        _pid_remove()  # should not raise

    def test_pid_remove_existing(self) -> None:
        from cli.core.daemon import _pid_remove, _pid_write, PID_FILE
        _pid_write()
        assert os.path.exists(PID_FILE)
        _pid_remove()
        assert not os.path.exists(PID_FILE)


class TestIsRunning:
    """_is_running() tests."""

    def test_is_running_none(self) -> None:
        from cli.core.daemon import _is_running
        assert _is_running(None) is False

    def test_is_running_alive(self) -> None:
        from cli.core.daemon import _is_running
        with mock.patch("cli.core.daemon.os.kill") as mk:
            assert _is_running(100) is True
            mk.assert_called_once_with(100, 0)

    def test_is_running_dead(self) -> None:
        from cli.core.daemon import _is_running
        with mock.patch("cli.core.daemon.os.kill", side_effect=ProcessLookupError):
            assert _is_running(999) is False

    def test_is_running_permission_error(self) -> None:
        from cli.core.daemon import _is_running
        with mock.patch("cli.core.daemon.os.kill", side_effect=PermissionError):
            assert _is_running(999) is False


class TestCacheManagement:
    """Cache file management tests."""

    def test_cache_write_and_read(self) -> None:
        from cli.core.daemon import _cache_write, _cache_read
        state = {"mode": "running", "active_goal": "test"}
        _cache_write(state)
        cached = _cache_read()
        assert cached is not None
        assert cached["state"]["mode"] == "running"

    def test_cache_read_nonexistent(self) -> None:
        from cli.core.daemon import _cache_read
        assert _cache_read() is None

    def test_cache_read_corrupt(self) -> None:
        from cli.core.daemon import CACHE_FILE, _cache_read
        with open(CACHE_FILE, "w") as f:
            f.write("not valid json")
        assert _cache_read() is None


class TestCmdStart:
    """cmd_start() tests."""

    def test_start_daemon(self) -> None:
        from cli.core.daemon import cmd_start
        with patch_fork():
            with mock.patch("cli.core.daemon._is_running", return_value=False):
                with mock.patch("cli.core.daemon._daemon_loop"):
                    cmd_start([])

    def test_start_already_running(self) -> None:
        from cli.core.daemon import cmd_start
        with mock.patch("cli.core.daemon._is_running", return_value=True):
            with pytest.raises(SystemExit):
                cmd_start([])

    def test_start_failed(self) -> None:
        from cli.core.daemon import cmd_start
        with patch_fork():
            with mock.patch("cli.core.daemon._is_running", side_effect=[False, False]):
                with mock.patch("cli.core.daemon._daemon_loop"):
                    with pytest.raises(SystemExit):
                        cmd_start([])

    def test_start_with_interval(self) -> None:
        from cli.core.daemon import cmd_start
        with patch_fork():
            with mock.patch("cli.core.daemon._is_running", return_value=False):
                with mock.patch("cli.core.daemon._daemon_loop"):
                    cmd_start(["--interval", "10"])


class TestCmdStop:
    """cmd_stop() tests."""

    def test_stop_not_running(self) -> None:
        from cli.core.daemon import cmd_stop
        with mock.patch("cli.core.daemon._is_running", return_value=False):
            cmd_stop([])

    def test_stop_running(self) -> None:
        from cli.core.daemon import cmd_stop
        with mock.patch("cli.core.daemon._is_running", return_value=True):
            with mock.patch("cli.core.daemon._pid_read", return_value=100):
                with mock.patch("cli.core.daemon._pid_remove"):
                    with mock.patch("cli.core.daemon.os.kill"):
                        cmd_stop([])

    def test_stop_already_dead(self) -> None:
        from cli.core.daemon import cmd_stop
        with mock.patch("cli.core.daemon._is_running", return_value=False):
            with mock.patch("cli.core.daemon._pid_read", return_value=100):
                with mock.patch("cli.core.daemon._pid_remove"):
                    cmd_stop([])


class TestCmdStatus:
    """cmd_status() tests."""

    def test_status_running(self, capsys) -> None:
        from cli.core.daemon import cmd_status
        with mock.patch("cli.core.daemon._is_running", return_value=True):
            with mock.patch("cli.core.daemon._pid_read", return_value=100):
                cmd_status([])
                captured = capsys.readouterr()
                assert "running" in captured.out

    def test_status_stopped(self, capsys) -> None:
        from cli.core.daemon import cmd_status
        with mock.patch("cli.core.daemon._is_running", return_value=False):
            cmd_status([])
            captured = capsys.readouterr()
            assert "stopped" in captured.out

    def test_status_with_cache(self, capsys) -> None:
        from cli.core.daemon import cmd_status, CACHE_FILE
        write_cache_file(CACHE_FILE, {"mode": "running", "active_goal": "test"})
        with mock.patch("cli.core.daemon._is_running", return_value=True):
            with mock.patch("cli.core.daemon._pid_read", return_value=100):
                cmd_status([])
                captured = capsys.readouterr()
                assert "running" in captured.out
                assert "test" in captured.out

    def test_status_without_cache(self, capsys) -> None:
        from cli.core.daemon import cmd_status
        with mock.patch("cli.core.daemon._is_running", return_value=False):
            cmd_status([])
            captured = capsys.readouterr()
            assert "stopped" in captured.out
            assert "cache" in captured.out.lower()


