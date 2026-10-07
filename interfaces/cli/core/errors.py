"""ETHAN CLI Error System — human-readable, actionable, no stack traces.

Usage:
    from core.errors import EthanError, format_error, error

    raise EthanError(
        "SYS-001", "API unreachable", "ethan daemon may be stopped", "try: ethan daemon start"
    )
    print(format_error(e))
    print(error("Something failed", "context here", "try: ethan --help"))
"""

import sys
import traceback
from interfaces.cli.core import colors as clr


class EthanError(Exception):
    """Structured ETHAN error with code, context, and suggestion."""

    def __init__(self, code: str, title: str, context: str = "", suggestion: str = ""):
        self.code = code
        self.title = title
        self.context = context
        self.suggestion = suggestion
        super().__init__(self.title)

    def __repr__(self):
        return f"EthanError({self.code}, {self.title})"


class CLIError(EthanError):
    """Contract-aware error carrying its machine code and its exit code.

    Bridges the historical `EthanError` (code/title/context/suggestion, kept
    for the self-healing/debug loop) and `docs/specs/CLI_CONTRACT.md` §4.3-§5:
    every CLI failure must be renderable as JSON on stderr AND map to exactly
    one frozen exit code.
    """

    def __init__(
        self,
        title: str,
        *,
        code: str = "",
        error_code: str = "",
        context: str = "",
        hint: str = "",
        exit_code: int = 1,
        status: int | None = None,
    ):
        super().__init__(code, title, context, hint or "")
        from interfaces.cli.core.exit_codes import (
            ErrorCode,
            ExitCode,
            error_code_for_exit,
        )

        self.hint = hint
        self.status = status
        self.exit_code = int(exit_code if exit_code else int(ExitCode.OPERATION_FAILED))
        # No explicit machine code → derive it from the exit code.
        self.error_code = error_code or error_code_for_exit(self.exit_code)
        if self.error_code not in {e.value for e in ErrorCode}:  # pragma: no cover
            self.error_code = ErrorCode.OPERATION_FAILED


def usage_error(title: str, hint: str = "", context: str = "") -> CLIError:
    """Invalid/missing/unknown option → exit 2, evaluated before any network."""
    from interfaces.cli.core.exit_codes import ErrorCode, ExitCode

    return CLIError(
        title,
        code="CLI-USAGE",
        error_code=ErrorCode.USAGE,
        context=context,
        hint=hint,
        exit_code=ExitCode.USAGE,
    )


def api_error(status: int, detail: str, hint: str = "") -> CLIError:
    """HTTP failure from the Core API → contract exit code (§5)."""
    from interfaces.cli.core.exit_codes import exit_code_for_status

    code_by_status = {
        401: "CLI-401",
        403: "CLI-403",
        404: "CLI-404",
        409: "CLI-409",
    }
    return CLIError(
        f"API {status}: {detail}",
        code=code_by_status.get(status, "CLI-API"),
        context="the Core API returned an error",
        hint=hint,
        exit_code=exit_code_for_status(status),
        status=status,
    )


def connection_error(detail: str, hint: str = "") -> CLIError:
    """Core API unreachable (connection refused, DNS, 502/503/504) → exit 5."""
    from interfaces.cli.core.exit_codes import ErrorCode, ExitCode

    return CLIError(
        f"Core API unreachable: {detail}",
        code="CLI-UNREACHABLE",
        error_code=ErrorCode.UNAVAILABLE,
        context=detail,
        hint=hint or "check that ETHAN is running: ethan status",
        exit_code=ExitCode.UNAVAILABLE,
    )


def timeout_error(seconds: float, hint: str = "") -> CLIError:
    """Client-side deadline exceeded → exit 7 (§5)."""
    from interfaces.cli.core.exit_codes import ErrorCode, ExitCode

    return CLIError(
        f"Timeout after {seconds:g}s",
        code="CLI-TIMEOUT",
        error_code=ErrorCode.TIMEOUT,
        context="the operation exceeded the client deadline",
        hint=hint or f"retry with a larger deadline: --timeout {int(seconds * 2) or 10}",
        exit_code=ExitCode.TIMEOUT,
    )


def format_cli_error(err: CLIError, *, as_json: bool = False) -> str:
    """Render a CLIError for stderr, human or JSON (contract §4.3)."""
    import json as _json

    if as_json:
        payload = {
            "error": {
                "code": err.error_code,
                "status": err.status,
                "message": err.title,
                "hint": err.hint,
            }
        }
        return _json.dumps(payload, ensure_ascii=False, sort_keys=True)

    parts = [f"✗ error: {err.title}"]
    if err.context:
        parts.append(f"  → {err.context}")
    if err.hint:
        parts.append(f"  → {err.hint}")
    return "\n".join(parts)


