"""Génération de plan d'installation MCP — combine analyse et source.

Le plan est une projection **sans effet de bord** : rien n'est installé ni
exécuté ici. L'installation réelle est du ressort de ``McpInstaller`` après
approbation HROT.
"""

from __future__ import annotations

import re
import shlex
import shutil
from typing import Any

from core.mcp_installer.plan import (
    InstallationPlan,
    ProjectAnalysis,
    SourceType,
    TransportType,
)
from core.mcp_installer.project_analyzer import analyze_source
from core.mcp_installer.source_acquirer import parse_npx_command


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-")
    return cleaned or "mcp-server"


def slugify(value: str) -> str:
    """Identifiant stable et sûr pour un répertoire d'installation."""
    return _slug(value)


def _absolute_executable(name: str) -> str:
    """Résout un exécutable en chemin absolu, ou retourne le nom brut.

    La politique stdio du Core exige un chemin absolu : le plan le fournit
    lorsqu'il est résolvable afin d'éviter une installation qui échouerait
    seulement à l'enregistrement.
    """
    if not name:
        return ""
    resolved = shutil.which(name)
    return resolved or name


def _pinned_npm_spec(analysis: ProjectAnalysis, fallback: str) -> str:
    name = analysis.name or fallback
    if analysis.version and "@" not in name.rsplit("/", 1)[-1]:
        return f"{name}@{analysis.version}"
    return name


def make_stdio_config(name: str, command: str, args: list[str]) -> dict[str, Any]:
    """Config attendue par ``ToolServerManager.register`` (transport stdio)."""
    return {
        "name": _slug(name),
        "url": f"stdio://{_slug(name)}",
        "transport": "stdio",
        "metadata": {
            "transport": "stdio",
            "command": command,
            "args": list(args),
        },
    }


def make_http_config(name: str, url: str) -> dict[str, Any]:
    return {
        "name": _slug(name),
        "url": url,
        "transport": "http",
        "metadata": {"transport": "http"},
    }


def generate_installation_plan(source: str) -> InstallationPlan:
    """Analyse une source et génère un plan d'installation (aucune mutation)."""
    analysis = analyze_source(source)
    plan = InstallationPlan(
        source=source,
        name=analysis.name or source,
        source_type=analysis.source_type,
        resolved_version=analysis.version,
        runtime=analysis.runtime,
        package_manager=analysis.package_manager,
        dependencies=list(analysis.dependencies),
        analysis=analysis,
    )
    plan.transport = analysis.transport

    if analysis.source_type == SourceType.NPM_COMMAND:
        package, extra_args = parse_npx_command(source)
        spec = _pinned_npm_spec(analysis, package)
        plan.execution_command = _absolute_executable("npx")
        plan.execution_args = ["-y", spec, *extra_args]
        plan.transport = TransportType.STDIO if analysis.is_mcp_server else TransportType.UNKNOWN
    elif analysis.source_type == SourceType.NPM_PACKAGE:
        spec = _pinned_npm_spec(analysis, analysis.name or source)
        plan.execution_command = _absolute_executable("npx")
        plan.execution_args = ["-y", spec]
        plan.transport = TransportType.STDIO if analysis.is_mcp_server else TransportType.UNKNOWN
    elif analysis.source_type == SourceType.CUSTOM_COMMAND:
        try:
            parts = shlex.split(source)
        except ValueError:
            parts = source.split()
        plan.execution_command = _absolute_executable(parts[0]) if parts else ""
        plan.execution_args = parts[1:] if len(parts) > 1 else []
        plan.transport = TransportType.STDIO
    elif analysis.source_type == SourceType.REMOTE_HTTP:
        plan.execution_command = ""
        plan.execution_args = []
        plan.transport = TransportType.HTTP
    elif analysis.source_type == SourceType.GITHUB:
        # La commande dépend du clone et du manifeste : résolue à l'installation.
        plan.execution_command = ""
        plan.execution_args = []

    plan.install_actions = _build_install_actions(plan, analysis)
    plan.required_permissions = _build_required_permissions(plan, analysis)
    plan.expected_mcp_config = build_mcp_config(plan)
    return plan


