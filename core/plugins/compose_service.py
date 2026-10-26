"""Compose Service — classe de base générique pour les intégrations Docker Compose.

Extrait des conventions établies par Odin (core/plugins/odin.py) pour
constituer le contrat d'intégration standard de ETHAN.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import shutil
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.hardware.ports import is_port_in_use

logger = logging.getLogger(__name__)

# ── États standardisés du cycle de vie ──────────────────────────────────

STATE_NOT_INSTALLED = "not_installed"
STATE_STOPPED = "installed_stopped"
STATE_STARTING = "starting"
STATE_ACTIVE = "running"
STATE_DEGRADED = "degraded"
STATE_STOPPING = "stopping"
STATE_ERROR = "error"
STATE_UNKNOWN = "unknown"

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


# ── Commandes docker compose autorisées (figées) ────────────────────────

_ALLOWED_VERBS = {
    ("up", "-d"),
    ("down",),
    ("stop",),
    ("restart",),
    ("ps", "--all", "--format", "json"),
    ("config",),
    ("probe",),
}


def is_allowed_compose_args(args: list[str]) -> bool:
    """Vérifie qu'une liste d'arguments docker compose figure dans l'allowlist."""
    t = tuple(args)
    if t in _ALLOWED_VERBS:
        return True
    if (
        len(args) == 3
        and args[0] == "logs"
        and args[1].startswith("--tail=")
        and args[2] == "--no-color"
    ):
        tail_str = args[1].split("=", 1)[1]
        return tail_str.isdigit() and 1 <= int(tail_str) <= 500
    return False


