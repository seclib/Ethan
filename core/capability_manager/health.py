"""Health checks — une capability n'est pas READY parce qu'installée.

Paliers (section 8 de la spec) :
  Installed → Started → Endpoint reachable → API responds → Functional → READY
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any

from core.capability_manager.types import CapabilityRuntimeState, CapabilitySpec

logger = logging.getLogger(__name__)

_TCP_TIMEOUT = 2.0
_HTTP_TIMEOUT = 3.0


def _resolve(
    value: str,
    state: CapabilityRuntimeState,
    defaults: dict[str, Any] | None = None,
) -> str:
    """Résout {config.<field>} et {runtime_meta.<field>} dans une URL déclarée.

    Un champ de config **jamais saisi** par l'utilisateur vaut son défaut
    déclaré dans le schema de la spec : sinon `{config.x}` résoudrait en
    vide et un composant sain serait jugé « santé refusée » alors qu'il
    tourne avec la valeur par défaut.
    """
    if "{" not in value:
        return value
    defaults = defaults or {}
    parts = []
    remaining = value
    while "{" in remaining:
        before, rest = remaining.split("{", 1)
        placeholder, remaining = rest.split("}", 1)
        parts.append(before)
        if placeholder.startswith("config."):
            key = placeholder[7:]
            if key in state.config:
                parts.append(str(state.config[key]))
            else:
                parts.append(str(defaults.get(key, "")))
        elif placeholder.startswith("runtime_meta."):
            parts.append(str(state.runtime_meta.get(placeholder[13:], "")))
        else:
            parts.append("")
    parts.append(remaining)
    return "".join(parts)


class HealthChecker:
    """Évalue les paliers de santé déclarés dans la spec.

    Les vérifications n'utilisent QUE des données déclaratives (spec + état
    persisté typé) : aucune commande utilisateur n'est exécutée.
    """

    async def evaluate(
        self,
        spec: CapabilitySpec,
        state: CapabilityRuntimeState,
    ) -> dict[str, Any]:
        """Retourne {"ok": bool, "level": str, "checks": [...]}.

        `ok` est vrai uniquement si tous les checks `functional` passent
        (état READY) ; sinon `level` indique le palier atteint.
        """
        checks: list[dict[str, Any]] = []
        # Valeur effective d'un champ non saisi : son défaut déclaré par la
        # spec (la spec reste la source, jamais une saisie utilisateur).
        defaults = {f.name: f.default for f in spec.config_schema if f.default is not None}
        for hc in spec.health_checks:
            entry = await self._run_check(hc, state, defaults)
            entry["level"] = hc.level
            checks.append(entry)
        functional_checks = [c for c in checks if c.get("level") == "functional"]
        basic_checks = [c for c in checks if c.get("level") == "basic"]
        functional_ok = all(c["ok"] for c in functional_checks)
        basic_ok = bool(basic_checks) and all(c["ok"] for c in basic_checks)
        level = "ready" if functional_ok else ("basic" if basic_ok else "failing")
        return {"ok": functional_ok, "level": level, "checks": checks}

    async def _run_check(
        self, hc: Any, state: CapabilityRuntimeState, defaults: dict[str, Any]
    ) -> dict[str, Any]:
        start = time.monotonic()
        if hc.kind == "endpoint":
            ok, detail = await self._check_endpoint(hc, state, defaults)
        elif hc.kind == "tcp":
            ok, detail = await self._check_tcp(hc, state, defaults)
        elif hc.kind == "exec":
            ok, detail = await self._check_exec(hc, state)
        elif hc.kind == "builtin":
            # Composant intégré au process Core : présent par construction.
            # Le check reste réel côté opérationnel (process vivant).
            ok, detail = True, f"intégré au process Core (pid {os.getpid()})"
        else:
            return {"kind": hc.kind, "ok": False, "detail": f"kind inconnu: {hc.kind}"}
        return {
            "kind": hc.kind,
            "ok": ok,
            "detail": detail,
            "duration_ms": int((time.monotonic() - start) * 1000),
        }

    async def _check_endpoint(
        self, hc: Any, state: CapabilityRuntimeState, defaults: dict[str, Any]
    ) -> tuple[bool, str]:
        url = _resolve(hc.url, state, defaults)
        if not url:
            return False, "url non configuree"
        try:
            import httpx

            async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
                resp = await client.get(url)
            if resp.status_code < 500:
                return True, f"HTTP {resp.status_code}"
            return False, f"HTTP {resp.status_code}"
        except Exception as exc:  # noqa: BLE001 — bordure réseau intentionnelle
            return False, f"injoignable: {type(exc).__name__}"

    async def _check_tcp(
        self, hc: Any, state: CapabilityRuntimeState, defaults: dict[str, Any]
    ) -> tuple[bool, str]:
        host = hc.host or "127.0.0.1"
        port_raw = state.config.get(hc.port) if hc.port else None
        if port_raw is None and hc.port:
            # Champ non saisi → défaut déclaré par le schema de la spec.
            port_raw = defaults.get(hc.port)
        try:
            port = int(port_raw)
        except (TypeError, ValueError):
            return False, f"port non configure ({hc.port!r})"
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port), timeout=_TCP_TIMEOUT
            )
        except Exception as exc:  # noqa: BLE001
            return False, f"TCP {host}:{port} refuse: {type(exc).__name__}"
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:  # pragma: no cover — fermeture best-effort
            pass
        return True, f"TCP {host}:{port} ouvert"

    async def _check_exec(self, hc: Any, state: CapabilityRuntimeState) -> tuple[bool, str]:
        # Commande FIGÉE dans la spec — jamais dérivée d'un input utilisateur.
        if not hc.command:
            return False, "commande non declaree"
        try:
            proc = await asyncio.create_subprocess_exec(
                *hc.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
        except FileNotFoundError:
            return False, f"executable introuvable: {hc.command[0]}"
        try:
            out, _ = await asyncio.wait_for(proc.communicate(), timeout=10.0)
        except asyncio.TimeoutError:
            proc.kill()
            return False, "timeout"
        ok = proc.returncode == 0
        return ok, (out or b"").decode(errors="replace")[:200]
