"""Backends d'isolation d'installation MCP (exécution contrôlée de code tiers).

Le backend fournit un environnement éphémère et exécute des commandes
d'installation/acquisition à l'intérieur, jamais sur l'hôte. L'orchestrateur
(Core) pilote Docker/CLI côté hôte ; le payload tiers ne reçoit jamais l'accès
Docker et ne voit que les montages explicitement autorisés.
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

logger = logging.getLogger(__name__)

_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9_.-]+")


class IsolationBackendError(RuntimeError):
    """Erreur du backend d'isolation (indisponible ou exécution refusée/échouée)."""

    def __init__(self, message: str, *, code: str = "MCP-ISOLATION-BACKEND") -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class IsolatedCommandResult:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False
    diagnostics: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BackendProbe:
    available: bool
    effective: bool
    mechanism: str
    reason: str
    details: dict[str, Any] = field(default_factory=dict)


class IsolationBackend(Protocol):
    mechanism: str

    def probe(self) -> BackendProbe: ...

    def run(
        self,
        argv: list[str],
        *,
        workspace: Path,
        image: str,
        network: str = "none",
        timeout_seconds: int = 600,
        cpu: str = "1.0",
        memory: str = "1024m",
        pids_limit: int = 256,
        writable_workspace: bool = True,
        extra_readonly_mounts: dict[str, str] | None = None,
        env: dict[str, str] | None = None,
        workdir: str = "/workspace",
    ) -> IsolatedCommandResult: ...


def _safe_container_name(prefix: str) -> str:
    slug = _SAFE_NAME_RE.sub("-", prefix).strip("-.") or "mcp-install"
    return f"ethan-{slug[:30]}-{uuid.uuid4().hex[:8]}"