class ComposeService:
    """Gestionnaire générique de cycle de vie pour un service Docker Compose.

    Paramètres :
    - project_name : nom du projet Compose (ex: "odin")
    - repo_dir : répertoire canonique du dépôt
    - compose_file : chemin du fichier compose (défaut: repo_dir/compose.yaml)
    - port : port HTTP exposé par le service
    - host : host pour les sondes de santé
    - docker_cmd : binaire docker (défaut: "docker")
    - allowed_verbs : allowlist additionnelle de commandes autorisées
    """

    def __init__(
        self,
        project_name: str,
        repo_dir: Path | str,
        compose_file: Path | str | None = None,
        port: int = DEFAULT_PORT,
        host: str = DEFAULT_HOST,
        docker_cmd: str = "docker",
        allowed_verbs: set[tuple[str, ...]] | None = None,
    ) -> None:
        self._project_name = project_name
        self._repo_dir = Path(repo_dir).resolve()
        self._compose_file = (
            Path(compose_file).resolve()
            if compose_file is not None
            else (self._repo_dir / "compose.yaml")
        )
        self._port = port
        self._host = host
        self._docker_cmd = docker_cmd
        self._lock = asyncio.Lock()
        self._state: str = STATE_UNKNOWN
        self._last_error: str | None = None
        self._last_updated: str = _now()
        self._cached_container_id: str | None = None
        self._allowed_verbs = allowed_verbs or set(_ALLOWED_VERBS)

        # Validation de confinement : le compose doit être dans le dépôt
        self._validate_confinement()

    # ── Propriétés publiques ────────────────────────────────────────────

    @property
    def project_name(self) -> str:
        return self._project_name

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

    # ── Confinement ─────────────────────────────────────────────────────

    def _validate_confinement(self) -> None:
        """Vérifie que le compose est contenu dans le dépôt canonique.

        Fail-closed : tout chemin en dehors du dépôt est refusé.
        """
        try:
            repo = self._repo_dir.resolve()
            compose = self._compose_file.resolve()
            expected_compose = repo / "compose.yaml"
            # Le compose doit être exactement <repo>/compose.yaml
            if compose != expected_compose:
                raise ValueError(
                    f"fichier compose hors confinement : {compose} != {expected_compose}"
                )
        except ValueError:
            raise
        except Exception as exc:
            logger.warning(
                "Validation confinement impossible : %s", exc
            )

        if not self._compose_file.is_file():
            logger.warning(
                "Le fichier compose %s n'a pas été trouvé", self._compose_file
            )

    # ── Métadonnées ─────────────────────────────────────────────────────

    def get_metadata(self) -> dict[str, str]:
        """Lit les métadonnées depuis package.json s'il existe."""
        pkg_file = Path(self._repo_dir) / "package.json"
        name = self._project_name
        pkg_name = self._project_name
        desc = f"Service {self._project_name} piloté via l'API ETHAN."
        version = "0.0.1"
        if pkg_file.is_file():
            try:
                data = json.loads(pkg_file.read_text(encoding="utf-8"))
                raw_pkg = str(data.get("name", "")).strip()
                if raw_pkg:
                    pkg_name = raw_pkg
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


    # ── Exécution Docker Compose ────────────────────────────────────────

    def _is_allowed_docker_args(self, args: list[str]) -> bool:
        return is_allowed_compose_args(args) or tuple(args) in self._allowed_verbs

    async def _run_docker(
        self, args: list[str], timeout: float = 60.0
    ) -> tuple[bool, str]:
        """Exécute une commande Docker Compose figée sans shell=True."""
        if not self._is_allowed_docker_args(args):
            raise ValueError(f"commande Docker non autorisée : {args}")

        # Re-valide le confinement à chaque appel (TOCTOU minimal).
        self._validate_confinement()

        binary = shutil.which(self._docker_cmd) or self._docker_cmd
        argv = [
            binary,
            "compose",
            "--project-name",
            self._project_name,
            "-f",
            str(self._compose_file),
            *args,
        ]

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
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
            out_str = stdout.decode(errors="replace").strip()
            err_str = stderr.decode(errors="replace").strip()
            combined = f"{out_str}\n{err_str}".strip()
            return proc.returncode == 0, _redact_secrets(combined)
        except asyncio.TimeoutError:
            return False, f"Timeout ({timeout}s) dépassé lors de l'exécution de: {' '.join(argv)}"
        except Exception as exc:
            return False, _redact_secrets(f"Erreur d'exécution: {exc}")

    # ── Santé ───────────────────────────────────────────────────────────

    def check_health(self) -> bool:
        """Vérifie que le répond via HTTP sur l'endpoint configuré."""
        try:
            proc = subprocess.run(
                ["curl", "-fsS", f"http://{self._host}:{self._port}/"],
                capture_output=True,
                timeout=5,
                check=False,
            )
            if proc.returncode == 0:
                return True
        except FileNotFoundError:
            pass
        except Exception:
            pass
        try:
            request = urllib.request.Request(
                f"http://{self._host}:{self._port}/", method="GET"
            )
            with urllib.request.urlopen(request, timeout=1.5) as response:
                return 200 <= response.status < 500
        except urllib.error.HTTPError:
            return True
        except Exception:
            return False

    # ── Introspection conteneur ─────────────────────────────────────────

    async def _inspect_container(self) -> dict[str, Any] | None:
        """Interroge l'état du conteneur via docker compose ps."""
        ok, out = await self._run_docker(
            ["ps", "--all", "--format", "json"], timeout=10.0
        )
        if not ok:
            raise RuntimeError(out or "Docker Compose est inaccessible")
        if not out.strip():
            return None

        malformed: list[str] = []
        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if isinstance(data, list) and data:
                    return data[0] if data else None
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                malformed.append(line)
                continue
        if malformed:
            raise RuntimeError("Réponse JSON inattendue de docker compose ps")
        return None


    # ── État ────────────────────────────────────────────────────────────

    async def get_status(self) -> dict[str, Any]:
        """Retourne l'état réel et vérifié du service."""
        # Si une transition est en cours, retourner l'état intermédiaire
        if self._state in (STATE_STARTING, STATE_STOPPING):
            return self._build_status_dict(
                state=self._state,
                healthy=False,
                container_id=self._cached_container_id,
            )

        project_available = (
            self._repo_dir.is_dir() and self._compose_file.is_file()
        )
        if not project_available:
            self._state = STATE_NOT_INSTALLED
            return self._build_status_dict(
                state=STATE_NOT_INSTALLED,
                healthy=False,
                allowed_actions=["install"],
            )

        try:
            container_info = await self._inspect_container()
        except Exception as exc:
            self._state = STATE_UNKNOWN
            self._last_error = _redact_secrets(str(exc))
            return self._build_status_dict(
                state=STATE_UNKNOWN, healthy=False, error=self._last_error
            )

        if not container_info:
            self._cached_container_id = None
            self._state = STATE_NOT_INSTALLED
            self._last_error = None
            return self._build_status_dict(
                state=STATE_NOT_INSTALLED,
                healthy=False,
                allowed_actions=["install"],
            )

        port_busy = is_port_in_use(self._port, host=self._host)

        if container_info:
            c_state = str(container_info.get("State", "")).lower()
            c_name = container_info.get("Name") or container_info.get("Service")
            self._cached_container_id = c_name

            if c_state in ("running", "up"):
                is_healthy = self.check_health() and str(
                    container_info.get("Health", "")
                ).lower() != "unhealthy"
                new_state = STATE_ACTIVE if is_healthy else STATE_DEGRADED
                self._state = new_state
                self._last_error = None
                return self._build_status_dict(
                    state=new_state,
                    healthy=is_healthy,
                    container_id=c_name,
                    container_info=container_info,
                    allowed_actions=["stop", "restart", "uninstall"]
                    + (["open"] if is_healthy else []),
                )
            elif c_state in ("exited", "stopped", "dead"):
                exit_code = container_info.get("ExitCode")
                if exit_code not in (None, 0, "0"):
                    self._state = STATE_ERROR
                    self._last_error = (
                        f"Le conteneur {self._project_name} s'est arrêté avec le code {exit_code}."
                    )
                    return self._build_status_dict(
                        state=STATE_ERROR,
                        healthy=False,
                        container_id=c_name,
                        container_info=container_info,
                        error=self._last_error,
                        allowed_actions=["install", "start", "uninstall"],
                    )
                self._state = STATE_STOPPED
                return self._build_status_dict(
                    state=STATE_STOPPED,
                    healthy=False,
                    container_id=c_name,
                    container_info=container_info,
                    allowed_actions=["start", "uninstall"],
                )

        # Si le conteneur n'est pas vu par compose mais que le port est occupé
        if port_busy:
            is_healthy = self.check_health()
            if is_healthy:
                self._state = STATE_ACTIVE
                return self._build_status_dict(
                    state=STATE_ACTIVE,
                    healthy=True,
                    container_id=self._cached_container_id or f"{self._project_name}-1",
                    allowed_actions=["stop", "restart", "open"],
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
                    allowed_actions=["start", "restart"],
                )

        self._state = STATE_UNKNOWN
        return self._build_status_dict(
            state=STATE_UNKNOWN,
            healthy=False,
            error=f"État Compose {self._project_name} indéterminé.",
        )

