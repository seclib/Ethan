"""ETHAN CLI Error System — human-readable, actionable, no stack traces.

Usage:
    from core.errors import EthanError, format_error, error

    raise EthanError("SYS-001", "API unreachable", "ethan daemon may be stopped", "try: ethan daemon start")
    print(format_error(e))
    print(error("Something failed", "context here", "try: ethan --help"))
"""

import sys
import traceback
from cli.core import colors as clr


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
        f"try: ethan plugin list",
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