def _build_install_actions(plan: InstallationPlan, analysis: ProjectAnalysis) -> list[str]:
    actions: list[str] = []
    if analysis.source_type in (SourceType.NPM_COMMAND, SourceType.NPM_PACKAGE):
        actions.append("Vérifier Node.js et npm sur le PATH")
        actions.append("Créer un répertoire d'isolation dédié et un manifeste de version")
        spec = plan.execution_args[1] if len(plan.execution_args) > 1 else analysis.name
        actions.append(f"Installer le package épinglé dans l'isolation : npm install {spec}")
        actions.append("Résoudre le binaire du serveur et l'exécuter via node")
        actions.append(
            "Autoriser explicitement le chemin absolu de node dans "
            "ETHAN_MCP_STDIO_ALLOWLIST (politique Core fail-closed)"
        )
    elif analysis.source_type == SourceType.GITHUB:
        actions.append("Cloner le dépôt dans le répertoire d'isolation dédié")
        actions.append("Lire les manifestes pour détecter le gestionnaire de packages")
        if analysis.package_manager == "npm":
            actions.append("Installer les dépendances npm avec --ignore-scripts")
            actions.append("Déterminer le point d'entrée Node (bin/main)")
        elif analysis.package_manager == "pip":
            actions.append("Créer un virtualenv isolé puis installer le projet Python")
            actions.append("Déterminer le point d'entrée Python (project.scripts)")
        else:
            actions.append("Aucun gestionnaire de packages reconnu — installation manuelle requise")
        actions.append("Enregistrer le serveur puis synchroniser ses outils")
    elif analysis.source_type == SourceType.REMOTE_HTTP:
        actions.append("Valider l'URL avec la politique d'egress du Core")
        actions.append("Tester la connexion MCP et synchroniser les outils")
    elif analysis.source_type == SourceType.CUSTOM_COMMAND:
        actions.append("Vérifier que la commande est un chemin absolu autorisé")
        actions.append(
            "Ajouter le chemin absolu à ETHAN_MCP_STDIO_ALLOWLIST "
            "(politique Core fail-closed)"
        )
        actions.append("Tester la commande puis synchroniser les outils")

    if analysis.dependencies:
        actions.append(f"Dépendances déclarées : {len(analysis.dependencies)}")
    if analysis.env_vars:
        actions.append(f"Configurer {len(analysis.env_vars)} variable(s) d'environnement")
    if analysis.errors:
        actions.append("Analyse incomplète : consulter les erreurs avant d'approuver")
    return actions


def _build_required_permissions(
    plan: InstallationPlan, analysis: ProjectAnalysis
) -> list[str]:
    perms = [
        "Permission.ADMIN (enregistrement du serveur)",
        "Approbation humaine HROT (catégorie plugin_install)",
    ]
    if analysis.source_type in (SourceType.NPM_COMMAND, SourceType.NPM_PACKAGE):
        perms.append("Exécution npx (stdio) via allowlist Core")
    if analysis.source_type == SourceType.GITHUB:
        perms.append("Accès réseau GitHub (clone) et installation de dépendances")
    if analysis.source_type == SourceType.CUSTOM_COMMAND:
        perms.append("Exécution de la commande fournie (stdio) via allowlist Core")
    if plan.transport in (TransportType.HTTP, TransportType.STREAMABLE_HTTP):
        perms.append("Permission.EXECUTE (synchronisation MCP)")
    return perms


def build_mcp_config(plan: InstallationPlan, *, assume_mcp: bool = False) -> dict[str, Any]:
    """Config MCP attendue pour ``ToolServerManager.register()``.

    ``assume_mcp`` n'est jamais activé par l'analyse seule : il traduit une
    confirmation humaine explicite quand l'identité du package n'a pas pu être
    vérifiée (npm indisponible). Le Core revalide ensuite toute la config.
    """
    analysis = plan.analysis
    source_type = analysis.source_type if analysis else plan.source_type
    is_mcp = bool(analysis.is_mcp_server) if analysis else False
    if source_type in (SourceType.NPM_COMMAND, SourceType.NPM_PACKAGE):
        if not is_mcp and not assume_mcp:
            return {}
        return make_stdio_config(plan.name, plan.execution_command, plan.execution_args)
    if source_type == SourceType.CUSTOM_COMMAND:
        return make_stdio_config(plan.name, plan.execution_command, plan.execution_args)
    if source_type == SourceType.REMOTE_HTTP:
        return make_http_config(plan.name, plan.source)
    return {}


def npm_package_spec(plan: InstallationPlan) -> str:
    """Spec npm épinglée du plan (``pkg@version``) ou nom seul si inconnue."""
    analysis = plan.analysis
    if analysis is None:
        return plan.name
    if analysis.source_type == SourceType.NPM_COMMAND:
        package, _ = parse_npx_command(plan.source)
        return _pinned_npm_spec(analysis, package or analysis.name or plan.name)
    return _pinned_npm_spec(analysis, analysis.name or plan.name)


__all__ = [
    "build_mcp_config",
    "generate_installation_plan",
    "make_http_config",
    "make_stdio_config",
    "npm_package_spec",
    "slugify",
]