# ── Cycle de vie ────────────────────────────────────────────────────

    async def start(self) -> dict[str, Any]:
        """Démarre le service via docker compose up -d."""
        async with self._lock:
            curr = await self.get_status()
            if curr["status"] == STATE_ACTIVE:
                return curr
            if is_port_in_use(self._port, host=self._host):
                self._state = STATE_ERROR
                self._last_error = (
                    f"Conflit de port : le port {self._port} est déjà utilisé."
                )
                self._last_updated = _now()
                return self._build_status_dict(
                    state=STATE_ERROR, healthy=False, error=self._last_error
                )
            self._state = STATE_STARTING
            self._last_updated = _now()
            ok, out = await self._run_docker(["up", "-d"], timeout=900.0)
            if not ok:
                self._state = STATE_ERROR
                self._last_error = f"Échec du démarrage Docker Compose : {out[-400:]}"
                self._last_updated = _now()
                return self._build_status_dict(
                    state=STATE_ERROR, healthy=False, error=self._last_error
                )
            healthy = False
            for _ in range(15):
                await asyncio.sleep(1.0)
                if self.check_health():
                    healthy = True
                    break
            self._state = STATE_ACTIVE if healthy else STATE_DEGRADED
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
                    state=STATE_ERROR, healthy=False, error=self._last_error
                )
            self._state = STATE_STOPPED
            self._last_error = None
            self._last_updated = _now()
            return await self.get_status()