def format_error(err: EthanError | BaseException, debug: bool = False) -> str:
    """Render an error into a human-readable string.

    Args:
        err: Error to format
        debug: If True, include stack trace

    Returns:
        Formatted error string
    """
    if isinstance(err, EthanError):
        code_prefix = f"{clr.C.YELLOW}{err.code}{clr.C.RESET}: " if err.code else ""
        title = f"{clr.C.RED}{clr.I.CROSS} {code_prefix}{err.title}{clr.C.RESET}"

        parts = [title]
        if err.context:
            for line in err.context.split("\n"):
                parts.append(f"  {clr.C.DIM}{clr.I.ARROW} {line}{clr.C.RESET}")
        if err.suggestion:
            parts.append(f"  {clr.C.CYAN}{clr.I.ARROW} {err.suggestion}{clr.C.RESET}")

        if debug:
            parts.append("")
            parts.append(_format_traceback(sys.exc_info()[2]))

        return "\n".join(parts)

    # Generic exception
    title = f"{clr.C.RED}{clr.I.CROSS} {str(err)}{clr.C.RESET}"
    parts = [title]
    if debug:
        parts.append("")
        parts.append(_format_traceback(sys.exc_info()[2]))
    return "\n".join(parts)


def error(title: str, context: str = "", suggestion: str = "", code: str = "") -> str:
    """Quick error formatting without raising.

    Args:
        title: Error title
        context: Optional context (dim)
        suggestion: Optional actionable suggestion (cyan)
        code: Optional error code (yellow)

    Returns:
        Formatted error string
    """
    code_prefix = f"{clr.C.YELLOW}{code}{clr.C.RESET}: " if code else ""
    title_str = f"{clr.C.RED}{clr.I.CROSS} {code_prefix}{title}{clr.C.RESET}"

    parts = [title_str]
    if context:
        for line in context.split("\n"):
            parts.append(f"  {clr.C.DIM}{clr.I.ARROW} {line}{clr.C.RESET}")
    if suggestion:
        parts.append(f"  {clr.C.CYAN}{clr.I.ARROW} {suggestion}{clr.C.RESET}")

    return "\n".join(parts)


def _format_traceback(tb) -> str:
    """Format traceback, truncate to last 3 frames, sanitize paths."""
    lines = traceback.format_tb(tb)
    # Keep last 3 frames
    if len(lines) > 3:
        lines = ["  ... (truncated)\n"] + lines[-3:]
    # Sanitize paths (replace home dir with ~)
    home = sys.path[0] if sys.path else ""
    if home:
        lines = [line.replace(home, "~") for line in lines]
    return "".join(lines).rstrip()


# ── Common error constructors ──────────────────────────


def api_unreachable() -> EthanError:
    return EthanError(
        "SYS-001",
        "API unreachable",
        "ethan daemon may be stopped",
        "try: ethan daemon start",
    )


def capability_not_found(name: str) -> EthanError:
    return EthanError(
        "CAP-001",
        f"Capability not found: {name}",
        "the requested capability is not installed",
        "try: ethan plugin list",
    )


def execution_failed(cmd: str, exit_code: int = 1) -> EthanError:
    return EthanError(
        "CAP-002",
        f"Command failed: {cmd}",
        f"exit code {exit_code}",
        "try: ethan logs --follow",
    )


def timeout(seconds: int = 10) -> EthanError:
    return EthanError(
        "SYS-002",
        f"Timeout: request exceeded {seconds}s",
        "the operation took too long",
        f"try: ethan run --timeout {seconds * 2}",
    )


def permission_denied(reason: str, run_as: str = "") -> EthanError:
    return EthanError(
        "SYS-003",
        "Permission denied",
        reason,
        f"run as: {run_as}" if run_as else "check your permissions",
    )


def unknown_command(cmd: str, suggestion: str = "") -> EthanError:
    msg = f"Did you mean? {suggestion}" if suggestion else "try: ethan --help"
    return EthanError(
        "CMD-001",
        f"Unknown command: '{cmd}'",
        "",
        msg,
    )


def missing_argument(arg: str, usage: str, example: str) -> EthanError:
    return EthanError(
        "CMD-002",
        f"Missing argument: <{arg}>",
        "",
        f"Usage: {usage}",
    )


def invalid_session(session_id: str) -> EthanError:
    return EthanError(
        "INP-002",
        "Invalid session",
        f"session: {session_id[:8]}...",
        "try: ethan chat --resume",
    )


def file_not_found(path: str) -> EthanError:
    return EthanError(
        "INP-003",
        "File not found",
        f"path: {path}",
        "check the path and try again",
    )


def empty_input() -> EthanError:
    return EthanError(
        "INP-001",
        "Empty input",
        "",
        "type a command or message",
    )
