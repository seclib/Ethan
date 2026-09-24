"""Data Protection & Anti-Exfiltration (Phase 06).

Point d'entrée pour la protection des données locales et la prévention
d'exfiltration vers des destinations externes.

- ``SensitiveDataClassifier`` : détecte / masque les données sensibles.
- ``ExfilGuard`` : garde obligatoire de toute transmission externe.
- ``DataFlow`` / ``TransmitResult`` / ``TransmissionPolicy`` : modèle.
"""

from __future__ import annotations

from core.security.data.exfiltration import (
    DataFlow,
    ExfilBlockedError,
    ExfilConfirmationRequiredError,
    ExfilError,
    ExfilGuard,
    TransmissionDecision,
    TransmissionPolicy,
    TransmitResult,
)
from core.security.data.sensitive import (
    SensitiveDataClassifier,
    SensitiveKind,
    SensitiveScan,
)

__all__ = [
    "DataFlow",
    "ExfilBlockedError",
    "ExfilConfirmationRequiredError",
    "ExfilError",
    "ExfilGuard",
    "SensitiveDataClassifier",
    "SensitiveKind",
    "SensitiveScan",
    "TransmissionDecision",
    "TransmissionPolicy",
    "TransmitResult",
]