async def restart(self) -> dict[str, Any]:
        """Redémarre le service."""
        async with self._lock:
            self._state = STATE_STARTING
            self._last_updated = _now()
            ok, out = await self._run_docker(["restart"], timeout=60.0)
            if not ok:
                self._state = STATE_ERROR
                self._last_error = f"Échec du redémarrage Docker Compose : {out[-400:]}"
                self._last_updated = _now()
                return self._build_status_dict(
                    state=STATE_ERROR, healthy=False, error=self._last_error
                )
            healthy = False
            for _ in range(15):
                await asyncio.sleep(1.0)
                if self.check_health():
                    healthy = True
                    break
            self._state = STATE_ACTIVE if healthy else STATE_DEGRADED
            self._last_updated = _now()
            return await self.get_status()
async def install(self) -> dict[str, Any]:
        """Déploie le service via docker compose up -d après validation de la config."""
        async with self._lock:
            curr = await self.get_status()
            if curr["status"] == STATE_ACTIVE:
                return curr
            if not self._repo_dir.is_dir():
                self._state = STATE_ERROR
                self._last_error = (
                    f"Dépôt {self._project_name} introuvable : {self._repo_dir}. "
                    "Clonez le dépôt dans examples/."
                )
                self._last_updated = _now()
                return self._build_status_dict(
                    state=STATE_ERROR, healthy=False, error=self._last_error
                )
            if not self._compose_file.is_file():
                self._state = STATE_ERROR
                self._last_error = f"Fichier compose introuvable : {self._compose_file}"
                self._last_updated = _now()
                return self._build_status_dict(
                    state=STATE_ERROR, healthy=False, error=self._last_error
                )
            ok, out = await self._run_docker(["config"], timeout=30.0)
            if not ok:
                self._state = STATE_ERROR
                self._last_error = f"Configuration Compose invalide : {out[-400:]}"
                self._last_updated = _now()
                return self._build_status_dict(
                    state=STATE_ERROR, healthy=False, error=self._last_error
                )
            return await self.start()
async def uninstall(self) -> dict[str, Any]:
        """Désinstalle le service : arrêt et retrait des conteneurs."""
        async with self._lock:
            self._state = STATE_STOPPING
            self._last_updated = _now()
            ok, out = await self._run_docker(["down"], timeout=60.0)
            if not ok:
                self._state = STATE_ERROR
                self._last_error = f"Échec de la désinstallation Docker Compose : {out[-400:]}"
                self._last_updated = _now()
                return self._build_status_dict(
                    state=STATE_ERROR, healthy=False, error=self._last_error
                )
            self._state = STATE_NOT_INSTALLED
            self._last_error = None
            self._cached_container_id = None
            self._last_updated = _now()
            return await self.get_status()
async def get_logs(self, tail: int = 100) -> dict[str, Any]:
        """Retourne les logs récents du service."""
        safe_tail = max(1, min(int(tail), 500))
        ok, out = await self._run_docker(
            ["logs", f"--tail={safe_tail}", "--no-color"], timeout=15.0
        )
        if not ok:
            return {
                "ok": False,
                "error": out or "Erreur lors de la lecture des logs.",
                "logs": "",
            }
        return {"ok": True, "error": None, "logs": out}
def _build_status_dict(
        self,
        state: str,
        healthy: bool,
        container_id: str | None = None,
        container_info: dict[str, Any] | None = None,
        error: str | None = None,
        allowed_actions: list[str] | None = None,
    ) -> dict[str, Any]:
        meta = self.get_metadata()
        if allowed_actions is None:
            if state == STATE_NOT_INSTALLED:
                allowed_actions = ["install"]
            elif state == STATE_STOPPED:
                allowed_actions = ["start", "uninstall"]
            elif state in (STATE_ACTIVE, STATE_DEGRADED):
                allowed_actions = ["stop", "restart", "uninstall"]
                if healthy:
                    allowed_actions.append("open")
            elif state == STATE_ERROR:
                allowed_actions = ["install", "start", "restart", "uninstall"]
            elif state in (STATE_STARTING, STATE_STOPPING):
                allowed_actions = []
            else:
                allowed_actions = []

        return {
            "id": self._project_name,
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
__all__ = [
    "ComposeService",
    "STATE_ACTIVE",
    "STATE_ERROR",
    "STATE_DEGRADED",
    "STATE_STARTING",
    "STATE_STOPPED",
    "STATE_STOPPING",
    "STATE_NOT_INSTALLED",
    "STATE_UNKNOWN",
    "is_allowed_compose_args",
]
