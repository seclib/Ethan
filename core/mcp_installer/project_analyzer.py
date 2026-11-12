"""Analyse de projet MCP — détection de runtime, transport, dépendances.

L'analyse est strictement en lecture : aucun script du projet analysé n'est
exécuté. Un dépôt GitHub est cloné dans un répertoire temporaire uniquement
pour lire ses manifestes, puis supprimé.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

import tomllib

from core.mcp_installer.plan import ProjectAnalysis, RuntimeType, SourceType, TransportType
from core.mcp_installer.source_acquirer import (
    acquire_github_repo,
    acquire_npm_info,
    detect_runtime,
    detect_source_type,
    parse_npx_command,
)
from core.mcp_installer.source_validation import (
    McpSourceValidationError,
    validate_remote_http_url,
)

_MCP_MARKERS = ("mcp", "model context protocol", "model-context-protocol")


def _looks_like_mcp(*values: str) -> bool:
    """Détection volontairement conservatrice : marqueur explicite requis."""
    haystack = " ".join(v for v in values if v).lower()
    return any(marker in haystack for marker in _MCP_MARKERS)


def _keywords(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).lower() for item in value]
    return []


def analyze_npm_package(package: str) -> ProjectAnalysis:
    """Analyse un package npm et détermine s'il fournit un serveur MCP."""
    analysis = ProjectAnalysis(
        name=package,
        source_type=SourceType.NPM_PACKAGE,
        source_url=f"https://www.npmjs.com/package/{package}",
        runtime=RuntimeType.NODE,
        package_manager="npm",
    )
    info = acquire_npm_info(package)
    if info.get("errors"):
        # npm indisponible (réseau, proxy, config nvm…) : l'identité reste
        # inconnue. On ne conclut PAS que le package n'est pas un serveur MCP.
        analysis.errors.extend(info["errors"])
        analysis.prerequisites.append("npm metadata unavailable")
        return analysis

    analysis.metadata_available = True
    analysis.name = info.get("name", package) or package
    analysis.version = info.get("version", "")
    analysis.description = info.get("description", "")
    analysis.license = info.get("license", "")
    repo = info.get("repository", {})
    if isinstance(repo, dict) and repo.get("url"):
        analysis.source_url = str(repo["url"])
    analysis.dependencies = list(info.get("dependencies") or [])
    engines = info.get("engines", {})
    if isinstance(engines, dict) and engines.get("node"):
        analysis.runtime_version = str(engines["node"])

    bin_entry = info.get("bin", {})
    if isinstance(bin_entry, dict) and bin_entry:
        analysis.entry_point = str(next(iter(bin_entry.values())))
    elif isinstance(bin_entry, str):
        analysis.entry_point = bin_entry

    is_mcp = _looks_like_mcp(analysis.description, *(_keywords(info.get("keywords"))))
    analysis.is_mcp_server = is_mcp
    analysis.tool_type = "mcp_server" if is_mcp else "unknown"
    analysis.transport = TransportType.STDIO if is_mcp else TransportType.UNKNOWN

    runtime_info = detect_runtime()
    if runtime_info.get("node") is None:
        analysis.prerequisites.append("Node.js not found on PATH")
        analysis.errors.append("Node.js is required but not installed")
    if runtime_info.get("npm") is None:
        analysis.prerequisites.append("npm not found on PATH")
        analysis.errors.append("npm is required but not installed")

    return analysis


def _node_entry(data: dict[str, Any]) -> str:
    bin_entry = data.get("bin")
    if isinstance(bin_entry, dict) and bin_entry:
        return str(next(iter(bin_entry.values())))
    if isinstance(bin_entry, str):
        return bin_entry
    return str(data.get("main") or "")


