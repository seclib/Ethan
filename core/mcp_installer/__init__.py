"""ETHAN MCP Installer — acquisition, analyse et installation contrôlée de serveurs MCP externes.

Ce package est un **complément** du MCP Manager Core (`core/tools/servers.py`).
Il ne remplace pas le registre canonique : il prépare et installe des serveurs
MCP externes, puis les enregistre via `ToolServerManager`.

Aucune logique métier n'est dupliquée. L'installer réutilise :
- `ToolServerManager` pour l'enregistrement et le lifecycle MCP.
- `validate_server_config` pour la validation de la config serveur.
- `ApprovalEngine` / `HumanRoot` pour l'autorisation HROT.
- `SecureToolEnforcer` pour la politique fail-closed.
- `AuditStore` pour la traçabilité.
"""

from __future__ import annotations

from core.mcp_installer.installer import build_mcp_config, generate_installation_plan
from core.mcp_installer.plan import (
    InstallationPlan,
    ProjectAnalysis,
    RuntimeType,
    SourceType,
    TransportType,
)
from core.mcp_installer.project_analyzer import analyze_source
from core.mcp_installer.service import (
    CommandResult,
    InstallationState,
    McpInstaller,
    McpInstallError,
)
from core.mcp_installer.source_acquirer import detect_runtime, detect_source_type

__all__ = [
    "CommandResult",
    "InstallationPlan",
    "InstallationState",
    "McpInstallError",
    "McpInstaller",
    "ProjectAnalysis",
    "RuntimeType",
    "SourceType",
    "TransportType",
    "analyze_source",
    "build_mcp_config",
    "detect_runtime",
    "detect_source_type",
    "generate_installation_plan",
]
