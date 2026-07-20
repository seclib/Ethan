"""Result types — Contrat pour les résultats d'exécution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Error:
    """Erreur standardisée.

    Toute erreur du système suit ce format.
    Pas de stack traces dans les messages — uniquement dans les logs.
    """
    code: str = "UNKNOWN"
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    suggestion: str = ""  # Action suggérée à l'utilisateur


@dataclass
class Progress:
    """Progression d'une opération longue."""
    task_id: str = ""
    current: int = 0
    total: int = 100
    message: str = ""
    status: str = "running"  # "running", "completed", "failed"


@dataclass
class Result:
    """Résultat d'exécution standardisé.

    Encapsule le succès ou l'échec d'une opération.
    """
    success: bool = True
    data: Any = None
    error: Error | None = None
    duration_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(cls, data: Any = None, duration_ms: float = 0.0) -> "Result":
        return cls(success=True, data=data, duration_ms=duration_ms)

    @classmethod
    def fail(
        cls,
        code: str = "UNKNOWN",
        message: str = "",
        details: dict | None = None,
        suggestion: str = "",
        duration_ms: float = 0.0,
    ) -> "Result":
        return cls(
            success=False,
            error=Error(code=code, message=message, details=details or {}, suggestion=suggestion),
            duration_ms=duration_ms,
        )