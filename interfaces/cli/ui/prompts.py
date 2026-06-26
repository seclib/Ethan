"""Prompt rendering for ETHAN CLI.

Format: ◆ ethan ◇ chat ▸
"""

from typing import Optional
from ethan.ui.colors import Colors, Icons


def get_prompt(session_id: Optional[str] = None) -> str:
    """Build the prompt string for the current state."""
    mode = "chat"
    if session_id:
        mode = f"chat · {session_id[:8]}"

    return (
        f"{Colors.BLUE}{Icons.SECTION}{Colors.RESET}  "
        f"{Colors.BOLD}ethan{Colors.RESET}  "
        f"{Colors.CYAN}{mode}{Colors.RESET}  "
        f"{Colors.BLUE}{Icons.INPUT}{Colors.RESET} "
    )


def get_welcome(session_id: Optional[str] = None) -> str:
    """Build welcome banner."""
    sid = session_id[:8] if session_id else ""
    sid_part = f" ◇  session {sid}" if sid else ""
    return (
        f"\n{Colors.BLUE}{Icons.SECTION}{Colors.RESET}  "
        f"{Colors.BOLD}ETHAN Chat{Colors.RESET}"
        f"{Colors.CYAN}{sid_part}{Colors.RESET}\n\n"
        f"  Ctrl+D or /exit to quit  •  /help for commands\n"
    )