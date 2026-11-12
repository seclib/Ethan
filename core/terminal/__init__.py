"""Terminal ETHAN — capacité Core : sessions PTY réelles.

Source de vérité du cycle de vie du terminal. L'API n'est qu'une passerelle
(mince) et la WebUI un rendu (AGENTS.md, Première Loi).

    core/terminal/types.py    vocabulaire (états, session, erreurs)
    core/terminal/service.py  TerminalService (forkpty, I/O, signaux, purge)
"""

from core.terminal.service import (
    DEFAULT_ROOT,
    READ_SIZE,
    TerminalService,
    assert_not_root,
    build_clean_env,
    current_user,
    default_shell,
    hostname,
    resolve_cwd,
)
from core.terminal.types import (
    TerminalError,
    TerminalNotFound,
    TerminalSecurityError,
    TerminalSession,
    TerminalState,
    new_session_id,
)

__all__ = [
    "DEFAULT_ROOT",
    "READ_SIZE",
    "TerminalError",
    "TerminalNotFound",
    "TerminalSecurityError",
    "TerminalService",
    "TerminalSession",
    "TerminalState",
    "assert_not_root",
    "build_clean_env",
    "current_user",
    "default_shell",
    "hostname",
    "new_session_id",
    "resolve_cwd",
]
