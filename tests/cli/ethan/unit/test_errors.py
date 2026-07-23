"""Tests for cli/core/errors.py — error system."""
from __future__ import annotations

import pytest


class TestEthanError:
    """EthanError class tests."""

    def test_constructor(self) -> None:
        from cli.core.errors import EthanError
        err = EthanError("SYS-001", "Title", "Context", "Suggestion")
        assert err.code == "SYS-001"
        assert err.title == "Title"
        assert err.context == "Context"
        assert err.suggestion == "Suggestion"

    def test_repr(self) -> None:
        from cli.core.errors import EthanError
        err = EthanError("SYS-001", "Title")
        assert repr(err) == "EthanError(SYS-001, Title)"

    def test_is_exception(self) -> None:
        from cli.core.errors import EthanError
        err = EthanError("E-001", "Test")
        assert isinstance(err, Exception)


class TestFormatError:
    """format_error() tests."""

    def test_format_ethan_error(self) -> None:
        from cli.core.errors import EthanError, format_error
        err = EthanError("SYS-001", "Something failed", "context here", "try again")
        result = format_error(err)
        assert "SYS-001" in result
        assert "Something failed" in result
        assert "context here" in result
        assert "try again" in result

    def test_format_ethan_error_no_code(self) -> None:
        from cli.core.errors import EthanError, format_error
        err = EthanError("", "Something failed")
        result = format_error(err)
        assert "Something failed" in result

    def test_format_generic_exception(self) -> None:
        from cli.core.errors import format_error
        result = format_error(RuntimeError("generic error"))
        assert "generic error" in result

    def test_format_ethan_error_no_context(self) -> None:
        from cli.core.errors import EthanError, format_error
        err = EthanError("E-001", "Title", "", "")
        result = format_error(err)
        assert "Title" in result
        assert "E-001" in result


class TestErrorFunction:
    """error() quick formatting tests."""

    def test_error_basic(self) -> None:
        from cli.core.errors import error
        result = error("Failed")
        assert "Failed" in result

    def test_error_with_context(self) -> None:
        from cli.core.errors import error
        result = error("Failed", "context", "try again", "E-001")
        assert "Failed" in result
        assert "context" in result
        assert "try again" in result
        assert "E-001" in result

    def test_error_with_code(self) -> None:
        from cli.core.errors import error
        result = error("Failed", code="E-001")
        assert "E-001" in result


class TestErrorConstructors:
    """Common error constructor tests."""

    def test_api_unreachable(self) -> None:
        from cli.core.errors import api_unreachable, EthanError
        err = api_unreachable()
        assert isinstance(err, EthanError)
        assert err.code == "SYS-001"
        assert err.title == "API unreachable"

    def test_capability_not_found(self) -> None:
        from cli.core.errors import capability_not_found
        err = capability_not_found("test_cap")
        assert err.code == "CAP-001"
        assert "test_cap" in err.title

    def test_execution_failed(self) -> None:
        from cli.core.errors import execution_failed
        err = execution_failed("build", 1)
        assert err.code == "CAP-002"
        assert "build" in err.title

    def test_timeout(self) -> None:
        from cli.core.errors import timeout
        err = timeout(10)
        assert err.code == "SYS-002"
        assert "10" in err.title

    def test_permission_denied(self) -> None:
        from cli.core.errors import permission_denied
        err = permission_denied("no write access", "root")
        assert err.code == "SYS-003"
        assert "no write access" in err.context
        assert "root" in err.suggestion

    def test_unknown_command(self) -> None:
        from cli.core.errors import unknown_command
        err = unknown_command("chatt", "chat")
        assert err.code == "CMD-001"
        assert "chatt" in err.title

    def test_missing_argument(self) -> None:
        from cli.core.errors import missing_argument
        err = missing_argument("cmd", "ethan run <cmd>", "ethan run build")
        assert err.code == "CMD-002"
        assert "cmd" in err.title

    def test_invalid_session(self) -> None:
        from cli.core.errors import invalid_session
        err = invalid_session("abc-123")
        assert err.code == "INP-002"
        assert "session" in err.context.lower()

    def test_file_not_found(self) -> None:
        from cli.core.errors import file_not_found
        err = file_not_found("/path/to/file")
        assert err.code == "INP-003"
        assert "/path/to/file" in err.context

    def test_empty_input(self) -> None:
        from cli.core.errors import empty_input
        err = empty_input()
        assert err.code == "INP-001"
        assert "Empty input" in err.title