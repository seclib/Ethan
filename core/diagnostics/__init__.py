"""ETHAN Core — Diagnostics système.

Capacité Core-owned : vérifie l'état réel des composants d'ETHAN
(infrastructure, providers, intelligence) et collecte les métriques système.

Consommée par :
  - l'API   : GET /diagnostics, GET /diagnostics/metrics
  - le CLI  : ethan doctor
  - le WebUI : pages /diagnostics et /monitoring (pur affichage)

Aucune donnée fictive : si un composant est injoignable, le rapport le dit ;
si une métrique est indisponible (pas de GPU, pas de NVML), elle est
déclarée indisponible avec la raison — jamais inventée.
"""

from .metrics import SystemMetrics
from .system import (
    CheckResult,
    Status,
    SystemDiagnostics,
)

__all__ = ["CheckResult", "Status", "SystemDiagnostics", "SystemMetrics"]
