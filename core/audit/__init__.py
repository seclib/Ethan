"""ETHAN Core — Audit Module

Journal d'audit immuable pour tracer toutes les décisions système.
Append-only : aucune entrée n'est jamais modifiée ou supprimée.
"""

from .store import AuditStore
from .types import AuditEntry, AuditDecision, AuditCategory

__version__ = "1.0.0"
__all__ = ["AuditStore", "AuditEntry", "AuditDecision", "AuditCategory"]