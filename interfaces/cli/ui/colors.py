"""Terminal colors and styles for ETHAN CLI.

Minimal palette: Blue (primary), Cyan (info), Green (success),
Red (error), Purple (thinking), Dim (metadata).
"""

import os
import sys


def _supports_color() -> bool:
    """Check if terminal supports color."""
    if not sys.stdout.isatty():
        return False
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    return True


_HAS_COLOR = _supports_color()


class Colors:
    """ANSI color constants."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    BLUE = "\033[38;5;39m"
    CYAN = "\033[38;5;44m"
    GREEN = "\033[38;5;42m"
    YELLOW = "\033[38;5;220m"
    RED = "\033[38;5;196m"
    PURPLE = "\033[38;5;135m"
    WHITE = "\033[38;5;255m"


class Icons:
    """Icon set for terminal display."""
    CHECK = "✓"
    CROSS = "✗"
    WARN = "⚠"
    INFO = "ℹ"
    ARROW = "→"
    SECTION = "◆"
    INPUT = "▸"
    TIMER = "⏱"
    DOT = "●"
    CIRCLE = "○"


class style:
    """Style helpers for terminal output."""

    @staticmethod
    def section(title: str) -> str:
        if not _HAS_COLOR:
            return f"[{title}]"
        return f"{Colors.BLUE}{Icons.SECTION} {title}{Colors.RESET}"

    @staticmethod
    def success(msg: str) -> str:
        if not _HAS_COLOR:
            return f"[OK] {msg}"
        return f"  {Colors.GREEN}{Icons.CHECK} {msg}{Colors.RESET}"

    @staticmethod
    def error(title: str, context: str = "", suggestion: str = "") -> str:
        if not _HAS_COLOR:
            parts = [f"[!!] {title}"]
            if context:
                parts.append(f"  -> {context}")
            if suggestion:
                parts.append(f"  -> {suggestion}")
            return "\n".join(parts)
        parts = [f"  {Colors.RED}{Icons.CROSS} {title}{Colors.RESET}"]
        if context:
            parts.append(f"  {Colors.DIM}{Icons.ARROW} {context}{Colors.RESET}")
        if suggestion:
            parts.append(f"  {Colors.CYAN}{Icons.ARROW} {suggestion}{Colors.RESET}")
        return "\n".join(parts)

    @staticmethod
    def info(msg: str) -> str:
        if not _HAS_COLOR:
            return f"[i] {msg}"
        return f"  {Colors.CYAN}{Icons.INFO} {msg}{Colors.RESET}"

    @staticmethod
    def warning(msg: str) -> str:
        if not _HAS_COLOR:
            return f"[!!] {msg}"
        return f"  {Colors.YELLOW}{Icons.WARN} {msg}{Colors.RESET}"

    @staticmethod
    def thinking(msg: str) -> str:
        if not _HAS_COLOR:
            return f"  ... {msg}"
        return f"  {Colors.PURPLE}● {msg}{Colors.RESET}"

    @staticmethod
    def metadata(text: str) -> str:
        if not _HAS_COLOR:
            return f"  ({text})"
        return f"  {Colors.DIM}{Icons.TIMER} {text}{Colors.RESET}"

    @staticmethod
    def dim(text: str) -> str:
        if not _HAS_COLOR:
            return text
        return f"{Colors.DIM}{text}{Colors.RESET}"

    @staticmethod
    def bold(text: str) -> str:
        if not _HAS_COLOR:
            return text
        return f"{Colors.BOLD}{text}{Colors.RESET}"