def _truncate(text: str, limit: int = 8000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...[truncated]"


class DockerInstallIsolationBackend:
    """Backend Docker durci pour opérations d'installation/acquisition.

    L'accès Docker (CLI/socket côté hôte) n'est JAMAIS monté dans le conteneur.
    """

    mechanism = "docker"

    def __init__(
        self,
        *,
        docker_bin: str | None = None,
        require_seccomp: bool = False,
    ) -> None:
        self._docker = docker_bin or shutil.which("docker") or "docker"
        self._require_seccomp = require_seccomp

    def _run_host(self, argv: list[str], timeout: int = 30) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

    def probe(self) -> BackendProbe:
        if not shutil.which(self._docker):
            return BackendProbe(False, False, self.mechanism, "CLI Docker introuvable", {})
        try:
            proc = self._run_host([self._docker, "info", "--format", "{{json .}}"], timeout=20)
        except Exception as exc:  # noqa: BLE001
            return BackendProbe(False, False, self.mechanism, f"Docker indisponible: {exc}", {})
        if proc.returncode != 0:
            msg = _truncate((proc.stderr or proc.stdout or "").strip())
            return BackendProbe(False, False, self.mechanism, f"Docker non opérationnel: {msg}", {})
        try:
            info = json.loads(proc.stdout or "{}")
        except json.JSONDecodeError:
            info = {}
        security = info.get("SecurityOptions") or []
        details = {
            "cgroup_driver": info.get("CgroupDriver"),
            "security_options": security,
            "server_version": info.get("ServerVersion"),
            "rootless": info.get("Rootless"),
        }
        # Capacité minimale : exécution conteneur possible. Les garanties complètes
        # (userns/seccomp profile spécifique/quotas disque natifs) dépendent de la
        # configuration hôte ; on les expose dans details/diagnostics.
        return BackendProbe(
            available=True,
            effective=True,
            mechanism=self.mechanism,
            reason="Backend Docker disponible (exécution conteneur durcie).",
            details=details,
        )

    def ensure_image(self, image: str) -> None:
        proc = self._run_host([self._docker, "image", "inspect", image], timeout=20)
        if proc.returncode != 0:
            raise IsolationBackendError(
                f"Image Docker requise indisponible localement: {image}",
                code="MCP-ISOLATION-IMAGE",
            )

    def run(
        self,
        argv: list[str],
        *,
        workspace: Path,
        image: str,
        network: str = "none",
        timeout_seconds: int = 600,
        cpu: str = "1.0",
        memory: str = "1024m",
        pids_limit: int = 256,
        writable_workspace: bool = True,
        extra_readonly_mounts: dict[str, str] | None = None,
        env: dict[str, str] | None = None,
        workdir: str = "/workspace",
    ) -> IsolatedCommandResult:
        if not argv or any(not isinstance(a, str) for a in argv):
            raise IsolationBackendError("argv invalide", code="MCP-ISOLATION-ARGV")
        if network not in {"none", "bridge"}:
            # Réseau custom non autorisé sans validation explicite supplémentaire.
            raise IsolationBackendError(
                f"mode réseau non autorisé: {network}", code="MCP-ISOLATION-NETWORK"
            )
        self.ensure_image(image)
        workspace = workspace.resolve()
        workspace.mkdir(parents=True, exist_ok=True)
        container_name = _safe_container_name("mcp-install")
        uid = os.getuid()
        gid = os.getgid()

        docker_cmd: list[str] = [
            self._docker,
            "run",
            "--name",
            container_name,
            "--rm",
            "--init",
            "--user",
            f"{uid}:{gid}",
            "--cap-drop=ALL",
            "--security-opt",
            "no-new-privileges:true",
            "--pids-limit",
            str(int(pids_limit)),
            "--cpus",
            str(cpu),
            "--memory",
            str(memory),
            "--memory-swap",
            str(memory),
            "--ipc",
            "none",
            "--read-only",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=256m",
            "--network",
            network,
            "--workdir",
            workdir,
        ]
        # IMPORTANT: ne jamais monter /var/run/docker.sock ni le home/hôte.
        mount_mode = "rw" if writable_workspace else "ro"
        docker_cmd += ["-v", f"{workspace}:/workspace:{mount_mode}"]
        for host_path, container_path in (extra_readonly_mounts or {}).items():
            hp = Path(host_path).resolve()
            if not hp.exists():
                continue
            docker_cmd += ["-v", f"{hp}:{container_path}:ro"]

        safe_env = {
            "HOME": "/tmp/home",
            "TMPDIR": "/tmp",
            "CI": "1",
            "npm_config_cache": "/tmp/npm-cache",
            "npm_config_audit": "false",
            "npm_config_fund": "false",
            "npm_config_update_notifier": "false",
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        }
        if env:
            # N'accepte que des clés/valeurs simples non secrètes explicitement fournies.
            for k, v in env.items():
                if isinstance(k, str) and isinstance(v, str):
                    safe_env[k] = v
        for k, v in safe_env.items():
            docker_cmd += ["-e", f"{k}={v}"]

        docker_cmd += [image, *argv]

        timed_out = False
        diagnostics: dict[str, Any] = {
            "backend": self.mechanism,
            "image": image,
            "network": network,
            "container_name": container_name,
            "limits": {"cpu": cpu, "memory": memory, "pids_limit": pids_limit},
            "workspace_mount": "/workspace",
            "docker_socket_mounted": False,
        }
        try:
            proc = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
            rc = proc.returncode
            stdout = proc.stdout or ""
            stderr = proc.stderr or ""
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            rc = 124
            stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
            stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
            # Best-effort kill/cleanup
            try:
                self._run_host([self._docker, "kill", container_name], timeout=15)
            except Exception:  # noqa: BLE001
                pass
            try:
                self._run_host([self._docker, "rm", "-f", container_name], timeout=15)
            except Exception:  # noqa: BLE001
                pass
            diagnostics["cleanup"] = "attempted_after_timeout"
        except Exception as exc:  # noqa: BLE001
            raise IsolationBackendError(
                f"Échec d'exécution dans le backend Docker: {exc}",
                code="MCP-ISOLATION-RUN",
            ) from exc

        diagnostics["timed_out"] = timed_out
        return IsolatedCommandResult(
            returncode=rc,
            stdout=_truncate(stdout),
            stderr=_truncate(stderr),
            timed_out=timed_out,
            diagnostics=diagnostics,
        )


def default_install_backend() -> DockerInstallIsolationBackend | None:
    if shutil.which("docker"):
        return DockerInstallIsolationBackend()
    return None
