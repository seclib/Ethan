"""Plan d'installation MCP — structures de données partagées Core/API/CLI."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


def _enum_value(enum_type: type[StrEnum], value: Any, default: str) -> Any:
    """Convertit une valeur sérialisée en enum, sans jamais lever.

    Les records peuvent avoir été écrits par une version antérieure : un
    installateur redémarré doit pouvoir les relire (fail-open de lecture,
    fail-closed d'exécution — la politique Core revalide tout).
    """
    if isinstance(value, enum_type):
        return value
    try:
        return enum_type(str(value))
    except ValueError:
        return enum_type(default)


class SourceType(StrEnum):
    """Type de source d'installation."""

    NPM_COMMAND = "npm_command"  # npx -y package
    NPM_PACKAGE = "npm_package"  # @org/package
    GITHUB = "github"  # URL GitHub
    CUSTOM_COMMAND = "custom_command"  # exécutable + args
    REMOTE_HTTP = "remote_http"  # URL HTTP/SSE


class TransportType(StrEnum):
    """Transport MCP compatible."""

    STDIO = "stdio"
    HTTP = "http"
    STREAMABLE_HTTP = "streamable_http"
    UNKNOWN = "unknown"


class RuntimeType(StrEnum):
    """Runtime requis."""

    NODE = "node"
    PYTHON = "python"
    UNKNOWN = "unknown"


@dataclass
class ProjectAnalysis:
    """Résultat de l'analyse d'une source (aucune exécution de code)."""

    name: str = ""
    version: str = ""
    publisher: str = ""
    description: str = ""
    license: str = ""
    source_type: SourceType = SourceType.CUSTOM_COMMAND
    source_url: str = ""
    runtime: RuntimeType = RuntimeType.UNKNOWN
    runtime_version: str = ""
    package_manager: str = ""
    entry_point: str = ""
    transport: TransportType = TransportType.UNKNOWN
    dependencies: list[str] = field(default_factory=list)
    env_vars: list[str] = field(default_factory=list)
    secrets: list[str] = field(default_factory=list)
    is_mcp_server: bool = False
    tool_type: str = "unknown"  # mcp_server, cli_tool, library, plugin, dependency
    prerequisites: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    #: True dès qu'un manifeste (npm view, package.json, pyproject.toml) a été
    #: lu. Permet de distinguer « pas un serveur MCP » (métadonnées fiables)
    #: de « identité inconnue » (réseau/npm indisponible) — l'installateur ne
    #: transforme jamais la seconde situation en certitude.
    metadata_available: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "publisher": self.publisher,
            "description": self.description,
            "license": self.license,
            "source_type": self.source_type.value,
            "source_url": self.source_url,
            "runtime": self.runtime.value,
            "runtime_version": self.runtime_version,
            "package_manager": self.package_manager,
            "entry_point": self.entry_point,
            "transport": self.transport.value,
            "dependencies": self.dependencies,
            "env_vars": self.env_vars,
            "secrets": self.secrets,
            "is_mcp_server": self.is_mcp_server,
            "tool_type": self.tool_type,
            "prerequisites": self.prerequisites,
            "errors": self.errors,
            "metadata_available": self.metadata_available,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ProjectAnalysis:
        return cls(
            name=str(data.get("name") or ""),
            version=str(data.get("version") or ""),
            publisher=str(data.get("publisher") or ""),
            description=str(data.get("description") or ""),
            license=str(data.get("license") or ""),
            source_type=_enum_value(
                SourceType, data.get("source_type"), SourceType.CUSTOM_COMMAND.value
            ),
            source_url=str(data.get("source_url") or ""),
            runtime=_enum_value(RuntimeType, data.get("runtime"), RuntimeType.UNKNOWN.value),
            runtime_version=str(data.get("runtime_version") or ""),
            package_manager=str(data.get("package_manager") or ""),
            entry_point=str(data.get("entry_point") or ""),
            transport=_enum_value(
                TransportType, data.get("transport"), TransportType.UNKNOWN.value
            ),
            dependencies=[str(item) for item in data.get("dependencies") or []],
            env_vars=[str(item) for item in data.get("env_vars") or []],
            secrets=[str(item) for item in data.get("secrets") or []],
            is_mcp_server=bool(data.get("is_mcp_server", False)),
            tool_type=str(data.get("tool_type") or "unknown"),
            prerequisites=[str(item) for item in data.get("prerequisites") or []],
            errors=[str(item) for item in data.get("errors") or []],
            metadata_available=bool(data.get("metadata_available", False)),
        )


@dataclass
class InstallationPlan:
    """Plan d'installation structuré, présenté à l'utilisateur avant exécution."""

    source: str = ""
    name: str = ""
    source_type: SourceType = SourceType.CUSTOM_COMMAND
    resolved_version: str = ""
    runtime: RuntimeType = RuntimeType.UNKNOWN
    package_manager: str = ""
    dependencies: list[str] = field(default_factory=list)
    install_actions: list[str] = field(default_factory=list)
    execution_command: str = ""
    execution_args: list[str] = field(default_factory=list)
    execution_env: dict[str, str] = field(default_factory=dict)
    transport: TransportType = TransportType.UNKNOWN
    isolation: str = "dedicated_directory"
    required_permissions: list[str] = field(default_factory=list)
    expected_mcp_config: dict[str, Any] = field(default_factory=dict)
    analysis: ProjectAnalysis | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "name": self.name,
            "source_type": self.source_type.value,
            "resolved_version": self.resolved_version,
            "runtime": self.runtime.value,
            "package_manager": self.package_manager,
            "dependencies": self.dependencies,
            "install_actions": self.install_actions,
            "execution_command": self.execution_command,
            "execution_args": self.execution_args,
            "execution_env": self.execution_env,
            "transport": self.transport.value,
            "isolation": self.isolation,
            "required_permissions": self.required_permissions,
            "expected_mcp_config": self.expected_mcp_config,
            "analysis": self.analysis.to_dict() if self.analysis else None,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> InstallationPlan:
        raw_analysis = data.get("analysis")
        execution_env = data.get("execution_env")
        expected = data.get("expected_mcp_config")
        return cls(
            source=str(data.get("source") or ""),
            name=str(data.get("name") or ""),
            source_type=_enum_value(
                SourceType, data.get("source_type"), SourceType.CUSTOM_COMMAND.value
            ),
            resolved_version=str(data.get("resolved_version") or ""),
            runtime=_enum_value(RuntimeType, data.get("runtime"), RuntimeType.UNKNOWN.value),
            package_manager=str(data.get("package_manager") or ""),
            dependencies=[str(item) for item in data.get("dependencies") or []],
            install_actions=[str(item) for item in data.get("install_actions") or []],
            execution_command=str(data.get("execution_command") or ""),
            execution_args=[str(item) for item in data.get("execution_args") or []],
            execution_env={str(k): str(v) for k, v in (execution_env or {}).items()},
            transport=_enum_value(
                TransportType, data.get("transport"), TransportType.UNKNOWN.value
            ),
            isolation=str(data.get("isolation") or "dedicated_directory"),
            required_permissions=[str(item) for item in data.get("required_permissions") or []],
            expected_mcp_config=dict(expected or {}),
            analysis=(
                ProjectAnalysis.from_dict(raw_analysis)
                if isinstance(raw_analysis, Mapping)
                else None
            ),
        )
