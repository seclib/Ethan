"""God's Eye View / Odin Service Manager (Core layer).

Contrôle sécurisé du cycle de vie du plugin applicatif God's Eye View / Odin :
- Détecte l'état réel du conteneur Docker et la disponibilité du port local.
- Détecte les conflits de ports (évite les collisions sur 4173).
- Exécute STRICTEMENT des opérations figées (start, stop, restart, status, logs, health).
- Aucune commande Docker arbitraire n'est acceptée.
- Confinement strict au fichier compose sous examples/gods-eye-view ou examples/odin.
- Support du renommage transparent en Odin sans régression.
- Redaction automatique des secrets dans les logs.
- Aucun démarrage automatique non sollicité au boot d'ETHAN.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import shutil
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.hardware.ports import is_port_in_use

logger = logging.getLogger(__name__)

# États standardisés du service
STATE_STOPPED = "stopped"
STATE_STARTING = "starting"
STATE_ACTIVE = "active"
STATE_STOPPING = "stopping"
STATE_ERROR = "error"

DEFAULT_PORT = 4173
DEFAULT_HOST = "127.0.0.1"

_SECRET_PATTERN = re.compile(
    r"(?i)\b(api[_-]?key|token|secret|password|passwd|authorization)\b\s*[:=]\s*([^\s,;]+)"
)
_BEARER_PATTERN = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]+=*")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _redact_secrets(text: str) -> str:
    """Anonymise les tokens et secrets dans les logs et sorties d'erreur."""
    if not text:
        return ""
    redacted = _SECRET_PATTERN.sub(r"\1=***", text)
    redacted = _BEARER_PATTERN.sub("Bearer ***", redacted)
    return redacted


def _resolve_default_repo() -> Path:
    """Résout le chemin du dépôt en vérifiant la présence réelle d'odin ou gods-eye-view."""
    ethan_root = Path(__file__).resolve().parent.parent.parent
    for candidate_name in ("odin", "gods-eye-view"):
        candidate = ethan_root / "examples" / candidate_name
        if candidate.is_dir() and (candidate / "compose.yaml").is_file():
            return candidate.resolve()
    return (ethan_root / "examples" / "gods-eye-view").resolve()


