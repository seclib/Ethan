"""Types du terminal ETHAN — le vocabulaire de session, partagé Core/API/WebUI.

Ce module ne contient AUCUNE logique : uniquement les types, les états et le
vocabulaire d'erreur. Le terminal est une capacité du Core — la WebUI le
révèle, elle ne le possède pas (AGENTS.md, Première Loi).
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


class TerminalState:
    """États d'une session terminal.

    Vocabulaire du Core, jamais traduit par les interfaces (§ CLI_CONTRACT §4.1).
    """

    RUNNING = "RUNNING"
    EXITED = "EXITED"
    CLOSED = "CLOSED"
    ERROR = "ERROR"

    ALL = frozenset({RUNNING, EXITED, CLOSED, ERROR})
    ACTIVE = frozenset({RUNNING})


class TerminalError(Exception):
    """Erreur du service terminal (refus de sécurité ou état invalide)."""

    #: Code stable, consumé par l'API et l'interface (aucun message libre).
    code = "TERMINAL-ERR"

    def __init__(self, message: str, *, reason: str = "", code: str | None = None):
        super().__init__(message)
        self.reason = reason
        if code:
            self.code = code


class TerminalSecurityError(TerminalError):
    """Refus fail-closed : root, cwd hors périmètre, commande interdite."""

    code = "TERMINAL-SEC"


class TerminalNotFound(TerminalError):
    """Session inconnue (jamais créée ou déjà purgée)."""

    code = "TERMINAL-NOTFOUND"


def _now() -> float:
    return time.time()


@dataclass
class TerminalSession:
    """Une session terminal — état réel, jamais simulé côté interface.

    `pid` est le processus enfant forké dans son propre groupe : c'est ce qui
    rend le Ctrl+C et la terminaison de groupe possibles sans toucher au
    serveur.
    """

    id: str
    user: str
    cwd: str
    pid: int
    state: str = TerminalState.RUNNING
    exit_code: int | None = None
    created_at: float = field(default_factory=_now)
    last_activity: float = field(default_factory=_now)
    cols: int = 80
    rows: int = 24
    hostname: str = ""
    #: Permission ETHAN requise pour piloter cette session.
    permission: str = "execute"
    #: `FD` du maître PTY (côté serveur), absent après fermeture.
    fd: int | None = field(default=None, repr=False)

    def touch(self) -> None:
        self.last_activity = _now()

    def to_dict(self) -> dict[str, Any]:
        """Vue destinée aux interfaces — jamais de descripteur ni de secret."""
        return {
            "id": self.id,
            "user": self.user,
            "cwd": self.cwd,
            "state": self.state,
            "pid": self.pid,
            "exit_code": self.exit_code,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "cols": self.cols,
            "rows": self.rows,
            "hostname": self.hostname,
            "permission": self.permission,
        }


def new_session_id() -> str:
    """Identifiant opaque, non séquentiel et non devinable."""
    return "term_" + uuid.uuid4().hex[:16]


__all__ = [
    "TerminalError",
    "TerminalNotFound",
    "TerminalSecurityError",
    "TerminalSession",
    "TerminalState",
    "new_session_id",
]