def analyze_github_repo(repo_path: str) -> ProjectAnalysis:
    """Analyse un dépôt GitHub déjà cloné (lecture seule)."""
    analysis = ProjectAnalysis(source_type=SourceType.GITHUB, source_url=repo_path)
    root = Path(repo_path)
    if not root.exists():
        analysis.errors.append(f"repository path does not exist: {repo_path}")
        return analysis

    pkg_json = root / "package.json"
    pyproject = root / "pyproject.toml"
    setup_py = root / "setup.py"

    if pkg_json.exists():
        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            analysis.errors.append(f"invalid package.json: {exc}")
            return analysis
        analysis.metadata_available = True
        analysis.name = str(data.get("name") or root.name)
        analysis.version = str(data.get("version") or "")
        analysis.description = str(data.get("description") or "")
        analysis.license = str(data.get("license") or "")
        analysis.dependencies = list((data.get("dependencies") or {}).keys())
        engines = data.get("engines", {})
        if isinstance(engines, dict):
            analysis.runtime_version = str(engines.get("node") or "")
        analysis.runtime = RuntimeType.NODE
        analysis.package_manager = "npm"
        analysis.entry_point = _node_entry(data)
        is_mcp = _looks_like_mcp(
            analysis.description, analysis.name, *(_keywords(data.get("keywords")))
        )
        analysis.is_mcp_server = is_mcp
        analysis.tool_type = "mcp_server" if is_mcp else "unknown"
        analysis.transport = TransportType.STDIO if is_mcp else TransportType.UNKNOWN
    elif pyproject.exists() or setup_py.exists():
        analysis.metadata_available = True
        analysis.name = root.name
        analysis.runtime = RuntimeType.PYTHON
        analysis.package_manager = "pip"
        if pyproject.exists():
            try:
                py_data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
                project = py_data.get("project", {})
                analysis.name = str(project.get("name") or root.name)
                analysis.version = str(project.get("version") or "")
                analysis.description = str(project.get("description") or "")
                dependencies = list(project.get("dependencies") or [])
                analysis.dependencies = dependencies
                scripts = project.get("scripts", {})
                if isinstance(scripts, dict) and scripts:
                    # Le nom du script console est la clé : c'est l'exécutable
                    # créé dans le virtualenv (la valeur est le module:fonction).
                    analysis.entry_point = str(next(iter(scripts)))
            except (tomllib.TOMLDecodeError, OSError) as exc:
                analysis.errors.append(f"invalid pyproject.toml: {exc}")
        readme = root / "README.md"
        readme_text = readme.read_text(encoding="utf-8", errors="ignore") if readme.exists() else ""
        is_mcp = _looks_like_mcp(
            analysis.description, analysis.name, readme_text[:2000]
        )
        analysis.is_mcp_server = is_mcp
        analysis.tool_type = "mcp_server" if is_mcp else "unknown"
        analysis.transport = TransportType.STDIO if is_mcp else TransportType.UNKNOWN

    for mcp_file in ("mcp.json", ".mcp.json", "mcp-config.json"):
        if (root / mcp_file).exists():
            analysis.metadata_available = True
            analysis.is_mcp_server = True
            analysis.tool_type = "mcp_server"
            if analysis.transport == TransportType.UNKNOWN:
                analysis.transport = TransportType.STDIO

    if not analysis.name:
        analysis.name = root.name

    runtime_info = detect_runtime()
    if analysis.runtime == RuntimeType.NODE and runtime_info.get("node") is None:
        analysis.prerequisites.append("Node.js not found")
        analysis.errors.append("Node.js required but not installed")
    if (
        analysis.runtime == RuntimeType.PYTHON
        and runtime_info.get("python3") is None
        and runtime_info.get("python") is None
    ):
        analysis.prerequisites.append("Python not found")
        analysis.errors.append("Python required but not installed")

    return analysis


def _github_name(url: str) -> str:
    return url.rstrip("/").removesuffix(".git").split("/")[-1] or url


def analyze_github_url(url: str) -> ProjectAnalysis:
    """Clone temporairement un dépôt (sans exécuter son code) puis l'analyse."""
    tmp_root = Path(tempfile.mkdtemp(prefix="ethan-mcp-analyze-"))
    repo_dir = tmp_root / "repo"
    try:
        acquisition = acquire_github_repo(url, str(repo_dir))
        if acquisition.get("errors"):
            return ProjectAnalysis(
                name=_github_name(url),
                source_type=SourceType.GITHUB,
                source_url=url,
                errors=list(acquisition["errors"]),
            )
        analysis = analyze_github_repo(str(repo_dir))
        analysis.source_url = url
        return analysis
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)


def analyze_source(source: str) -> ProjectAnalysis:
    """Analyse une source (URL, package, commande) sans rien exécuter."""
    normalized = source.strip()
    source_type = detect_source_type(normalized)

    if source_type == SourceType.NPM_PACKAGE:
        return analyze_npm_package(normalized)
    if source_type == SourceType.NPM_COMMAND:
        package, _extra_args = parse_npx_command(normalized)
        analysis = analyze_npm_package(package or normalized)
        analysis.source_type = SourceType.NPM_COMMAND
        analysis.source_url = normalized
        return analysis
    if source_type == SourceType.GITHUB:
        return analyze_github_url(normalized)
    if source_type == SourceType.REMOTE_HTTP:
        try:
            safe_url = validate_remote_http_url(normalized)
        except McpSourceValidationError as exc:
            return ProjectAnalysis(
                name=normalized.rstrip("/").split("/")[-1] or normalized,
                source_type=SourceType.REMOTE_HTTP,
                source_url=normalized,
                is_mcp_server=False,
                tool_type="unknown",
                transport=TransportType.UNKNOWN,
                errors=[str(exc)],
            )
        return ProjectAnalysis(
            name=safe_url.rstrip("/").split("/")[-1] or safe_url,
            source_type=SourceType.REMOTE_HTTP,
            source_url=safe_url,
            is_mcp_server=True,
            tool_type="mcp_server",
            transport=TransportType.HTTP,
            metadata_available=False,
        )
    return ProjectAnalysis(
        name=(parse_npx_command(normalized)[0] or normalized),
        source_type=SourceType.CUSTOM_COMMAND,
        source_url=normalized,
        entry_point=parse_npx_command(normalized)[0],
        is_mcp_server=False,
        tool_type="unknown",
        transport=TransportType.UNKNOWN,
    )