class GodsEyeViewService:
    """Gestionnaire de cycle de vie du service Docker God's Eye View / Odin."""

    def __init__(
        self,
        repo_dir: Path | None = None,
        port: int = DEFAULT_PORT,
        host: str = DEFAULT_HOST,
        docker_cmd: str = "docker",
    ) -> None:
        if repo_dir is None:
            self._repo_dir = _resolve_default_repo()
        else:
            self._repo_dir = Path(repo_dir).resolve()

        self._compose_file = self._repo_dir / "compose.yaml"
        self._port = port
        self._host = host
        self._docker_cmd = docker_cmd
        self._lock = asyncio.Lock()
        self._state: str = STATE_STOPPED
        self._last_error: str | None = None
        self._last_updated: str = _now()
        self._cached_container_id: str | None = None

        # Validation de confinement
        self._validate_confinement()

    @property
    def repo_dir(self) -> Path:
        return self._repo_dir

    @property
    def compose_file(self) -> Path:
        return self._compose_file

    @property
    def port(self) -> int:
        return self._port

    @property
    def host(self) -> str:
        return self._host

    @property
    def state(self) -> str:
        return self._state

    def _validate_confinement(self) -> None:
        """Vérifie que le chemin du compose est valide et confiné.

        Confinement strict : le compose doit être exactement
        ``examples/gods-eye-view/compose.yaml`` ou ``examples/odin/compose.yaml``
        sous la racine ETHAN. Tout autre chemin est refusé (fail-closed).
        """
        try:
            ethan_root = Path(__file__).resolve().parent.parent.parent
            allowed_repos = {
                (ethan_root / "examples" / "gods-eye-view").resolve(),
                (ethan_root / "examples" / "odin").resolve(),
            }
            repo = self._repo_dir.resolve()
            if repo not in allowed_repos:
                raise ValueError(f"chemin GEV/Odin hors allowlist : {repo}")
            compose = (repo / "compose.yaml").resolve()
            if compose != (repo / "compose.yaml").resolve():
                raise ValueError(f"fichier compose invalide : {compose}")
        except ValueError:
            raise
        except Exception as exc:
            logger.warning("Validation confinement GEV/Odin impossible : %s", exc)

        if not self._compose_file.is_file():
            logger.warning(
                "Le fichier compose %s n'a pas été trouvé", self._compose_file
            )

    def get_metadata(self) -> dict[str, str]:
        """Lit les métadonnées réelles du dépôt (nom, package, description, version)."""
        pkg_file = Path(self._repo_dir) / "package.json"
        name = "God's Eye View"
        pkg_name = "gods-eye-view"
        desc = "Console géospatiale 3D et fusion multi-sources — conteneur local piloté via l'API ETHAN."
        version = "0.2.1"
        if pkg_file.is_file():
            try:
                data = json.loads(pkg_file.read_text(encoding="utf-8"))
                raw_pkg = str(data.get("name", "")).strip()
                if raw_pkg:
                    pkg_name = raw_pkg
                    if raw_pkg.lower() == "odin":
                        name = "Odin"
                raw_desc = str(data.get("description", "")).strip()
                if raw_desc:
                    desc = raw_desc
                raw_ver = str(data.get("version", "")).strip()
                if raw_ver:
                    version = raw_ver
            except Exception as exc:
                logger.debug("Lecture metadata package.json échouée : %s", exc)
        return {
            "name": name,
            "package_name": pkg_name,
            "description": desc,
            "version": version,
        }

    def _is_allowed_docker_args(self, args: list[str]) -> bool:
        """Allowlist stricte des arguments docker compose."""
        t = tuple(args)
        if t in {("up", "-d"), ("stop",), ("restart",), ("ps", "--format", "json")}:
            return True
        if len(args) == 3 and args[0] == "logs" and args[1].startswith("--tail=") and args[2] == "--no-color":
            tail_str = args[1].split("=", 1)[1]
            return tail_str.isdigit() and 1 <= int(tail_str) <= 500
        return False

    async def _run_docker(self, args: list[str], timeout: float = 60.0) -> tuple[bool, str]:
        """Exécute une commande Docker figée sans shell=True."""
        if not self._is_allowed_docker_args(args):
            raise ValueError(f"commande Docker non autorisée : {args}")

        # Re-valide le confinement à chaque appel (TOCTOU minimal).
        self._validate_confinement()
        binary = shutil.which(self._docker_cmd) or self._docker_cmd
        argv = [binary, "compose", "-f", str(self._compose_file), *args]

        env = os.environ.copy()
        env.setdefault("UID", str(os.getuid() if hasattr(os, "getuid") else 1000))
        env.setdefault("GID", str(os.getgid() if hasattr(os, "getgid") else 1000))

        try:
            proc = await asyncio.create_subprocess_exec(
                *argv,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self._repo_dir),
                env=env,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            out_str = stdout.decode(errors="replace").strip()
            err_str = stderr.decode(errors="replace").strip()
            combined = f"{out_str}\n{err_str}".strip()
            return proc.returncode == 0, _redact_secrets(combined)
        except asyncio.TimeoutError:
            return False, f"Timeout ({timeout}s) dépassé lors de l'exécution de: {' '.join(argv)}"
        except Exception as exc:
            return False, _redact_secrets(f"Erreur d'exécution: {exc}")

    def check_health(self) -> bool:
        """Vérifie la disponibilité HTTP / TCP de l'endpoint local."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                s.connect((self._host, self._port))
                return True
        except (ConnectionRefusedError, socket.timeout, OSError):
            return False

    async def _inspect_container(self) -> dict[str, Any] | None:
        """Interroge l'état du conteneur via docker compose ps."""
        ok, out = await self._run_docker(["ps", "--format", "json"], timeout=10.0)
        if not ok or not out.strip():
            return None

        # docker compose ps --format json retourne un ou plusieurs objets JSON
        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if isinstance(data, list) and data:
                    return data[0]
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                continue
        return None

    async def get_health(self) -> dict[str, Any]:
        """Vérification approfondie de l'état de santé du service."""
        is_healthy = self.check_health()
        container_info = await self._inspect_container()
        container_state = str(container_info.get("State", "")).lower() if container_info else "none"

        status_str = "healthy" if is_healthy else ("degraded" if container_state in ("running", "up") else "unreachable")
        return {
            "status": status_str,
            "healthy": is_healthy,
            "reachable": is_healthy,
            "tcp_probe": is_healthy,
            "container_state": container_state,
            "port": self._port,
            "host": self._host,
            "url": f"http://{self._host}:{self._port}",
            "last_transition": self._last_updated,
            "checked_at": _now(),
        }

    async def get_logs(self, tail: int = 100) -> dict[str, Any]:
        """Consulte les logs récents du service avec anonymisation des données sensibles."""
        safe_tail = max(1, min(int(tail), 500))
        ok, out = await self._run_docker(["logs", f"--tail={safe_tail}", "--no-color"], timeout=15.0)

        cleaned = _redact_secrets(out)
        lines = [line for line in cleaned.splitlines() if line.strip()]

        return {
            "status": "ok" if ok else "error",
            "logs": cleaned,
            "total_lines": len(lines),
            "redacted": True,
            "fetched_at": _now(),
            "error": None if ok else cleaned,
        }

    async def get_status(self) -> dict[str, Any]:
        """Retourne l'état réel et vérifié du service."""
        # Si une transition est en cours, retourner l'état intermédiaire
        if self._state in (STATE_STARTING, STATE_STOPPING):
            return self._build_status_dict(
                state=self._state,
                healthy=False,
                container_id=self._cached_container_id,
            )

        container_info = await self._inspect_container()
        port_busy = is_port_in_use(self._port, host=self._host)

        if container_info:
            c_state = str(container_info.get("State", "")).lower()
            c_name = container_info.get("Name") or container_info.get("Service")
            self._cached_container_id = c_name

            if c_state in ("running", "up"):
                is_healthy = self.check_health()
                new_state = STATE_ACTIVE if is_healthy or port_busy else STATE_STARTING
                self._state = new_state
                self._last_error = None
                return self._build_status_dict(
                    state=new_state,
                    healthy=is_healthy,
                    container_id=c_name,
                    container_info=container_info,
                )
            elif c_state in ("exited", "stopped", "dead"):
                self._state = STATE_STOPPED
                return self._build_status_dict(
                    state=STATE_STOPPED,
                    healthy=False,
                    container_id=c_name,
                    container_info=container_info,
                )

        # Si le conteneur n'est pas vu par compose mais que le port est occupé
        if port_busy:
            is_healthy = self.check_health()
            if is_healthy:
                self._state = STATE_ACTIVE
                return self._build_status_dict(
                    state=STATE_ACTIVE,
                    healthy=True,
                    container_id=self._cached_container_id or "gods-eye-view-1",
                )
            else:
                self._state = STATE_ERROR
                self._last_error = (
                    f"Conflit de port : le port {self._port} est déjà utilisé "
                    "par un autre processus."
                )
                return self._build_status_dict(
                    state=STATE_ERROR,
                    healthy=False,
                    error=self._last_error,
                )

        # Non démarré
        self._state = STATE_STOPPED
        return self._build_status_dict(state=STATE_STOPPED, healthy=False)

    async def start(self) -> dict[str, Any]:
        """Démarre le service via docker compose up -d."""
        async with self._lock:
            # 1. Vérifier si déjà actif
            curr = await self.get_status()
            if curr["status"] == STATE_ACTIVE:
                return curr

            # 2. Vérifier les conflits de port avec un tiers
            if is_port_in_use(self._port, host=self._host):
                if not self.check_health():
                    self._state = STATE_ERROR
                    self._last_error = (
                        f"Impossible de démarrer : le port {self._port} "
                        "est déjà utilisé par une autre application."
                    )
                    self._last_updated = _now()
                    return self._build_status_dict(
                        state=STATE_ERROR,
                        healthy=False,
                        error=self._last_error,
                    )

            # 3. Marquer le démarrage
            self._state = STATE_STARTING
            self._last_error = None
            self._last_updated = _now()

            # 4. Exécuter docker compose up -d
            ok, out = await self._run_docker(["up", "-d"], timeout=120.0)
            if not ok:
                self._state = STATE_ERROR
                self._last_error = f"Échec du démarrage Docker Compose : {out[-400:]}"
                self._last_updated = _now()
                return self._build_status_dict(
                    state=STATE_ERROR,
                    healthy=False,
                    error=self._last_error,
                )

            # 5. Attendre la disponibilité réseau (polling 2s, timeout 60s)
            healthy = False
            for _ in range(30):
                await asyncio.sleep(2.0)
                if self.check_health():
                    healthy = True
                    break

            self._state = STATE_ACTIVE if healthy else STATE_STARTING
            self._last_updated = _now()
            return await self.get_status()

    async def stop(self) -> dict[str, Any]:
        """Arrête le service sans supprimer les volumes ni les données."""
        async with self._lock:
            self._state = STATE_STOPPING
            self._last_updated = _now()

            ok, out = await self._run_docker(["stop"], timeout=60.0)
            if not ok:
                self._state = STATE_ERROR
                self._last_error = f"Échec de l'arrêt Docker Compose : {out[-400:]}"
                self._last_updated = _now()
                return self._build_status_dict(
                    state=STATE_ERROR,
                    healthy=False,
                    error=self._last_error,
                )

            self._state = STATE_STOPPED
            self._last_error = None
            self._last_updated = _now()
            return self._build_status_dict(state=STATE_STOPPED, healthy=False)

    async def restart(self) -> dict[str, Any]:
        """Redémarre le conteneur du service."""
        async with self._lock:
            self._state = STATE_STARTING
            self._last_updated = _now()

            ok, out = await self._run_docker(["restart"], timeout=60.0)
            if not ok:
                self._state = STATE_ERROR
                self._last_error = f"Échec du redémarrage Docker Compose : {out[-400:]}"
                self._last_updated = _now()
                return self._build_status_dict(
                    state=STATE_ERROR,
                    healthy=False,
                    error=self._last_error,
                )

            healthy = False
            for _ in range(15):
                await asyncio.sleep(1.0)
                if self.check_health():
                    healthy = True
                    break

            self._state = STATE_ACTIVE if healthy else STATE_STARTING
            self._last_updated = _now()
            return await self.get_status()

    def _build_status_dict(
        self,
        state: str,
        healthy: bool,
        container_id: str | None = None,
        container_info: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        meta = self.get_metadata()
        allowed_actions = []
        if state == STATE_STOPPED:
            allowed_actions = ["start"]
        elif state == STATE_ACTIVE:
            allowed_actions = ["stop", "restart"]
            if healthy:
                allowed_actions.append("open")
        elif state == STATE_ERROR:
            allowed_actions = ["start", "restart"]
        elif state in (STATE_STARTING, STATE_STOPPING):
            allowed_actions = []

        return {
            "id": "gods-eye-view",
            "name": meta["name"],
            "package_name": meta["package_name"],
            "description": meta["description"],
            "version": meta["version"],
            "status": state,
            "port": self._port,
            "host": self._host,
            "url": f"http://{self._host}:{self._port}",
            "container_id": container_id or self._cached_container_id,
            "healthy": healthy,
            "mcp_tools_count": 35,
            "error": error or self._last_error,
            "updated_at": self._last_updated,
            "last_transition": self._last_updated,
            "allowed_actions": allowed_actions,
            "details": {
                "compose_file": str(self._compose_file),
                "repo_dir": str(self._repo_dir),
                "container_info": container_info or {},
            },
        }


# Singleton Core
_gev_service: GodsEyeViewService | None = None


def get_gods_eye_view_service() -> GodsEyeViewService:
    global _gev_service
    if _gev_service is None:
        _gev_service = GodsEyeViewService()
    return _gev_service


def set_gods_eye_view_service(service: GodsEyeViewService | None) -> None:
    global _gev_service
    _gev_service = service


__all__ = [
    "STATE_ACTIVE",
    "STATE_ERROR",
    "STATE_STARTING",
    "STATE_STOPPED",
    "STATE_STOPPING",
    "GodsEyeViewService",
    "get_gods_eye_view_service",
    "set_gods_eye_view_service",
]
