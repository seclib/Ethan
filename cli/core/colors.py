"""ETHAN CLI Visual Identity — color system, icons, and formatters.

Usage:
    from core.colors import C, I, section, success, error, metadata, prompt

    print(section("Result"))
    print(success("System online"))
    print(error("Timeout", "host: localhost:4222", "try ethan daemon start"))
    print(metadata("1.2s"))
    print(prompt("idle"), end="")
"""

import sys

# ── Color Constants ────────────────────────────────────

class C:
    """ANSI color codes (16-color terminal safe)."""
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    BLUE    = "\033[38;5;39m"
    CYAN    = "\033[38;5;44m"
    GREEN   = "\033[38;5;42m"
    YELLOW  = "\033[38;5;220m"
    RED     = "\033[38;5;196m"
    PURPLE  = "\033[38;5;135m"
    WHITE   = "\033[38;5;255m"


# ── Icon Constants ─────────────────────────────────────

class I:
    """Unicode icons for CLI output."""
    CHECK   = "\u2713"    # ✓
    CROSS   = "\u2717"    # ✗
    WARN    = "\u26a0"    # ⚠
    INFO    = "\u2139"    # ℹ
    ARROW   = "\u2192"    # →
    WRAP    = "\u21b3"    # ↳
    SECTION = "\u25c6"    # ◆
    SPINNER = ["\u25d0", "\u25d3", "\u25d1", "\u25d2"]  # ◐◓◑◒
    TIMER   = "\u23f1"    # ⏱
    DOT     = "\u25cf"    # ●
    CIRCL   = "\u25cb"    # ○
    INPUT   = "\u25b8"    # ▸


# ── Formatter Functions ────────────────────────────────

def section(title: str, subtitle: str = "") -> str:
    """Blue section header with optional subtitle."""
    parts = [f"{C.BLUE}{I.SECTION} {title}{C.RESET}"]
    if subtitle:
        parts.append(f"{C.DIM}{subtitle}{C.RESET}")
    return "  ".join(parts)


def success(msg: str) -> str:
    """Green success message."""
    return f"  {C.GREEN}{I.CHECK} {msg}{C.RESET}"


def error(title: str, context: str | None = None, suggestion: str | None = None) -> str:
    """Red error block with optional context and suggestion."""
    lines = [f"  {C.RED}{I.CROSS} {title}{C.RESET}"]
    if context:
        lines.append(f"    {C.DIM}{I.ARROW} {context}{C.RESET}")
    if suggestion:
        lines.append(f"    {C.CYAN}{I.ARROW} {suggestion}{C.RESET}")
    return "\n".join(lines)


def warn(msg: str) -> str:
    """Yellow warning."""
    return f"  {C.YELLOW}{I.WARN} {msg}{C.RESET}"


def warning(msg: str) -> str:
    """Alias for warn()."""
    return warn(msg)


def info(msg: str) -> str:
    """Cyan info message."""
    return f"  {C.CYAN}{I.INFO} {msg}{C.RESET}"


def item(text: str) -> str:
    """Cyan list item."""
    return f"    {C.CYAN}{I.ARROW} {text}{C.RESET}"


def wrap(text: str) -> str:
    """Dim line continuation."""
    return f"  {C.DIM}{I.WRAP} {text}{C.RESET}"


def metadata(text: str) -> str:
    """Dim metadata line (timing, counts)."""
    return f"  {C.DIM}{I.TIMER} {text}{C.RESET}"


def online(text: str = "ONLINE") -> str:
    """Green online indicator."""
    return f"  {C.GREEN}{I.DOT} {text}{C.RESET}"


def offline(text: str = "OFFLINE") -> str:
    """Dim offline indicator."""
    return f"  {C.DIM}{I.CIRCL} {text}{C.RESET}"


def prompt(state: str = "idle") -> str:
    """Interactive prompt line with state badge."""
    badge_colors = {
        "idle": C.GREEN,
        "working": C.CYAN,
        "error": C.RED,
        "thinking": C.PURPLE,
        "auto": C.CYAN,
        "chat": C.CYAN,
    }
    badge_color = badge_colors.get(state, C.CYAN)
    return (
        f"{C.BLUE}{I.SECTION}{C.RESET}"
        f"  {C.BOLD}ethan{C.RESET}"
        f"  {badge_color}{I.ARROW}{C.RESET}"
        f" {badge_color}{state}{C.RESET}"
        f"  {C.BLUE}{I.INPUT}{C.RESET} "
    )


