"""Safety — Ethan OS

Aucune action ne peut être exécutée sans :
- validation du système
- contexte clair
- traçabilité
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SafetyContext:
    """Contexte de sécurité pour une exécution."""
    validated: bool = False
    user_id: str = ""
    session_id: str = ""
    trace_id: str = ""
    permissions: List[str] = field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW


class SafetyViolation(Exception):
    """Levée quand une action n'est pas validée."""
    pass


class SafetyValidator:
    """Valide les actions avant exécution."""

    def validate(self, context: SafetyContext) -> bool:
        if not context.user_id:
            return False
        if not context.session_id:
            return False
        if not context.trace_id:
            return False
        context.validated = True
        return True