"""Frame service manager (Core layer).

Gère le cycle de vie Docker Compose de l'application indépendante Frame
(base HyperFrames). Frame reste une application autonome; ETHAN ne fait que
piloter son cycle de vie via un compose figé et des routes sécurisées.
"""

from __future__ import annotations

import os
from pathlib import Path

from core.plugins.compose_service import ComposeService, STATE_ACTIVE, STATE_ERROR, STATE_STOPPED

FRAME_DEFAULT_PORT = 5190
FRAME_DEFAULT_HOST = "127.0.0.1"


def _resolve_default_repo() -> Path:
    configured = os.getenv("ETHAN_FRAME_REPO_DIR")
    if configured:
        return Path(configured).resolve()
    ethan_root = Path(__file__).resolve().parent.parent.parent
    return (ethan_root / "examples" / "frame").resolve()


class FrameService(ComposeService):
    def __init__(
        self,
        repo_dir: Path | None = None,
        port: int = FRAME_DEFAULT_PORT,
        host: str = FRAME_DEFAULT_HOST,
        docker_cmd: str = "docker",
    ) -> None:
        super().__init__(
            project_name="frame",
            repo_dir=repo_dir or _resolve_default_repo(),
            port=port,
            host=host,
            docker_cmd=docker_cmd,
        )

    def get_metadata(self) -> dict[str, str]:
        meta = super().get_metadata()
        if str(meta.get("name", "")).lower() in ("frame", "frame"):
            meta["name"] = "Frames"
        if str(meta.get("package_name", "")).strip().lower() in ("", "frame"):
            meta["package_name"] = meta.get("package_name", "frame")
        return meta


_frame_service: FrameService | None = None


def get_frame_service() -> FrameService:
    global _frame_service
    if _frame_service is None:
        _frame_service = FrameService()
    return _frame_service

def set_frame_service(service: FrameService | None) -> None:
    global _frame_service
    _frame_service = service


__all__ = [
    "FRAME_DEFAULT_PORT",
    "FRAME_DEFAULT_HOST",
    "FrameService",
    "get_frame_service",
    "set_frame_service",
    "STATE_ACTIVE",
    "STATE_ERROR",
    "STATE_STOPPED",
]
