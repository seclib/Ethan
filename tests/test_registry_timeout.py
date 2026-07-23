"""Tests for ETHAN CLI registry timeout — command timeout mechanism."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "cli"))


def test_registry_import():
    from cli.registry import dispatch, register, TimeoutError, _COMMAND_TIMEOUT, _get_handler
    assert callable(dispatch)
    assert callable(register)
    assert callable(_get_handler)


def test_timeout_error_class():
    from cli.registry import TimeoutError
    err = TimeoutError("timeout")
    assert isinstance(err, Exception)
    assert "timeout" in str(err)


def test_command_timeout_constant():
    from cli.registry import _COMMAND_TIMEOUT
    assert _COMMAND_TIMEOUT > 0
    assert _COMMAND_TIMEOUT <= 600  # max 10 minutes


def test_dispatch_returns_int_zero():
    """dispatch([]) should return 0 with 'help'."""
    from cli.registry import dispatch, discover_commands
    discover_commands()
    result = dispatch([])
    assert result == 0


def test_dispatch_unknown_command():
    """dispatch('nonexistent') should return 1."""
    from cli.registry import dispatch, discover_commands
    discover_commands()
    result = dispatch(["nonexistent_command_xyz"])
    assert result == 1


def test_dispatch_with_timeout():
    """Verify timeout parameter is accepted."""
    from cli.registry import dispatch, discover_commands
    discover_commands()
    # timeout=0 means no timeout
    result = dispatch(["help"], timeout=0)
    assert result == 0


def test_handler_resolution():
    """Verify that registered commands resolve."""
    from cli.registry import _get_handler, discover_commands
    discover_commands()
    h = _get_handler("help")
    assert h is not None, "help handler should be registered"


def test_get_handler_nonexistent():
    from cli.registry import _get_handler
    assert _get_handler("__nonexistent__") is None


def test_registry_help_dispatch():
    """Test that 'help' command runs without error."""
    from cli.registry import dispatch, discover_commands
    discover_commands()
    result = dispatch(["help"])
    assert result == 0


def test_registry_version_dispatch():
    """Test that 'version' command runs without error."""
    from cli.registry import dispatch, discover_commands
    discover_commands()
    result = dispatch(["version"])
    assert result == 0
