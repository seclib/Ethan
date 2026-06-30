"""Types du module budget — scopes, statuts, alertes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4


class BudgetScope(StrEnum):
    """Scope budgétaire disponible."""

    GLOBAL = "global"
    PROJECT = "project"
    RUN = "run"
    SESSION = "session"


class BudgetStatus(StrEnum):
    """Statut budgétaire d'un scope."""

    OK = "ok"
    WARNING = "warning"
    HARD_STOP = "hard_stop"
    UNLIMITED = "unlimited"
    DISABLED = "disabled"


@dataclass(frozen=True)
class BudgetAlert:
    """Alerte budgétaire émise quand un seuil est atteint."""

    id: str = field(default_factory=lambda: f"bgt_{uuid4().hex[:10]}")
    timestamp: datetime = field(default_factory=datetime.utcnow)
    scope: BudgetScope = BudgetScope.GLOBAL
    scope_id: str = ""
    status: BudgetStatus = BudgetStatus.OK
    ratio: float = 0.0
    spent_usd: float = 0.0
    limit_usd: float = 0.0
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "scope": self.scope.value,
            "scope_id": self.scope_id,
            "status": self.status.value,
            "ratio": round(self.ratio, 4),
            "spent_usd": round(self.spent_usd, 6),
            "limit_usd": round(self.limit_usd, 6),
            "message": self.message,
        }


@dataclass
class BudgetConfig:
    """Configuration budgétaire globale."""

    enabled: bool = True
    monthly_limit_usd: float = 50.0
    project_limit_usd: float = 5.0
    run_limit_usd: float = 1.0
    warn_ratio: float = 0.8
    alert_on_warning: bool = True
    alert_on_hard_stop: bool = True