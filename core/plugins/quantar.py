"""Quantar service lifecycle (Core layer).

Réutilise le gestionnaire générique ComposeService pour la gestion
optionnelle du runtime Docker autonome de Quantar.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from core.plugins.compose_service import (
    ComposeService,
    STATE_ACTIVE,
    STATE_ERROR,
    STATE_STOPPED,
    STATE_UNKNOWN,
    STATE_NOT_INSTALLED,
)


def _resolve_default_repo() -> Path:
    configured = os.getenv("ETHAN_QUANTAR_REPO_DIR")
    if configured:
        return Path(configured).resolve()
    ethan_root = Path(__file__).resolve().parent.parent.parent
    return (ethan_root / "examples" / "quantar").resolve()


class QuantarService(ComposeService):
    def __init__(
        self,
        repo_dir: Path | None = None,
        docker_cmd: str = "docker",
    ) -> None:
        super().__init__(
            project_name="quantar",
            repo_dir=repo_dir or _resolve_default_repo(),
            port=0,
            host="127.0.0.1",
            docker_cmd=docker_cmd,
        )

    def check_health(self) -> bool:
        """Santé basée sur l'état réel du conteneur, sans HTTP."""
        try:
            info = subprocess.run(
                [
                    shutil.which(self._docker_cmd) or self._docker_cmd,
                    "compose",
                    "--project-name",
                    self._project_name,
                    "-f",
                    str(self._compose_file),
                    "ps",
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=str(self._repo_dir),
                check=False,
            )
            if info.returncode != 0:
                return False
            normalized_state = "running"
            for line in info.stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if isinstance(data, list) and data:
                        data = data[0]
                    if isinstance(data, dict):
                        state = str(data.get("State", "")).lower()
                        if return_state := (state in ("running", "up")):
                            return True
                except json.JSONDecodeError:
                    continue
            return False
        except Exception:
            return False


    def _image_available(self) -> bool:
        import shutil
        binary = shutil.which(self._docker_cmd) or self._docker_cmd
        try:
            proc = subprocess.run(
                [binary, "image", "inspect", "quantar-runtime:latest"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            return proc.returncode == 0
        except Exception:
            return False

    async def get_status(self) -> dict[str, Any]:
        result = await super().get_status()
        if result.get("status") == STATE_NOT_INSTALLED and self._image_available():
            return self._build_status_dict(
                state=STATE_STOPPED,
                healthy=False,
                allowed_actions=["start", "inspect"],
                error="Runtime image installed, no Quantar container currently started.",
            )
        return result

_quantar_service: QuantarService | None = None


def get_quantar_service() -> QuantarService:
    global _quantar_service
    if _quantar_service is None:
        _quantar_service = QuantarService()
    return _quantar_service


def set_quantar_service(service: QuantarService | None) -> None:
    global _quantar_service
    _quantar_service = service


__all__ = ["QuantarService", "get_quantar_service", "set_quantar_service",
           "STATE_ACTIVE", "STATE_ERROR", "STATE_STOPPED", "STATE_UNKNOWN", "STATE_NOT_INSTALLED"]