def spinner(phase: int = 0) -> str:
    """Spinner character for the given animation phase."""
    return I.SPINNER[phase % len(I.SPINNER)]


def progress_bar(current: int, total: int, width: int = 8) -> str:
    """ASCII progress bar."""
    filled = int(width * current / total) if total > 0 else 0
    bar = "█" * filled + "░" * (width - filled)
    pct = int(100 * current / total) if total > 0 else 0
    return f"  [{C.CYAN}{bar}{C.RESET}] {C.BOLD}{pct}%{C.RESET} ({current}/{total})"


# ── Convenience ────────────────────────────────────────

def print_section(title: str) -> None:
    """Print a section header."""
    print()
    print(section(title))


def print_error(title: str, context: str | None = None, suggestion: str | None = None) -> None:
    """Print an error block."""
    print()
    print(error(title, context, suggestion))


# ── Extended Output Formatting (OUTPUT_FORMATTING.md) ──

def subheader(text: str) -> str:
    """Bold sub-header."""
    return f"{C.BOLD}{text}{C.RESET}"


DIVIDER = f"{C.DIM}{'─' * 40}{C.RESET}"


def divider() -> str:
    """Return a horizontal divider."""
    return DIVIDER


def inline_code(text: str) -> str:
    """Cyan inline code."""
    return f"{C.CYAN}`{text}`{C.RESET}"


def code_block(language: str, code: str) -> str:
    """Fenced code block with dim border."""
    lines = code.strip().split("\n")
    pad = max(0, 40 - len(language))
    header = f"{C.DIM}┌─ {language} {'─' * pad}┐{C.RESET}"
    footer = f"{C.DIM}└{'─' * 40}┘{C.RESET}"
    body = "\n".join(f"    {C.WHITE}{line}{C.RESET}" for line in lines)
    return f"{header}\n{body}\n{footer}"


def output_lines(lines: list[str]) -> str:
    """Dim multi-line output."""
    return "\n".join(f"  {C.DIM}{line}{C.RESET}" for line in lines)


def table(headers: list[str], rows: list[list[str]], status_col: int = -1) -> str:
    """Terminal-safe table."""
    col_widths = [
        max(len(str(h)), max((len(str(r[i])) for r in rows), default=0))
        for i, h in enumerate(headers)
    ]
    out = [f"  {'  '.join(h.ljust(w) for h, w in zip(headers, col_widths))}"]
    out.append(f"  {'  '.join('─' * w for w in col_widths)}")
    for row in rows:
        cells = []
        for i, cell in enumerate(row):
            cell = str(cell)
            cells.append(cell.ljust(col_widths[i]))
        out.append(f"  {'  '.join(cells)}")
    return "\n".join(out)


def numbered_list(items: list[str], start: int = 1) -> str:
    """Numbered list."""
    width = len(str(len(items) + start))
    return "\n".join(
        f"  {str(i).rjust(width)}.  {item}" for i, item in enumerate(items, start=start)
    )


def definition_list(pairs: dict[str, str]) -> str:
    """Key: value definition list."""
    max_key = max(len(k) for k in pairs) if pairs else 0
    return "\n".join(
        f"  {k.ljust(max_key)}:  {v}" for k, v in pairs.items()
    )


def timing(duration: float, timestamp: str = "") -> str:
    """Timing footer."""
    parts = [f"{C.DIM}{I.TIMER} {duration:.1f}s{C.RESET}"]
    if timestamp:
        parts.append(f"{C.DIM}@ {timestamp}{C.RESET}")
    return f"  {'  '.join(parts)}"


def counters(**kwargs: int) -> str:
    """Counter footer."""
    parts = [f"{v} {k}" for k, v in kwargs.items()]
    return f"  {C.DIM}{'  |  '.join(parts)}{C.RESET}"


def progress(current: int, total: int, width: int = 12, label: str = "") -> str:
    """Progress bar."""
    filled = int(width * current / total) if total > 0 else 0
    bar = "█" * filled + "░" * (width - filled)
    pct = int(100 * current / total) if total > 0 else 0
    suffix = f"  {pct}%"
    if label:
        suffix += f"  ({label})"
    return f"  [{C.CYAN}{bar}{C.RESET}]{suffix}"