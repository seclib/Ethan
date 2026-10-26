"""Odin Service Manager (Core layer).

Contrôle sécurisé du cycle de vie du plugin applicatif Odin :
- Détecte l'état réel du conteneur Docker et la disponibilité du port local.
- Détecte les conflits de ports (évite les collisions sur 4173).
- Exécute STRICTEMENT des opérations figées (start, stop, restart, status, logs, health).
- Aucune commande Docker arbitraire n'est acceptée.
- Confinement strict au fichier compose sous examples/odin.
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
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.hardware.ports import is_port_in_use

logger = logging.getLogger(__name__)

# États standardisés du service
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


def _resolve_default_repo() -> Path:
    """Résout le chemin du dépôt Odin."""
    configured = os.getenv("ETHAN_ODIN_REPO_DIR")
    if configured:
        return Path(configured).resolve()
    ethan_root = Path(__file__).resolve().parent.parent.parent
    candidate = ethan_root / "examples" / "odin"
    if candidate.is_dir() and (candidate / "compose.yaml").is_file():
        return candidate.resolve()
    return candidate


class OdinService:
    """Gestionnaire de cycle de vie du service Docker Odin."""

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
        self._controller_url = os.getenv("ETHAN_ODIN_CONTROLLER_URL", "").rstrip("/")
        self._controller_token = os.getenv("ETHAN_ODIN_CONTROLLER_TOKEN", "")
        self._lock = asyncio.Lock()
        self._state: str = STATE_UNKNOWN
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
        ``examples/odin/compose.yaml`` sous la racine ETHAN.
        Tout autre chemin est refusé (fail-closed).
        """
        try:
            configured = os.getenv("ETHAN_ODIN_REPO_DIR")
            ethan_root = Path(__file__).resolve().parent.parent.parent
            expected_repo = (
                Path(configured).resolve()
                if configured
                else (ethan_root / "examples" / "odin").resolve()
            )
            allowed_repos = {expected_repo}
            repo = self._repo_dir.resolve()
            if repo not in allowed_repos:
                raise ValueError(f"chemin Odin hors allowlist : {repo}")
            compose = self._compose_file.resolve()
            expected_compose = repo / "compose.yaml"
            if compose != expected_compose:
                raise ValueError(f"fichier compose invalide : {compose}")
        except ValueError:
            raise
        except Exception as exc:
            logger.warning("Validation confinement Odin impossible : %s", exc)

        if not self._compose_file.is_file():
            logger.warning(
                "Le fichier compose %s n'a pas été trouvé", self._compose_file
            )

    def get_metadata(self) -> dict[str, str]:
        """Lit les métadonnées réelles du dépôt (nom, package, description, version)."""
        pkg_file = Path(self._repo_dir) / "package.json"
        name = "Odin"
        pkg_name = "odin"
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
        if t in {
            ("up", "-d"),
            ("down",),
            ("stop",),
            ("restart",),
            ("ps", "--all", "--format", "json"),
            ("config",),
            ("probe",),
        }:
            return True
        if len(args) == 3 and args[0] == "logs" and args[1].startswith("--tail=") and args[2] == "--no-color":
            tail_str = args[1].split("=", 1)[1]
            return tail_str.isdigit() and 1 <= int(tail_str) <= 500
        return False

    async def _run_docker(self, args: list[str], timeout: float = 60.0) -> tuple[bool, str]:
        """Exécute une commande Docker figée sans shell=True."""
        if not self._is_allowed_docker_args(args):
            raise ValueError(f"commande Docker non autorisée : {args}")

        if getattr(self, "_controller_url", ""):
            return await asyncio.to_thread(self._run_controller_sync, args, timeout)

        # Re-valide le confinement à chaque appel (TOCTOU minimal).
        self._validate_confinement()
        binary = shutil.which(self._docker_cmd) or self._docker_cmd
        argv = [binary, "compose", "--project-name", "odin", "-f", str(self._compose_file), *args]

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

    def _controller_request(
        self, path: str, args: list[str] | None = None, timeout: float = 10.0
    ) -> dict[str, Any]:
        controller_url = getattr(self, "_controller_url", "")
        token = getattr(self, "_controller_token", "")
        if not controller_url or (args is not None and not token):
            raise RuntimeError("Contrôleur Odin non configuré")
        headers = {"Accept": "application/json"}
        data = None
        if args is not None:
            headers["Content-Type"] = "application/json"
            headers["Authorization"] = f"Bearer {token}"
            data = json.dumps({"args": args}).encode()
        request = urllib.request.Request(
            f"{controller_url}{path}", data=data, headers=headers,
            method="POST" if data is not None else "GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read(16384))
        except Exception as exc:
            raise RuntimeError(f"Contrôleur Odin inaccessible : {_redact_secrets(str(exc))}") from None
        if not isinstance(payload, dict):
            raise RuntimeError("Réponse invalide du contrôleur Odin")
        return payload

    def _run_controller_sync(self, args: list[str], timeout: float) -> tuple[bool, str]:
        try:
            result = self._controller_request("/run", args, timeout=timeout + 5.0)
            return bool(result.get("ok")), str(result.get("output") or result.get("error") or "")
        except Exception as exc:
            return False, _redact_secrets(str(exc))

    async def _controller_project_available(self) -> bool | None:
        try:
            result = await asyncio.to_thread(self._controller_request, "/health")
            return bool(result.get("project_available"))
        except Exception:
            return None

    async def check_health(self) -> bool:
        """Vérifie qu'Odin répond réellement en HTTP sur l'endpoint configuré."""
        if getattr(self, "_controller_url", ""):
            for _attempt in range(3):
                try:
                    result = await asyncio.to_thread(
                        self._controller_request, "/run", ["probe"], timeout=20.0
                    )
                    if bool(result.get("ok")):
                        return True
                except Exception:
                    pass
                if _attempt < 2:
                    await asyncio.sleep(0.5)
            return False
        try:
            request = urllib.request.Request(f"http://{self._host}:{self._port}/", method="GET")
            response = await asyncio.to_thread(urllib.request.urlopen, request, timeout=1.5)
            return 200 <= response.status < 500
        except urllib.error.HTTPError:
            return True
        except Exception:
            return False

    async def _inspect_container(self) -> dict[str, Any] | None:
        """Interroge l'état du conteneur via docker compose ps."""
        ok, out = await self._run_docker(["ps", "--all", "--format", "json"], timeout=10.0)
        if not ok:
            raise RuntimeError(out or "Docker Compose est inaccessible")
        if not out.strip():
            return None

        # docker compose ps --format json retourne un ou plusieurs objets JSON
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

    async def get_health(self) -> dict[str, Any]:
        """Vérification approfondie de l'état de santé du service."""
        is_healthy = await self.check_health()
        try:
            container_info = await self._inspect_container()
        except Exception as exc:
            return {"status": "unknown", "healthy": False, "reachable": False, "tcp_probe": False,
                    "container_state": "unknown", "port": self._port, "host": self._host,
                    "url": f"http://{self._host}:{self._port}", "last_transition": self._last_updated,
                    "checked_at": _now(), "error": _redact_secrets(str(exc))}
        container_state = str(container_info.get("State", "none")).lower() if container_info else "none"
        container_health = str(container_info.get("Health", "unknown")).lower() if container_info else "unknown"
        is_healthy = is_healthy and container_health != "unhealthy"

        status_str = "healthy" if is_healthy else ("degraded" if container_state in ("running", "up") else "unreachable")
        return {
            "status": status_str,
            "healthy": is_healthy,
            "reachable": is_healthy,
            "tcp_probe": is_healthy,
            "container_state": container_state,
            "container_health": container_health,
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

        project_available = (
            await self._controller_project_available()
            if getattr(self, "_controller_url", "")
            else self._repo_dir.is_dir() and self._compose_file.is_file()
        )
        if project_available is None:
            self._state = STATE_UNKNOWN
            self._last_error = "Contrôleur Docker Odin inaccessible."
            return self._build_status_dict(state=STATE_UNKNOWN, healthy=False, error=self._last_error)
        if not project_available:
            self._state = STATE_NOT_INSTALLED
            return self._build_status_dict(state=STATE_NOT_INSTALLED, healthy=False, allowed_actions=["install"])
        try:
            container_info = await self._inspect_container()
        except Exception as exc:
            self._state = STATE_UNKNOWN
            self._last_error = _redact_secrets(str(exc))
            return self._build_status_dict(state=STATE_UNKNOWN, healthy=False, error=self._last_error)
        if not container_info:
            self._cached_container_id = None
            self._state = STATE_NOT_INSTALLED
            self._last_error = None
            return self._build_status_dict(state=STATE_NOT_INSTALLED, healthy=False, allowed_actions=["install"])
        port_busy = is_port_in_use(self._port, host=self._host)

        if container_info:
            c_state = str(container_info.get("State", "")).lower()
            c_name = container_info.get("Name") or container_info.get("Service")
            self._cached_container_id = c_name

            if c_state in ("running", "up"):
                is_healthy = await self.check_health() and str(container_info.get("Health", "")).lower() != "unhealthy"
                new_state = STATE_ACTIVE if is_healthy else STATE_DEGRADED
                self._state = new_state
                self._last_error = None
                return self._build_status_dict(
                    state=new_state,
                    healthy=is_healthy,
                    container_id=c_name,
                    container_info=container_info,
                    allowed_actions=["stop", "restart", "uninstall"] + (["open"] if is_healthy else []),
                )
            elif c_state in ("exited", "stopped", "dead"):
                exit_code = container_info.get("ExitCode")
                if exit_code not in (None, 0, "0", 137, "137", 143, "143"):
                    self._state = STATE_ERROR
                    self._last_error = f"Le conteneur Odin s'est arrêté avec le code {exit_code}."
                    return self._build_status_dict(
                        state=STATE_ERROR, healthy=False, container_id=c_name,
                        container_info=container_info, error=self._last_error,
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
            is_healthy = await self.check_health()
            if is_healthy:
                self._state = STATE_ACTIVE
                return self._build_status_dict(
                    state=STATE_ACTIVE,
                    healthy=True,
                    container_id=self._cached_container_id or "odin-1",
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
        return self._build_status_dict(state=STATE_UNKNOWN, healthy=False, error="État Compose Odin indéterminé.")

    async def start(self) -> dict[str, Any]:
        """Démarre le service via docker compose up -d."""
        async with self._lock:
            # 1. Vérifier si déjà actif
            curr = await self.get_status()
            if curr["status"] == STATE_ACTIVE:
                return curr

            # 2. Vérifier les conflits de port avec un tiers
            if is_port_in_use(self._port, host=self._host):
                if not await self.check_health():
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
            ok, out = await self._run_docker(["up", "-d"], timeout=900.0)
            if not ok:
                self._state = STATE_ERROR
                self._last_error = f"Échec du démarrage Docker Compose : {out[-400:]}"
                self._last_updated = _now()
                return self._build_status_dict(
                    state=STATE_ERROR,
                    healthy=False,
                    error=self._last_error,
                )

            # 5. Attendre la disponibilité réseau (polling 2s, timeout ~90s)
            healthy = False
            consecutive = 0
            for _ in range(45):
                await asyncio.sleep(2.0)
                if await self.check_health():
                    consecutive += 1
                    if consecutive >= 2:
                        healthy = True
                        break
                else:
                    consecutive = 0

            self._state = STATE_ACTIVE if healthy else STATE_DEGRADED
            if not healthy:
                self._last_error = "Le conteneur a démarré, mais Odin ne répond pas sur son endpoint HTTP."
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

            # Vérifier que le conteneur est bien arrêté (polling jusqu'à 30s)
            stopped = False
            for _ in range(30):
                try:
                    container_info = await self._inspect_container()
                except Exception:
                    container_info = None
                if not container_info:
                    stopped = True
                    break
                c_state = str(container_info.get("State", "")).lower()
                if c_state in ("exited", "stopped", "dead"):
                    stopped = True
                    break
                await asyncio.sleep(1.0)

            if not stopped:
                self._state = STATE_ERROR
                self._last_error = "Le conteneur Odin n'a pas pu être arrêté dans le délai imparti."
                self._last_updated = _now()
                return self._build_status_dict(
                    state=STATE_ERROR,
                    healthy=False,
                    error=self._last_error,
                )

            self._state = STATE_STOPPED
            self._last_error = None
            self._last_updated = _now()
            return await self.get_status()

    async def install(self) -> dict[str, Any]:
        """Déploie Odin via docker compose up -d après validation de la config.

        Ne réinstalle pas si déjà présent et actif.
        Ne touche pas aux fichiers .env ni aux volumes existants.
        """
        async with self._lock:
            # 1. Vérifier si déjà actif
            curr = await self.get_status()
            if curr["status"] == STATE_ACTIVE:
                return curr

            # 2. Vérifier la présence du dépôt et du compose
            project_available = (
                await self._controller_project_available()
                if getattr(self, "_controller_url", "")
                else self._repo_dir.is_dir()
            )
            if project_available is None:
                self._state = STATE_UNKNOWN
                self._last_error = "Contrôleur Docker Odin inaccessible."
                return self._build_status_dict(state=STATE_UNKNOWN, healthy=False, error=self._last_error)
            if not project_available:
                self._state = STATE_ERROR
                self._last_error = (
                    f"Dépôt Odin introuvable : {self._repo_dir}. "
                    "Clonez le dépôt https://github.com/seclib/odin dans examples/odin."
                )
                self._last_updated = _now()
                return self._build_status_dict(state=STATE_ERROR, healthy=False, error=self._last_error)

            if not getattr(self, "_controller_url", "") and not self._compose_file.is_file():
                self._state = STATE_ERROR
                self._last_error = f"Fichier compose introuvable : {self._compose_file}"
                self._last_updated = _now()
                return self._build_status_dict(state=STATE_ERROR, healthy=False, error=self._last_error)

            # 3. Valider la configuration Compose
            ok, out = await self._run_docker(["config"], timeout=30.0)
            if not ok:
                self._state = STATE_ERROR
                self._last_error = f"Configuration Compose invalide : {out[-400:]}"
                self._last_updated = _now()
                return self._build_status_dict(state=STATE_ERROR, healthy=False, error=self._last_error)

            # 4. Déployer (docker compose up -d pull les images si nécessaire)
            self._state = STATE_STARTING
            self._last_error = None
            self._last_updated = _now()

            ok, out = await self._run_docker(["up", "-d"], timeout=900.0)
            if not ok:
                self._state = STATE_ERROR
                self._last_error = f"Échec du déploiement Docker Compose : {out[-400:]}"
                self._last_updated = _now()
                return self._build_status_dict(state=STATE_ERROR, healthy=False, error=self._last_error)

            # 5. Attendre la disponibilité réseau (polling 2s, timeout ~90s)
            healthy = False
            consecutive = 0
            for _ in range(45):
                await asyncio.sleep(2.0)
                if await self.check_health():
                    consecutive += 1
                    if consecutive >= 2:
                        healthy = True
                        break
                else:
                    consecutive = 0

            self._state = STATE_ACTIVE if healthy else STATE_DEGRADED
            self._last_updated = _now()
            return await self.get_status()

    async def uninstall(self) -> dict[str, Any]:
        """Arrête et retire uniquement les conteneurs du projet Odin.

        Préserve les volumes de données et les fichiers utilisateur (.env, etc.).
        N'utilise jamais `docker compose down -v`.
        """
        async with self._lock:
            self._state = STATE_STOPPING
            self._last_updated = _now()

            # 1. Vérifier que le dépôt existe
            if not self._repo_dir.is_dir():
                self._state = STATE_NOT_INSTALLED
                self._last_error = None
                self._last_updated = _now()
                return self._build_status_dict(state=STATE_NOT_INSTALLED, healthy=False)

            # 2. Arrêter et retirer les conteneurs (sans -v pour préserver les volumes)
            ok, out = await self._run_docker(["down"], timeout=60.0)
            if not ok:
                self._state = STATE_ERROR
                self._last_error = f"Échec de la désinstallation Docker Compose : {out[-400:]}"
                self._last_updated = _now()
                return self._build_status_dict(state=STATE_ERROR, healthy=False, error=self._last_error)

            # 3. Vérifier que plus rien ne tourne
            try:
                container_info = await self._inspect_container()
            except Exception as exc:
                self._state = STATE_ERROR
                self._last_error = _redact_secrets(str(exc))
                return self._build_status_dict(state=STATE_ERROR, healthy=False, error=self._last_error)
            if container_info:
                self._state = STATE_ERROR
                self._last_error = "Des ressources Compose Odin subsistent après la désinstallation."
                return self._build_status_dict(state=STATE_ERROR, healthy=False, error=self._last_error)

            self._state = STATE_NOT_INSTALLED
            self._last_error = None
            self._last_updated = _now()
            return self._build_status_dict(state=STATE_NOT_INSTALLED, healthy=False)

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

            # Vérifier que le conteneur a redémarré et répond (polling jusqu'à 15s)
            healthy = False
            for _ in range(15):
                await asyncio.sleep(1.0)
                if await self.check_health():
                    try:
                        container_info = await self._inspect_container()
                    except Exception:
                        container_info = None
                    if container_info:
                        c_state = str(container_info.get("State", "")).lower()
                        if c_state in ("running", "up"):
                            healthy = True
                            break
                    else:
                        healthy = True
                        break

            self._state = STATE_ACTIVE if healthy else STATE_DEGRADED
            self._last_updated = _now()
            return await self.get_status()

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
            "id": "odin",
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
_odin_service: OdinService | None = None


def get_odin_service() -> OdinService:
    global _odin_service
    if _odin_service is None:
        _odin_service = OdinService()
    return _odin_service


def set_odin_service(service: OdinService | None) -> None:
    global _odin_service
    _odin_service = service


__all__ = [
    "STATE_ACTIVE",
    "STATE_ERROR",
    "STATE_DEGRADED",
    "STATE_STARTING",
    "STATE_STOPPED",
    "STATE_STOPPING",
    "STATE_NOT_INSTALLED",
    "STATE_UNKNOWN",
    "OdinService",
    "get_odin_service",
    "set_odin_service",
]
