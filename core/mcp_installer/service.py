"""McpInstaller — installation contrôlée de serveurs MCP externes (Core-owned).

Ce service est l'unique chemin d'installation MCP d'ETHAN. Il ne remplace ni
le registre canonique (`ToolServerManager`) ni la politique de sûreté
(`core.tools.server_policy`) : il les réutilise.

Flux invariable :

1. ``analyze`` — lecture seule (npm view, clone GitHub temporaire), produit un
   plan et le persiste côté Core (aucune donnée de plan ne vient du client).
2. ``request_install`` — vérifie les prérequis, pré-valide la politique Core,
   crée une demande HROT ``PLUGIN_INSTALL`` et rend la main immédiatement.
3. Approbation humaine (``ApprovalEngine`` / ``/internal/approval/resolve``).
4. ``_install`` — installation isolée sous ``~/.ethan/mcp/servers``, manifeste
   durable, enregistrement via ``ToolServerManager.register`` puis
   synchronisation best-effort.

Aucun secret n'est journalisé ni renvoyé : le plan ne contient que des noms de
variables, jamais leurs valeurs.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import shutil
import signal
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4

from core.approval import ApprovalCategory, ApprovalEngine, ApprovalStatus
from core.audit import AuditCategory, AuditDecision, AuditStore
from core.mcp_installer.installer import (
    generate_installation_plan,
    make_http_config,
    make_stdio_config,
    npm_package_spec,
    slugify,
)
from core.mcp_installer.isolation import (
    InstallIsolationProvider,
    IsolationUnavailableError,
    default_isolation_provider,
)
from core.mcp_installer.plan import InstallationPlan, ProjectAnalysis, SourceType
from core.mcp_installer.source_acquirer import acquire_github_repo, acquire_npm_info
from core.mcp_installer.source_validation import (
    McpSourceValidationError,
    validate_source_text,
)
from core.state.record_store import CoreRecordStore
from core.tools.server_policy import validate_server_config
from core.tools.servers import ToolServerManager

logger = logging.getLogger(__name__)


class McpInstallError(RuntimeError):
    """Erreur d'installation MCP exposable à l'interface (message sûr)."""

    def __init__(self, message: str, *, code: str = "MCP-INSTALL") -> None:
        super().__init__(message)
        self.code = code


class InstallationState(StrEnum):
    """États durables d'une installation MCP.

    Compatibilité : les états historiques (installed/removed) restent valides.
    Phase 3 ajoute approved/installing/starting/ready/stopped/uninstalling/uninstalled.
    """

    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    INSTALLING = "installing"
    INSTALLED = "installed"
    STARTING = "starting"
    READY = "ready"
    FAILED = "failed"
    STOPPED = "stopped"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    UNINSTALLING = "uninstalling"
    UNINSTALLED = "uninstalled"
    REMOVED = "removed"


_TERMINAL_STATES = {
    InstallationState.READY,
    InstallationState.INSTALLED,
    InstallationState.FAILED,
    InstallationState.STOPPED,
    InstallationState.REJECTED,
    InstallationState.CANCELLED,
    InstallationState.UNINSTALLED,
    InstallationState.REMOVED,
}


@dataclass(frozen=True)
class CommandResult:
    """Résultat borné d'une commande d'installation (jamais de secret)."""

    returncode: int
    stdout: str = ""
    stderr: str = ""


CommandRunner = Callable[[list[str], Path, int], Awaitable[CommandResult]]

_MAX_LOG_CHARS = 4000


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _decode(raw: bytes) -> str:
    return raw.decode("utf-8", errors="replace") if raw else ""


def _tail(value: str, limit: int = _MAX_LOG_CHARS) -> str:
    cleaned = value.strip()
    return cleaned[-limit:] if len(cleaned) > limit else cleaned


def _clean_env(root: Path) -> dict[str, str]:
    """Environnement minimal, sans secrets de l'opérateur.

    ``npm_config_userconfig`` pointe vers un fichier vide dans l'isolation :
    la configuration nvm/registry personnelle de l'opérateur (parfois cassée)
    ne peut ni casser ni influencer une installation.
    """
    env: dict[str, str] = {}
    for key in ("PATH", "LANG", "LC_ALL", "TZ", "TMPDIR", "HOME"):
        if os.environ.get(key):
            env[key] = os.environ[key]
    env.setdefault("PATH", "/usr/local/bin:/usr/bin:/bin")
    env["CI"] = "1"
    env["npm_config_audit"] = "false"
    env["npm_config_fund"] = "false"
    env["npm_config_update_notifier"] = "false"
    env["npm_config_ignore_scripts"] = "true"
    env["npm_config_cache"] = str(root / ".npm-cache")
    env["npm_config_userconfig"] = str(root / ".npmrc")
    return env


async def _exec_runner(argv: list[str], cwd: Path, timeout: int) -> CommandResult:
    """Exécute une commande d'installation sans shell et sans héritage d'env."""
    process = await asyncio.create_subprocess_exec(
        *argv,
        cwd=str(cwd),
        env=_clean_env(cwd),
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        start_new_session=True,
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
    except TimeoutError as exc:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        await process.communicate()
        raise McpInstallError(
            f"commande interrompue après {timeout}s : {Path(argv[0]).name}",
            code="MCP-TIMEOUT",
        ) from exc
    return CommandResult(process.returncode or 0, _decode(stdout), _decode(stderr))


def _fingerprint(source: str, plan: dict[str, Any]) -> str:
    payload = json.dumps({"source": source, "plan": plan}, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def _package_name(spec: str) -> str:
    """Nom npm sans version (supporte les packages scopés)."""
    cleaned = spec.strip()
    if cleaned.startswith("@"):
        parts = cleaned.split("@")
        return f"@{parts[1]}" if len(parts) > 1 else cleaned
    return cleaned.split("@", 1)[0]


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


class McpInstaller:
    """Analyse, approuve et installe des serveurs MCP sous contrôle Core."""

    _INSTALLATIONS = "mcp-installations"
    _PLANS = "mcp-installer-plans"
    _PLAN_TTL_SECONDS = 1800

    def __init__(
        self,
        *,
        tool_servers: ToolServerManager,
        approval_engine: ApprovalEngine,
        store: CoreRecordStore | None = None,
        audit_store: AuditStore | None = None,
        install_root: str | Path | None = None,
        runner: CommandRunner | None = None,
        isolation_provider: InstallIsolationProvider | None = None,
        approval_timeout_seconds: int = 900,
        install_timeout_seconds: int = 600,
        sync_timeout_seconds: int = 120,
    ) -> None:
        self._tool_servers = tool_servers
        self._approval = approval_engine
        self._store = store or CoreRecordStore()
        self._audit_store = audit_store
        configured_root = install_root or os.environ.get("ETHAN_MCP_INSTALL_ROOT")
        self._root = Path(configured_root or (Path.home() / ".ethan" / "mcp" / "servers"))
        self._runner = runner or _exec_runner
        self._isolation = isolation_provider or default_isolation_provider()
        self._approval_timeout = max(30, int(approval_timeout_seconds))
        self._install_timeout = max(30, int(install_timeout_seconds))
        self._sync_timeout = max(10, int(sync_timeout_seconds))
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._lock = asyncio.Lock()

    @property
    def install_root(self) -> str:
        """Racine d'isolation exposée pour le diagnostic (jamais un secret)."""
        return str(self._root)

    # ── Analyse (lecture seule) ────────────────────────────────────

    async def analyze(self, source: str) -> dict[str, Any]:
        """Analyse une source et persiste le plan côté Core (aucune mutation)."""
        try:
            normalized = validate_source_text(source or "")
        except McpSourceValidationError as exc:
            raise McpInstallError(
                str(exc), code=getattr(exc, "code", "MCP-SOURCE-INVALID")
            ) from exc
        plan = await asyncio.to_thread(generate_installation_plan, normalized)
        plan_payload = plan.to_dict()
        analysis_id = _fingerprint(normalized, plan_payload)
        await self._store.save(
            self._PLANS,
            analysis_id,
            {
                "analysis_id": analysis_id,
                "source": normalized,
                "plan": plan_payload,
                "created_at": _now(),
            },
        )
        return self._analysis_payload(analysis_id, plan)

    def _analysis_payload(self, analysis_id: str, plan: InstallationPlan) -> dict[str, Any]:
        analysis = plan.analysis
        is_mcp = bool(analysis and analysis.is_mcp_server)
        warnings: list[str] = []
        unresolved_prerequisites: list[str] = []
        if analysis:
            warnings.extend(str(item) for item in analysis.errors)
            unresolved_prerequisites.extend(str(item) for item in analysis.prerequisites)
            if not analysis.metadata_available and analysis.source_type in (
                SourceType.NPM_PACKAGE,
                SourceType.NPM_COMMAND,
            ):
                warnings.append(
                    "Métadonnées npm indisponibles : l'identité du package n'a pas pu "
                    "être vérifiée. Une confirmation explicite est requise."
                )

        status, confidence, evidence = self._classify(analysis)
        if status == "invalid_or_unsupported_source":
            # Source refusée/invalide : aucune installation possible sans correction.
            pass

        # Compatibilité installateur (Phase 1) : ces clés restent présentes.
        payload: dict[str, Any] = {
            "analysis_id": analysis_id,
            "plan": plan.to_dict(),
            "is_mcp_server": is_mcp,
            "requires_confirmation": status not in {
                "confirmed_mcp_server",
                "probable_mcp_server",
            },
            "warnings": warnings,
            # Phase 2 — contrat partagé API/CLI
            "analysis_status": status,
            "source": self._source_section(plan, analysis),
            "project_analysis": self._project_analysis_section(plan, analysis, evidence),
            "installation_plan": self._installation_plan_section(
                plan, warnings, unresolved_prerequisites
            ),
            "identification": {
                "status": status,
                "confidence": confidence,
                "evidence": evidence,
            },
        }
        return payload

    @staticmethod
    def _source_section(
        plan: InstallationPlan, analysis: ProjectAnalysis | None
    ) -> dict[str, Any]:
        source_type = plan.source_type.value
        resolved_package = ""
        repository = ""
        package_name = ""
        package_version = ""
        if analysis is not None:
            if analysis.source_type in (SourceType.NPM_PACKAGE, SourceType.NPM_COMMAND):
                package_name = analysis.name or ""
                package_version = analysis.version or ""
                resolved_package = package_name
            if analysis.source_type == SourceType.GITHUB:
                repository = analysis.source_url or plan.source
                resolved_package = repository
            if analysis.source_type == SourceType.REMOTE_HTTP:
                resolved_package = analysis.source_url or plan.source
        return {
            "type": source_type,
            "original": plan.source,
            "resolved_package_or_repository": resolved_package or plan.source,
            "package_name": package_name,
            "package_version": package_version,
            "repository": repository,
        }

    @staticmethod
    def _project_analysis_section(
        plan: InstallationPlan, analysis: ProjectAnalysis | None, evidence: list[str]
    ) -> dict[str, Any]:
        if analysis is None:
            return {
                "detected_project_type": "unknown",
                "runtime": "unknown",
                "runtime_version_requirements": "",
                "package_manager": "",
                "dependencies": [],
                "potential_mcp_identification": "unknown",
                "confidence": "low",
                "evidence": evidence,
                "detected_entry_point": "",
                "detected_transport": "unknown",
            }
        if analysis.is_mcp_server:
            potential = "mcp_server"
        elif analysis.metadata_available and analysis.tool_type == "unknown":
            potential = "non_mcp"
        else:
            potential = "unknown"
        project_type = {
            SourceType.NPM_PACKAGE: "npm_package",
            SourceType.NPM_COMMAND: "npm_command",
            SourceType.GITHUB: "git_repository",
            SourceType.REMOTE_HTTP: "remote_mcp_endpoint",
            SourceType.CUSTOM_COMMAND: "custom_command",
        }.get(analysis.source_type, "unknown")
        confidence = "high" if any("manifest MCP" in item for item in evidence) else (
            "medium" if analysis.is_mcp_server else "low"
        )
        return {
            "detected_project_type": project_type,
            "runtime": analysis.runtime.value,
            "runtime_version_requirements": analysis.runtime_version,
            "package_manager": analysis.package_manager,
            "dependencies": list(analysis.dependencies),
            "potential_mcp_identification": potential,
            "confidence": confidence,
            "evidence": evidence,
            "detected_entry_point": analysis.entry_point,
            "detected_transport": analysis.transport.value,
        }

    @staticmethod
    def _installation_plan_section(
        plan: InstallationPlan,
        warnings: list[str],
        unresolved_prerequisites: list[str],
    ) -> dict[str, Any]:
        # Valeurs d'environnement interdites en sortie : seuls les noms sont exposés.
        env_names = sorted(set(plan.execution_env.keys())) if plan.execution_env else []
        if plan.analysis and plan.analysis.env_vars:
            env_names = sorted(set(env_names) | set(plan.analysis.env_vars))
        launch = {
            "command": plan.execution_command,
            "args": list(plan.execution_args),
            "transport": plan.transport.value,
        }
        install_command = ""
        for action in plan.install_actions:
            if action.lower().startswith("installer") or "npm install" in action.lower():
                install_command = action
                break
        return {
            "required_actions": list(plan.install_actions),
            "installation_command": install_command,
            "launch_command": launch,
            "environment_variable_names": env_names,
            "mcp_configuration": dict(plan.expected_mcp_config),
            "required_permissions": list(plan.required_permissions),
            "isolation_requirements": plan.isolation,
            "warnings": warnings,
            "unresolved_prerequisites": unresolved_prerequisites,
        }

    @staticmethod
    def _classify(
        analysis: ProjectAnalysis | None,
    ) -> tuple[str, str, list[str]]:
        """Statut d'identification fondé sur des preuves, jamais sur une supposition."""
        if analysis is None:
            return "undetermined_package_type", "low", ["aucune analyse disponible"]

        evidence: list[str] = []
        errors_text = " ".join(analysis.errors).lower()
        invalid_markers = (
            "ssrf",
            "interdit",
            "invalide",
            "invalid",
            "unsupported",
            "non support",
            "métadonnées cloud",
            "metadata endpoint",
            "forbidden",
            "not allowed",
            "credentials in the url",
            "credentials inline",
            "github.com est accepté",
            "doivent utiliser https",
            "url github invalide",
            "résolution dns impossible",
            "nom de package npm invalide",
            "source trop longue",
            "caractères de contrôle",
            "schéma",
            "scheme",
        )
        if any(marker in errors_text for marker in invalid_markers):
            evidence.extend(analysis.errors)
            return "invalid_or_unsupported_source", "high", evidence

        source_type = analysis.source_type
        if source_type == SourceType.REMOTE_HTTP:
            evidence.append("endpoint HTTP distant déclaré comme transport MCP")
            evidence.append("handshake MCP non exécuté pendant l'analyse (lecture seule)")
            return "probable_mcp_server", "medium", evidence

        if source_type == SourceType.CUSTOM_COMMAND:
            if analysis.is_mcp_server:
                evidence.append("marqueur MCP explicite détecté")
                return "probable_mcp_server", "medium", evidence
            evidence.append("commande personnalisée : identité MCP non prouvée")
            return "undetermined_package_type", "low", evidence

        # npm / GitHub : signaux
        haystack = " ".join(
            [analysis.name, analysis.description, analysis.entry_point, analysis.source_url]
        ).lower()
        markers = ("mcp", "model context protocol", "model-context-protocol")
        has_marker = any(marker in haystack for marker in markers)

        # Manifeste MCP explicite (le plus fort)
        # (project_analyzer positionne is_mcp_server True sur fichiers mcp.json)
        # On détecte via transport connu + is_mcp_server + metadata disponible sur repo
        if analysis.is_mcp_server and has_marker and analysis.metadata_available:
            evidence.append("marqueurs MCP explicites détectés dans les métadonnées")
            return "confirmed_mcp_server", "high", evidence
        if analysis.is_mcp_server and has_marker:
            evidence.append("marqueurs MCP détectés (métadonnées partielles)")
            return "probable_mcp_server", "medium", evidence
        if analysis.is_mcp_server:
            evidence.append("indicateur MCP détecté")
            return "probable_mcp_server", "medium", evidence

        if not analysis.metadata_available and source_type in (
            SourceType.NPM_PACKAGE,
            SourceType.NPM_COMMAND,
        ):
            evidence.append("métadonnées npm indisponibles : type non déterminable")
            evidence.extend(analysis.errors)
            return "undetermined_package_type", "low", evidence

        if analysis.metadata_available:
            evidence.append("métadonnées analysées sans marqueur MCP explicite")
            return "non_mcp_package", "high", evidence

        evidence.append("informations insuffisantes pour conclure")
        evidence.extend(analysis.errors)
        return "undetermined_package_type", "low", evidence

    # ── Demande d'installation ─────────────────────────────────────

    async def request_install(
        self,
        *,
        actor: str,
        source: str | None = None,
        analysis_id: str | None = None,
        confirmed_mcp: bool = False,
        replaces: str | None = None,
    ) -> dict[str, Any]:
        """Crée une demande HROT ; l'installation démarre après approbation."""
        plan = await self._resolve_plan(source=source, analysis_id=analysis_id)
        analysis = plan.analysis
        is_mcp = bool(analysis and analysis.is_mcp_server)
        if not is_mcp and not confirmed_mcp:
            raise McpInstallError(
                "l'analyse ne confirme pas un serveur MCP : renseignez "
                "confirmed_mcp=true pour assumer explicitement ce choix",
                code="MCP-CONFIRMATION-REQUIRED",
            )
        if plan.source_type == SourceType.GITHUB and analysis is not None:
            if not analysis.metadata_available:
                raise McpInstallError(
                    "dépôt GitHub illisible : " + "; ".join(analysis.errors or ["clone échoué"]),
                    code="MCP-ANALYSIS",
                )
        self._assert_prerequisites(plan)
        await asyncio.to_thread(self._preflight_policy, plan)
        isolation = await asyncio.to_thread(self._isolation.assess, plan)
        # Fail closed avant toute demande HROT pour les installations non isolables.
        if isolation.required and not (isolation.available and isolation.effective):
            raise McpInstallError(isolation.reason, code="MCP-ISOLATION-UNAVAILABLE")

        installation_id = f"mcpi_{uuid4().hex[:12]}"
        plan_payload = plan.to_dict()
        plan_fingerprint = _fingerprint(plan.source, plan_payload)
        record: dict[str, Any] = {
            "id": installation_id,
            "source": plan.source,
            "name": plan.name,
            "status": InstallationState.PENDING_APPROVAL.value,
            "phase": "pending_approval",
            "progress": 5,
            "actor": actor or "unknown",
            "confirmed_mcp": confirmed_mcp,
            "is_mcp_server": is_mcp,
            "plan": plan_payload,
            "plan_fingerprint": plan_fingerprint,
            "server_id": None,
            "installation_dir": None,
            "installed_version": "",
            "mcp_config": {},
            "sync": {},
            "verification": {},
            "isolation": isolation.to_dict(),
            "diagnostics": [],
            "replaces": replaces,
            "replaced_by": None,
            "approval_request_id": None,
            "error": "",
            "created_at": _now(),
            "updated_at": _now(),
            "approved_at": None,
            "installed_at": None,
            "ready_at": None,
            "removed_at": None,
        }
        await self._store.save(self._INSTALLATIONS, installation_id, record)
        self._audit(
            AuditDecision.PENDING,
            "mcp_installer.request",
            actor,
            {
                "installation_id": installation_id,
                "source": plan.source,
                "name": plan.name,
                "plan_fingerprint": plan_fingerprint,
                "isolation": isolation.to_dict(),
            },
        )
        task = asyncio.create_task(
            self._approve_and_install(installation_id, plan, confirmed_mcp, plan_fingerprint),
            name=f"mcp-install-{installation_id}",
        )
        self._tasks[installation_id] = task
        return self._public(record)

    async def _resolve_plan(
        self, *, source: str | None = None, analysis_id: str | None = None
    ) -> InstallationPlan:
        if analysis_id:
            stored = await self._store.get(self._PLANS, analysis_id)
            if stored is None:
                raise McpInstallError(
                    "analyse inconnue ou expirée : relancez l'analyse",
                    code="MCP-ANALYSIS-NOT-FOUND",
                )
            created_at = str(stored.get("created_at") or "")
            if created_at:
                try:
                    age = (datetime.now(UTC) - datetime.fromisoformat(created_at)).total_seconds()
                except ValueError:
                    age = 0
                if age > self._PLAN_TTL_SECONDS:
                    raise McpInstallError(
                        "analyse expirée : relancez l'analyse", code="MCP-ANALYSIS-EXPIRED"
                    )
            raw_plan = stored.get("plan")
            if not isinstance(raw_plan, dict):
                raise McpInstallError("plan stocké invalide", code="MCP-ANALYSIS-INVALID")
            return InstallationPlan.from_dict(raw_plan)
        if source:
            return await asyncio.to_thread(generate_installation_plan, source.strip())
        raise McpInstallError("source ou analysis_id requis", code="MCP-SOURCE")

    def _assert_prerequisites(self, plan: InstallationPlan) -> None:
        analysis = plan.analysis
        source_type = plan.source_type
        if source_type in (SourceType.NPM_COMMAND, SourceType.NPM_PACKAGE):
            if shutil.which("npm") is None or shutil.which("node") is None:
                raise McpInstallError(
                    "Node.js et npm sont requis pour installer un serveur MCP npm",
                    code="MCP-PREREQUISITE",
                )
        elif source_type == SourceType.GITHUB:
            if shutil.which("git") is None:
                raise McpInstallError(
                    "git est requis pour installer depuis GitHub", code="MCP-PREREQUISITE"
                )
            manager = analysis.package_manager if analysis else ""
            if manager == "npm" and (shutil.which("npm") is None or shutil.which("node") is None):
                raise McpInstallError(
                    "Node.js et npm sont requis pour ce dépôt", code="MCP-PREREQUISITE"
                )
            if (
                manager == "pip"
                and shutil.which("python3") is None
                and shutil.which("python") is None
            ):
                raise McpInstallError(
                    "Python 3 est requis pour ce dépôt", code="MCP-PREREQUISITE"
                )
        elif source_type == SourceType.CUSTOM_COMMAND:
            command = plan.execution_command
            if not command or not os.path.isabs(command) or not Path(command).exists():
                raise McpInstallError(
                    "la commande doit être un exécutable absolu existant",
                    code="MCP-PREREQUISITE",
                )

    def _preflight_policy(self, plan: InstallationPlan) -> None:
        """Échoue tôt si la politique Core refusera l'enregistrement final."""
        name = slugify(plan.name)
        try:
            if plan.source_type == SourceType.REMOTE_HTTP:
                validate_server_config(
                    name=name, url=plan.source, metadata={"transport": "http"}
                )
            elif plan.source_type == SourceType.CUSTOM_COMMAND:
                validate_server_config(
                    name=name,
                    url=f"stdio://{name}",
                    metadata={
                        "transport": "stdio",
                        "command": plan.execution_command,
                        "args": list(plan.execution_args),
                    },
                )
            elif plan.source_type in (SourceType.NPM_COMMAND, SourceType.NPM_PACKAGE):
                node = shutil.which("node") or "node"
                validate_server_config(
                    name=name,
                    url=f"stdio://{name}",
                    metadata={"transport": "stdio", "command": node, "args": []},
                )
        except ValueError as exc:
            raise McpInstallError(
                f"politique de sûreté Core : {exc}", code="MCP-POLICY"
            ) from exc

    # ── Approbation puis installation ──────────────────────────────

    async def _approve_and_install(
        self,
        installation_id: str,
        plan: InstallationPlan,
        confirmed_mcp: bool,
        plan_fingerprint: str,
    ) -> None:
        actor = "unknown"
        try:
            record = await self._require_record(installation_id)
            actor = str(record.get("actor") or "unknown")
            request = await self._approval.create_request(
                ApprovalCategory.PLUGIN_INSTALL,
                title=f"Installer le serveur MCP : {plan.name}",
                description=(
                    "ETHAN requests permission to install and register an external "
                    "MCP server. Nothing is executed before this approval."
                ),
                details={
                    "installation_id": installation_id,
                    "actor": actor,
                    "source": plan.source,
                    "source_type": plan.source_type.value,
                    "version": plan.resolved_version,
                    "install_actions": plan.install_actions,
                    "required_permissions": plan.required_permissions,
                },
                source="mcp_installer",
                # L'autorité humaine approuve une demande émise par le service :
                # `source_id` ne doit pas être l'acteur, sinon le garde-fou
                # anti-auto-approbation d'ApprovalEngine refuse la confirmation
                # légitime du propriétaire de la machine.
                source_id="mcp_installer",
                timeout_seconds=self._approval_timeout,
                correlation_id=installation_id,
            )
            await self._update(installation_id, approval_request_id=request.id)
            response = await self._approval.await_decision(
                request.id, timeout_seconds=self._approval_timeout
            )
            if response.status is not ApprovalStatus.APPROVED:
                state = (
                    InstallationState.REJECTED
                    if response.status is ApprovalStatus.REJECTED
                    else InstallationState.CANCELLED
                )
                await self._update(
                    installation_id,
                    status=state.value,
                    error=response.reason or response.status.value,
                )
                self._audit(
                    AuditDecision.REJECTED
                    if state is InstallationState.REJECTED
                    else AuditDecision.CANCELLED,
                    "mcp_installer.approval",
                    actor,
                    {"installation_id": installation_id, "status": response.status.value},
                )
                return

            # L'approbation porte sur le plan réellement exécuté.
            record = await self._require_record(installation_id)
            stored_fp = str(record.get("plan_fingerprint") or "")
            stored_plan = record.get("plan")
            stored_plan_fp = ""
            if isinstance(stored_plan, dict):
                try:
                    stored_plan_fp = _fingerprint(
                        str(record.get("source") or plan.source), stored_plan
                    )
                except Exception:  # noqa: BLE001
                    stored_plan_fp = ""
            current_plan_fp = _fingerprint(plan.source, plan.to_dict())
            if (
                (stored_fp and stored_fp != plan_fingerprint)
                or (stored_plan_fp and stored_plan_fp != plan_fingerprint)
                or current_plan_fp != plan_fingerprint
            ):
                await self._update(
                    installation_id,
                    status=InstallationState.FAILED.value,
                    error="plan modifié après approbation : approbation invalidée",
                    phase="failed",
                    progress=100,
                )
                self._audit(
                    AuditDecision.REJECTED,
                    "mcp_installer.plan_changed",
                    actor,
                    {
                        "installation_id": installation_id,
                        "expected": stored_fp or plan_fingerprint,
                        "actual": stored_plan_fp or current_plan_fp,
                    },
                )
                return

            self._audit(
                AuditDecision.APPROVED,
                "mcp_installer.approval",
                actor,
                {
                    "installation_id": installation_id,
                    "approval_request_id": request.id,
                    "plan_fingerprint": plan_fingerprint,
                },
            )
            await self._update(
                installation_id,
                status=InstallationState.APPROVED.value,
                approved_at=_now(),
                phase="approved",
                progress=20,
            )
            await self._install(installation_id, plan, confirmed_mcp, plan_fingerprint)
        except asyncio.CancelledError:
            await self._update(
                installation_id,
                status=InstallationState.CANCELLED.value,
                error="installation annulée",
            )
            raise
        except Exception as exc:  # noqa: BLE001 - l'état durable porte l'échec
            logger.warning("MCP installation %s failed: %s", installation_id, exc)
            await self._update(
                installation_id,
                status=InstallationState.FAILED.value,
                error=_tail(str(exc)),
            )
            self._audit(
                AuditDecision.ERROR,
                "mcp_installer.error",
                actor,
                {"installation_id": installation_id, "error": _tail(str(exc))},
            )
        finally:
            self._tasks.pop(installation_id, None)

    async def _install(
        self,
        installation_id: str,
        plan: InstallationPlan,
        confirmed_mcp: bool,
        plan_fingerprint: str,
    ) -> None:
        # Révérification isolation et empreinte du plan au moment de l'exécution.
        try:
            self._isolation.ensure_available(plan)
        except IsolationUnavailableError as exc:
            raise McpInstallError(str(exc), code=exc.code) from exc
        if _fingerprint(plan.source, plan.to_dict()) != plan_fingerprint:
            raise McpInstallError(
                "plan modifié après approbation : installation refusée",
                code="MCP-PLAN-CHANGED",
            )

        installation_dir = self._installation_dir(plan, installation_id)
        installation_dir.mkdir(parents=True, exist_ok=False)
        server_id: str | None = None

        try:
            isolation = self._isolation.assess(plan)
            await self._update(
                installation_id,
                status=InstallationState.INSTALLING.value,
                phase="installing",
                progress=40,
                isolation=isolation.to_dict(),
            )
            if plan.source_type in (SourceType.NPM_COMMAND, SourceType.NPM_PACKAGE):
                config, installed_version = await self._install_npm(
                    plan, installation_dir, isolation=isolation
                )
            elif plan.source_type == SourceType.GITHUB:
                config, installed_version = await self._install_github(
                    plan, installation_dir, isolation=isolation
                )
            elif plan.source_type == SourceType.CUSTOM_COMMAND:
                config, installed_version = self._install_custom(plan)
            elif plan.source_type == SourceType.REMOTE_HTTP:
                config, installed_version = self._install_remote(plan)
            else:
                raise McpInstallError(
                    f"type de source non pris en charge : {plan.source_type.value}",
                    code="MCP-SOURCE-TYPE",
                )

            if not config:
                raise McpInstallError(
                    "aucune configuration MCP n'a pu être produite", code="MCP-CONFIG"
                )
            if not (plan.analysis and plan.analysis.is_mcp_server) and not confirmed_mcp:
                raise McpInstallError(
                    "identité MCP non confirmée", code="MCP-CONFIRMATION-REQUIRED"
                )

            transport = "http" if plan.source_type == SourceType.REMOTE_HTTP else "stdio"
            server = await self._tool_servers.register(
                name=str(config["name"]),
                url=str(config["url"]),
                description=f"MCP installé par ETHAN depuis {plan.source}",
                metadata=dict(config["metadata"]),
            )
            server_id = str(server.get("id") or "")
            self._write_manifest(
                installation_dir,
                installation_id=installation_id,
                plan=plan,
                server=server,
                installed_version=installed_version,
                config=config,
                plan_fingerprint=plan_fingerprint,
            )
            await self._update(
                installation_id,
                status=InstallationState.INSTALLED.value,
                server_id=server_id,
                installation_dir=str(installation_dir),
                installed_version=installed_version,
                mcp_config=config,
                installed_at=_now(),
                phase="installed",
                progress=70,
            )

            # Démarrage contrôlé + vérification réelle avant ready.
            await self._update(
                installation_id,
                status=InstallationState.STARTING.value,
                phase="starting",
                progress=85,
            )
            sync = await self._sync(server_id)
            verification = {
                "registered": True,
                "sync_status": sync.get("status"),
                "tools_discovered": sync.get("tools", 0),
                "error": sync.get("error", ""),
                "checked_at": _now(),
            }
            if sync.get("status") != "ok":
                raise McpInstallError(
                    "vérification MCP échouée : " + _tail(str(sync.get("error") or "sync error")),
                    code="MCP-VERIFICATION-FAILED",
                )
            await self._update(
                installation_id,
                status=InstallationState.READY.value,
                sync=sync,
                verification=verification,
                ready_at=_now(),
                phase="ready",
                progress=100,
                error="",
            )
            self._audit(
                AuditDecision.ALLOWED,
                "mcp_installer.ready",
                str((await self._require_record(installation_id)).get("actor") or "unknown"),
                {
                    "installation_id": installation_id,
                    "server_id": server_id,
                    "transport": transport,
                    "version": installed_version,
                    "plan_fingerprint": plan_fingerprint,
                    "sync": sync,
                    "verification": verification,
                },
            )
            replaces = str((await self._require_record(installation_id)).get("replaces") or "")
            if replaces:
                await self._retire_replaced(replaces, installation_id)
        except Exception:
            # Nettoyage best-effort : ne jamais laisser un serveur partiel "ready".
            if server_id:
                try:
                    await self._tool_servers.delete(server_id)
                except Exception:  # noqa: BLE001
                    logger.debug("MCP cleanup: failed to remove server %s", server_id)
            shutil.rmtree(installation_dir, ignore_errors=True)
            raise

    async def _install_npm(
        self, plan: InstallationPlan, directory: Path, *, isolation: Any | None = None
    ) -> tuple[dict[str, Any], str]:
        spec = npm_package_spec(plan)
        mechanism = getattr(isolation, "mechanism", None) or (
            isolation.get("mechanism") if isinstance(isolation, dict) else ""
        )
        if mechanism == "docker":
            backend = self._isolation.backend()
            if backend is None:
                raise McpInstallError(
                    "backend Docker d'installation indisponible", code="MCP-ISOLATION-UNAVAILABLE"
                )
            details = (
                getattr(isolation, "details", None) or {}
                if not isinstance(isolation, dict)
                else (isolation.get("details") or {})
            )
            image = details.get("image")
            if not image:
                image = "node:20-alpine"
            # npm install nécessite un accès réseau (registre) : autorisé uniquement
            # pour cette opération d'installation approuvée. Vérification de source
            # (nom/version package) effectuée en amont ; contrôle egress fin
            # (proxy/allowlist destinations) reste une limite résiduelle documentée.
            result = await asyncio.to_thread(
                backend.run,
                [
                    "npm",
                    "install",
                    "--prefix",
                    "/workspace",
                    "--ignore-scripts",
                    "--no-audit",
                    "--no-fund",
                    "--save-exact",
                    spec,
                ],
                workspace=directory,
                image=str(image),
                network="bridge",
                timeout_seconds=self._install_timeout,
                cpu=os.getenv("ETHAN_MCP_INSTALL_CPU", "1.0"),
                memory=os.getenv("ETHAN_MCP_INSTALL_MEMORY", "1024m"),
                pids_limit=int(os.getenv("ETHAN_MCP_INSTALL_PIDS", "256")),
                writable_workspace=True,
            )
            if result.timed_out or result.returncode != 0:
                msg = _tail(result.stderr) or _tail(result.stdout) or "sortie vide"
                raise McpInstallError(
                    "npm install a échoué : " + msg, code="MCP-NPM-INSTALL"
                )
        else:
            npm = shutil.which("npm")
            node_host = shutil.which("node")
            if not npm or not node_host:
                raise McpInstallError("npm et node sont requis", code="MCP-PREREQUISITE")
            result_cmd = await self._runner(
                [
                    npm,
                    "install",
                    "--prefix",
                    str(directory),
                    "--ignore-scripts",
                    "--no-audit",
                    "--no-fund",
                    "--save-exact",
                    spec,
                ],
                directory,
                self._install_timeout,
            )
            if result_cmd.returncode != 0:
                raise McpInstallError(
                    "npm install a échoué : " + (_tail(result_cmd.stderr) or "sortie vide"),
                    code="MCP-NPM-INSTALL",
                )

        package_dir = directory / "node_modules" / _package_name(spec)
        entry = self._resolve_node_entry(package_dir, plan)
        version = self._read_package_version(package_dir) or plan.resolved_version
        # Le serveur MCP stdio s'exécute ensuite via ToolServerManager/MCPClient.
        # Le chemin absolu de node hôte est requis par la politique stdio Core.
        node = shutil.which("node") or "node"
        command, args = self._node_command(node, entry)
        return make_stdio_config(plan.name, command, args), version

    def _resolve_node_entry(self, package_dir: Path, plan: InstallationPlan) -> Path:
        manifest = package_dir / "package.json"
        if not manifest.exists():
            raise McpInstallError(
                f"package npm introuvable après installation : {package_dir.name}",
                code="MCP-NPM-ENTRY",
            )
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise McpInstallError(f"package.json illisible : {exc}", code="MCP-NPM-ENTRY") from exc
        relative = ""
        bin_field = data.get("bin")
        if isinstance(bin_field, dict) and bin_field:
            preferred = _package_name(str(data.get("name") or plan.name)).rsplit("/", 1)[-1]
            relative = str(bin_field.get(preferred) or next(iter(bin_field.values())))
        elif isinstance(bin_field, str):
            relative = bin_field
        elif plan.analysis and plan.analysis.entry_point:
            relative = plan.analysis.entry_point
        elif data.get("main"):
            relative = str(data["main"])
        if not relative:
            raise McpInstallError(
                "aucun point d'entrée exécutable déclaré par le package",
                code="MCP-NPM-ENTRY",
            )
        entry = (package_dir / relative).resolve()
        if not _is_relative_to(entry, package_dir.resolve()) or not entry.exists():
            raise McpInstallError(
                "point d'entrée hors du package ou inexistant", code="MCP-NPM-ENTRY"
            )
        return entry

    @staticmethod
    def _read_package_version(package_dir: Path) -> str:
        manifest = package_dir / "package.json"
        if not manifest.exists():
            return ""
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return ""
        return str(data.get("version") or "")

    @staticmethod
    def _node_command(node: str, entry: Path) -> tuple[str, list[str]]:
        if entry.suffix.lower() in {".js", ".mjs", ".cjs"}:
            return node, [str(entry)]
        try:
            first_line = entry.read_text(encoding="utf-8", errors="ignore").splitlines()[0]
        except (OSError, IndexError):
            first_line = ""
        if "node" in first_line:
            return node, [str(entry)]
        if os.access(entry, os.X_OK):
            return str(entry), []
        return node, [str(entry)]

    async def _install_github(
        self, plan: InstallationPlan, directory: Path, *, isolation: Any | None = None
    ) -> tuple[dict[str, Any], str]:
        mechanism = getattr(isolation, "mechanism", None) or (
            isolation.get("mechanism") if isinstance(isolation, dict) else ""
        )
        if mechanism == "docker":
            # Clone + installation de dépendances tiers dans un backend isolé
            # nécessitent une image git/runtime adaptée et une politique réseau
            # contrôlée par opération. Non câblé de manière générique/prouvée ici.
            raise McpInstallError(
                "Installation GitHub en backend Docker non disponible pour ce plan "
                "(image git+runtime/egress contrôlé requis). Fail closed.",
                code="MCP-ISOLATION-UNAVAILABLE",
            )
        clone_dir = directory / "repo"
        acquisition = await asyncio.to_thread(acquire_github_repo, plan.source, str(clone_dir))
        if acquisition.get("errors"):
            raise McpInstallError(
                "clone GitHub impossible : " + "; ".join(str(e) for e in acquisition["errors"]),
                code="MCP-GITHUB-CLONE",
            )
        manager = plan.analysis.package_manager if plan.analysis else ""

        if manager == "npm" or (clone_dir / "package.json").exists():
            npm = shutil.which("npm")
            node = shutil.which("node")
            if not npm or not node:
                raise McpInstallError("npm et node sont requis", code="MCP-PREREQUISITE")
            result = await self._runner(
                [npm, "install", "--ignore-scripts", "--no-audit", "--no-fund"],
                clone_dir,
                self._install_timeout,
            )
            if result.returncode != 0:
                raise McpInstallError(
                    "npm install a échoué : " + (_tail(result.stderr) or "sortie vide"),
                    code="MCP-NPM-INSTALL",
                )
            entry = self._resolve_node_entry(clone_dir, plan)
            version = self._read_package_version(clone_dir) or plan.resolved_version
            command, args = self._node_command(node, entry)
            return make_stdio_config(plan.name, command, args), version

        if manager == "pip" or (clone_dir / "pyproject.toml").exists():
            return await self._install_python_repo(plan, directory, clone_dir)

        raise McpInstallError(
            "aucun gestionnaire de packages reconnu (npm ou Python attendu)",
            code="MCP-GITHUB-MANAGER",
        )

    async def _install_python_repo(
        self, plan: InstallationPlan, directory: Path, clone_dir: Path
    ) -> tuple[dict[str, Any], str]:
        python = shutil.which("python3") or shutil.which("python")
        if not python:
            raise McpInstallError("Python 3 est requis", code="MCP-PREREQUISITE")
        venv_dir = directory / "venv"
        created = await self._runner(
            [python, "-m", "venv", str(venv_dir)], directory, self._install_timeout
        )
        if created.returncode != 0:
            raise McpInstallError(
                "création du virtualenv impossible : " + (_tail(created.stderr) or "sortie vide"),
                code="MCP-PYTHON-VENV",
            )
        bin_dir = venv_dir / ("Scripts" if os.name == "nt" else "bin")
        pip = bin_dir / ("pip.exe" if os.name == "nt" else "pip")
        installed = await self._runner(
            [
                str(pip),
                "install",
                "--no-input",
                "--disable-pip-version-check",
                str(clone_dir),
            ],
            directory,
            self._install_timeout,
        )
        if installed.returncode != 0:
            raise McpInstallError(
                "pip install a échoué : " + (_tail(installed.stderr) or "sortie vide"),
                code="MCP-PYTHON-INSTALL",
            )
        entry_name = plan.analysis.entry_point if plan.analysis else ""
        candidates = [bin_dir / entry_name] if entry_name else []
        candidates.extend(
            path
            for path in sorted(bin_dir.iterdir())
            if path.is_file()
            and os.access(path, os.X_OK)
            and not path.name.startswith(("pip", "python", "activate", "wheel"))
        )
        entry = next((path for path in candidates if path.exists()), None)
        if entry is None:
            raise McpInstallError(
                "aucun point d'entrée Python installé dans le virtualenv",
                code="MCP-PYTHON-ENTRY",
            )
        version = plan.resolved_version
        return make_stdio_config(plan.name, str(entry), []), version

    def _install_custom(self, plan: InstallationPlan) -> tuple[dict[str, Any], str]:
        return (
            make_stdio_config(plan.name, plan.execution_command, plan.execution_args),
            plan.resolved_version,
        )

    def _install_remote(self, plan: InstallationPlan) -> tuple[dict[str, Any], str]:
        return make_http_config(plan.name, plan.source), plan.resolved_version

    async def _sync(self, server_id: str) -> dict[str, Any]:
        """Synchronisation best-effort : l'installation reste valide sans elle."""
        try:
            tools = await asyncio.wait_for(
                self._tool_servers.sync_tools(server_id), timeout=self._sync_timeout
            )
        except Exception as exc:  # noqa: BLE001 - état exposé, pas de crash
            logger.info("MCP sync failed for %s: %s", server_id, exc)
            status = "error"
            error = _tail(str(exc))
            return {"status": status, "tools": 0, "error": error}
        return {"status": "ok", "tools": len(tools), "error": ""}

    def _installation_dir(self, plan: InstallationPlan, installation_id: str) -> Path:
        root = self._root.expanduser().resolve()
        suffix = installation_id.rsplit("_", 1)[-1][:8] or uuid4().hex[:8]
        target = (root / f"{slugify(plan.name)}-{suffix}").resolve()
        if not _is_relative_to(target, root) or target == root:
            raise McpInstallError(
                "répertoire d'installation hors de la racine isolée", code="MCP-ISOLATION"
            )
        root.mkdir(parents=True, exist_ok=True)
        return target

    def _write_manifest(
        self,
        directory: Path,
        *,
        installation_id: str,
        plan: InstallationPlan,
        server: dict[str, Any],
        installed_version: str,
        config: dict[str, Any],
        plan_fingerprint: str = "",
    ) -> None:
        manifest = {
            "installation_id": installation_id,
            "source": plan.source,
            "name": plan.name,
            "source_type": plan.source_type.value,
            "runtime": plan.runtime.value,
            "requested_version": plan.resolved_version,
            "installed_version": installed_version,
            "installed_at": _now(),
            "server_id": server.get("id"),
            "transport": config.get("transport"),
            "command": config.get("metadata", {}).get("command"),
            "args": config.get("metadata", {}).get("args", []),
            "dependencies": plan.dependencies,
            "plan_fingerprint": plan_fingerprint,
        }
        (directory / ".ethan-mcp-install.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
        )

    async def _retire_replaced(self, old_id: str, new_id: str) -> None:
        old = await self._store.get(self._INSTALLATIONS, old_id)
        if old is None or old.get("status") == InstallationState.REMOVED.value:
            return
        server_id = old.get("server_id")
        if server_id:
            await self._tool_servers.delete(str(server_id))
        self._remove_directory(str(old.get("installation_dir") or ""))
        await self._update(
            old_id,
            status=InstallationState.REMOVED.value,
            replaced_by=new_id,
            removed_at=_now(),
        )

    # ── Lifecycle ──────────────────────────────────────────────────

    async def list(self, *, include_removed: bool = False) -> list[dict[str, Any]]:
        records = await self._store.list(self._INSTALLATIONS)
        if not include_removed:
            records = [
                record
                for record in records
                if record.get("status")
                not in {InstallationState.REMOVED.value, InstallationState.UNINSTALLED.value}
            ]
        return [self._public(record) for record in records]

    async def get(self, installation_id: str) -> dict[str, Any] | None:
        record = await self._store.get(self._INSTALLATIONS, installation_id)
        return self._public(record) if record else None

    async def wait(self, installation_id: str, timeout: float = 30.0) -> dict[str, Any] | None:
        """Attend la fin de la tâche en cours (tests, CLI, diagnostic)."""
        task = self._tasks.get(installation_id)
        if task is not None:
            try:
                await asyncio.wait_for(asyncio.shield(task), timeout=timeout)
            except TimeoutError:
                pass
        return await self.get(installation_id)

    async def uninstall(self, installation_id: str, *, actor: str) -> dict[str, Any]:
        record = await self._require_record(installation_id)
        state = str(record.get("status") or "")
        if state in {InstallationState.REMOVED.value, InstallationState.UNINSTALLED.value}:
            return self._public(record)
        if state in {InstallationState.INSTALLING.value, InstallationState.STARTING.value}:
            raise McpInstallError(
                "opération en cours : annulez puis réessayez la désinstallation",
                code="MCP-BUSY",
            )
        await self._update(
            installation_id,
            status=InstallationState.UNINSTALLING.value,
            phase="uninstalling",
            progress=90,
        )
        task = self._tasks.get(installation_id)
        if task is not None and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)

        server_id = record.get("server_id")
        if server_id and await self._tool_servers.get(str(server_id)) is not None:
            await self._tool_servers.delete(str(server_id))
        self._remove_directory(str(record.get("installation_dir") or ""))
        updated = await self._update(
            installation_id,
            status=InstallationState.UNINSTALLED.value,
            server_id=None,
            removed_at=_now(),
            phase="uninstalled",
            progress=100,
        )
        self._audit(
            AuditDecision.ALLOWED,
            "mcp_installer.uninstalled",
            actor,
            {"installation_id": installation_id, "server_id": server_id},
        )
        return self._public(updated)

    async def check_update(self, installation_id: str) -> dict[str, Any]:
        record = await self._require_record(installation_id)
        plan = InstallationPlan.from_dict(record.get("plan") or {})
        current = str(record.get("installed_version") or plan.resolved_version or "")
        if plan.source_type not in (SourceType.NPM_COMMAND, SourceType.NPM_PACKAGE):
            return {
                "available": None,
                "current": current,
                "latest": None,
                "reason": "type de source sans vérification automatique",
            }
        spec = npm_package_spec(plan)
        info = await asyncio.to_thread(acquire_npm_info, _package_name(spec))
        if info.get("errors"):
            return {
                "available": None,
                "current": current,
                "latest": None,
                "error": _tail("; ".join(str(e) for e in info["errors"])),
            }
        latest = str(info.get("version") or "")
        return {
            "available": bool(latest and current and latest != current),
            "current": current,
            "latest": latest,
            "reason": "",
        }

    async def request_update(
        self, installation_id: str, *, actor: str, confirmed_mcp: bool = True
    ) -> dict[str, Any]:
        record = await self._require_record(installation_id)
        plan = InstallationPlan.from_dict(record.get("plan") or {})
        return await self.request_install(
            actor=actor,
            source=plan.source,
            confirmed_mcp=confirmed_mcp or bool(record.get("is_mcp_server")),
            replaces=installation_id,
        )

    async def cancel(self, installation_id: str) -> dict[str, Any]:
        record = await self._require_record(installation_id)
        state = str(record.get("status") or "")
        if state in _TERMINAL_STATES:
            return self._public(record)
        # L'annulation sûre est garantie avant exécution effective (pending/approved).
        task = self._tasks.get(installation_id)
        if state in {InstallationState.PENDING_APPROVAL.value, InstallationState.APPROVED.value}:
            if task is not None and not task.done():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
            # Annule aussi la demande HROT si connue.
            req_id = str(record.get("approval_request_id") or "")
            if req_id:
                try:
                    self._approval.cancel(req_id, "cancelled by operator")
                except Exception:  # noqa: BLE001
                    pass
            updated = await self._update(
                installation_id,
                status=InstallationState.CANCELLED.value,
                error="installation annulée",
                phase="cancelled",
                progress=100,
            )
            return self._public(updated)
        # Après démarrage des opérations d'installation/vérification, l'annulation
        # n'est pas sûre (état potentiellement partiel) : on refuse explicitement.
        raise McpInstallError(
            "annulation non sûre après démarrage de l'installation/vérification",
            code="MCP-CANCEL-UNSAFE",
        )

    async def shutdown(self) -> None:
        for task in list(self._tasks.values()):
            if not task.done():
                task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks.values(), return_exceptions=True)
        self._tasks.clear()

    # ── Helpers records ────────────────────────────────────────────

    async def _require_record(self, installation_id: str) -> dict[str, Any]:
        record = await self._store.get(self._INSTALLATIONS, installation_id)
        if record is None:
            raise McpInstallError(
                f"installation inconnue : {installation_id}", code="MCP-NOT-FOUND"
            )
        return record

    async def _update(self, installation_id: str, **fields: Any) -> dict[str, Any]:
        async with self._lock:
            record = await self._require_record(installation_id)
            record.update(fields)
            record["updated_at"] = _now()
            await self._store.save(self._INSTALLATIONS, installation_id, record)
            return record

    @staticmethod
    def _public(record: dict[str, Any]) -> dict[str, Any]:
        """Record exposable : aucun secret n'y est stocké par construction."""
        return dict(record)

    def _remove_directory(self, raw_path: str) -> None:
        if not raw_path:
            return
        root = self._root.expanduser().resolve()
        target = Path(raw_path).expanduser().resolve()
        if target == root or not _is_relative_to(target, root):
            logger.warning("Refusing to remove directory outside MCP install root: %s", target)
            return
        shutil.rmtree(target, ignore_errors=True)

    def _audit(
        self, decision: AuditDecision, action: str, actor: str, details: dict[str, Any]
    ) -> None:
        if self._audit_store is None:
            return
        try:
            self._audit_store.log(
                AuditCategory.PLUGIN,
                decision,
                action=action,
                actor=actor or "unknown",
                source="mcp_installer",
                details=details,
            )
        except Exception as exc:  # noqa: BLE001 - l'audit ne casse pas l'installation
            logger.debug("MCP installer audit failed: %s", exc)


__all__ = [
    "CommandResult",
    "InstallationState",
    "McpInstallError",
    "McpInstaller",
]
