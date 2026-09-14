"""SystemDiagnostics — vérification réelle de l'état d'ETHAN.

Chaque check interroge le composant RÉEL (ping SQL, ping Redis, connexion
NATS, docker ps, healthcheck kernel, ProviderManager, ToolServerManager,
PluginRegistry, RAG pipeline, filesystem).  Statuts :

    ok          — le composant répond et fonctionne
    warning     — fonctionne mais avec une réserve explicite (clé absente…)
    error       — le composant est censé exister mais échoue
    unavailable — le composant n'est pas configuré / pas injecté / absent

Les dépendances sont injectées par la composition root (API lifespan ou
CLI) — le service ne crée jamais lui-même de connexion persistante.
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Timeout par défaut d'un check individuel (secondes).
CHECK_TIMEOUT_S = 4.0


class Status(str, Enum):
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    UNAVAILABLE = "unavailable"


@dataclass
class CheckResult:
    """Résultat d'un check de diagnostic."""

    component: str
    status: Status
    message: str
    detail: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "component": self.component,
            "status": self.status.value,
            "message": self.message,
            "detail": self.detail,
            "metadata": self.metadata,
            "duration_ms": round(self.duration_ms, 1),
        }


async def _run_check(component: str, coro_factory) -> CheckResult:
    """Exécute un check avec timeout global et capture d'exception."""
    start = time.monotonic()
    try:
        result = await asyncio.wait_for(coro_factory(), timeout=CHECK_TIMEOUT_S)
    except asyncio.TimeoutError:
        result = CheckResult(
            component=component,
            status=Status.ERROR,
            message=f"Timeout après {CHECK_TIMEOUT_S:.0f}s — le composant ne répond pas",
        )
    except Exception as exc:  # noqa: BLE001 — un diagnostic ne doit jamais planter
        logger.debug("Diagnostic %s failed: %s", component, exc)
        result = CheckResult(
            component=component,
            status=Status.ERROR,
            message=f"{type(exc).__name__}: {exc}",
        )
    result.duration_ms = (time.monotonic() - start) * 1000
    return result


class SystemDiagnostics:
    """Vérifie l'état réel des composants d'ETHAN.

    Args:
        pg_pool: Pool asyncpg PostgreSQL (optionnel).
        redis_client: Client Redis async (optionnel).
        nats_url: URL du broker NATS (optionnel).
        database_url: URL PostgreSQL (fallback si pas de pool injecté).
        kernel_url: URL du kernel Runtime (healthcheck /health/ready).
        provider_manager: ProviderManager Core (optionnel).
        rag_pipeline: RAGPipeline Core (optionnel).
        tool_manager: ToolManager Core (optionnel).
        tool_servers_manager: ToolServerManager Core (optionnel).
        plugin_registry: PluginRegistry Core (optionnel).
        workspace_dir: Répertoire workspace à vérifier (défaut : cwd).
    """

    def __init__(
        self,
        *,
        pg_pool: Any = None,
        redis_client: Any = None,
        nats_url: str | None = None,
        database_url: str | None = None,
        kernel_url: str | None = None,
        provider_manager: Any = None,
        rag_pipeline: Any = None,
        tool_manager: Any = None,
        tool_servers_manager: Any = None,
        plugin_registry: Any = None,
        workspace_dir: str | None = None,
    ) -> None:
        self._pg_pool = pg_pool
        self._redis = redis_client
        self._nats_url = nats_url or os.getenv("NATS_URL", "nats://localhost:4222")
        self._database_url = database_url or os.getenv(
            "DATABASE_URL", "postgresql://ethan:ethan@localhost:5432/ethan"
        )
        self._kernel_url = (kernel_url or os.getenv(
            "ETHAN_KERNEL_URL", "http://localhost:8080"
        )).rstrip("/")
        self._provider_manager = provider_manager
        self._rag = rag_pipeline
        self._tool_manager = tool_manager
        self._tool_servers = tool_servers_manager
        self._plugins = plugin_registry
        self._workspace_dir = workspace_dir or os.getcwd()

    # ── Orchestration ──────────────────────────────────────────────────

    async def run(self, components: list[str] | None = None) -> dict[str, Any]:
        """Exécute tous les checks (ou un sous-ensemble) et retourne le rapport."""
        checks = {
            "postgres": self._check_postgres,
            "redis": self._check_redis,
            "nats": self._check_nats,
            "kernel": self._check_kernel,
            "docker": self._check_docker,
            "providers": self._check_providers,
            "models": self._check_models,
            "knowledge": self._check_knowledge,
            "tools": self._check_tools,
            "mcp": self._check_mcp,
            "plugins": self._check_plugins,
            "filesystem": self._check_filesystem,
        }
        if components:
            wanted = {c.strip().lower() for c in components}
            checks = {k: v for k, v in checks.items() if k in wanted}

        from .host import check_host_resources

        host_results = await asyncio.get_running_loop().run_in_executor(
            None, check_host_resources
        )
        results = [
            *(await asyncio.gather(
                *(_run_check(name, factory) for name, factory in checks.items())
            )),
            *host_results,
        ]
        report = {r.component: r.to_dict() for r in results}
        counts = {s.value: 0 for s in Status}
        for r in results:
            counts[r.status.value] += 1
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total": len(results),
                "counts": counts,
                "status": self._overall(counts),
            },
            "components": report,
        }

    @staticmethod
    def _overall(counts: dict[str, int]) -> str:
        if counts.get("error"):
            return "unhealthy"
        if counts.get("warning") or counts.get("unavailable"):
            # UNAVAILABLE n'est pas une panne (GPU absent, optionnel non
            # configuré) : le système est dégradé/limité, pas cassé.
            return "degraded"
        return "healthy"

    @staticmethod
    def _redact(url: str | None) -> str:
        """Masque les credentials d'une URL (règle repo : jamais de secret)."""
        if not url:
            return ""
        parsed = urlparse(url)
        if parsed.password or parsed.username:
            netloc = parsed.hostname or ""
            if parsed.port:
                netloc = f"{netloc}:{parsed.port}"
            return f"{parsed.scheme}://{netloc}{parsed.path}"
        return url


    # ── Infrastructure ─────────────────────────────────────────────────

    async def _check_postgres(self) -> CheckResult:
        if self._pg_pool is None:
            return CheckResult(
                "postgres", Status.UNAVAILABLE,
                "Aucun pool PostgreSQL — le Core n'a pas réussi à s'y connecter",
                detail=self._redact(self._database_url),
            )
        try:
            await asyncio.wait_for(self._pg_pool.fetch("SELECT 1"), timeout=3.0)
        except Exception as exc:  # noqa: BLE001
            return CheckResult(
                "postgres", Status.ERROR,
                f"Connexion PostgreSQL échouée : {exc}",
                detail=self._redact(self._database_url),
            )
        return CheckResult(
            "postgres", Status.OK, "Connecté",
            metadata={"url": self._redact(self._database_url)},
        )

    async def _check_redis(self) -> CheckResult:
        if self._redis is None:
            return CheckResult(
                "redis", Status.UNAVAILABLE,
                "Aucun client Redis — le Core n'a pas réussi à s'y connecter",
            )
        try:
            pong = await asyncio.wait_for(self._redis.ping(), timeout=3.0)
        except Exception as exc:  # noqa: BLE001
            return CheckResult("redis", Status.ERROR, f"Ping Redis échoué : {exc}")
        return CheckResult(
            "redis", Status.OK, "Connecté", metadata={"pong": str(pong)},
        )

    async def _check_nats(self) -> CheckResult:
        try:
            import nats as nats_lib
        except ImportError:
            return CheckResult(
                "nats", Status.UNAVAILABLE, "Le paquet nats-py n'est pas installé",
            )
        client = None
        try:
            client = await nats_lib.connect(
                servers=[self._nats_url],
                connect_timeout=2,
                max_reconnect_attempts=0,
                allow_reconnect=False,
            )
        except Exception as exc:  # noqa: BLE001
            return CheckResult(
                "nats", Status.ERROR,
                f"Connexion NATS échouée : {exc}",
                detail=self._nats_url,
            )
        finally:
            if client is not None:
                try:
                    await client.drain()
                except Exception:  # noqa: BLE001
                    pass
        return CheckResult(
            "nats", Status.OK, "Connecté", metadata={"url": self._nats_url},
        )

    async def _check_kernel(self) -> CheckResult:
        import urllib.request

        url = f"{self._kernel_url}/health/ready"

        def _fetch() -> tuple[int, str]:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=2) as resp:  # noqa: S310
                return resp.status, resp.read(200).decode("utf-8", "replace")

        try:
            status, body = await asyncio.get_running_loop().run_in_executor(None, _fetch)
        except Exception as exc:  # noqa: BLE001
            return CheckResult(
                "kernel", Status.ERROR,
                f"Kernel Runtime injoignable : {exc}",
                detail=url,
            )
        return CheckResult(
            "kernel", Status.OK, f"Kernel prêt (HTTP {status})",
            metadata={"url": url, "body": body[:120]},
        )

    async def _check_docker(self) -> CheckResult:
        if shutil.which("docker") is None:
            return CheckResult(
                "docker", Status.UNAVAILABLE,
                "La commande 'docker' est introuvable (conteneur sans socket Docker ?)",
            )
        try:
            def _run() -> "subprocess.CompletedProcess[str]":
                return subprocess.run(
                    ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"],
                    capture_output=True, text=True, timeout=5, check=True,
                )
            proc = await asyncio.get_running_loop().run_in_executor(None, _run)
        except subprocess.CalledProcessError as exc:
            return CheckResult(
                "docker", Status.ERROR,
                f"'docker ps' a échoué : {(exc.stderr or '').strip()[:200]}",
            )
        except subprocess.TimeoutExpired:
            return CheckResult("docker", Status.ERROR, "Timeout du daemon Docker")
        containers = [
            line.split("\t", 1)
            for line in proc.stdout.strip().splitlines()
            if line.strip()
        ]
        return CheckResult(
            "docker", Status.OK,
            f"Daemon accessible ({len(containers)} conteneurs actifs)",
            metadata={"containers": containers},
        )

    # ── Intelligence (providers, modèles, RAG, tools, MCP, plugins) ────

    async def _check_providers(self) -> CheckResult:
        if self._provider_manager is None:
            return CheckResult(
                "providers", Status.UNAVAILABLE,
                "ProviderManager non initialisé (échec au démarrage du Core ?)",
            )
        try:
            providers = await self._provider_manager.list_providers()
        except Exception as exc:  # noqa: BLE001
            return CheckResult(
                "providers", Status.ERROR, f"Liste des providers échouée : {exc}",
            )
        if not providers:
            return CheckResult(
                "providers", Status.WARNING,
                "Aucun provider LLM enregistré — configurez-en un (page Providers)",
            )
        entries = []
        warnings = 0
        errors = 0
        for p in providers:
            pstatus = str(p.get("status", ""))
            if p.get("enabled") and not p.get("has_api_key", True):
                state = "warning"
                warnings += 1
            elif pstatus in ("connected", "available", "ok"):
                state = "ok"
            elif pstatus in ("error", "unreachable", "failed"):
                state = "error"
                errors += 1
            else:
                state = "warning"
                warnings += 1
            entries.append({
                "name": p.get("name") or p.get("id"),
                "type": p.get("type"),
                "state": state,
                "status": pstatus,
                "enabled": bool(p.get("enabled")),
                "has_api_key": bool(p.get("has_api_key")),
                "default_model": p.get("default_model") or "",
            })
        if errors:
            status = Status.ERROR
            message = f"{errors} provider(s) en erreur sur {len(entries)}"
        elif warnings:
            status = Status.WARNING
            message = f"{warnings} provider(s) à configurer sur {len(entries)}"
        else:
            status = Status.OK
            message = f"{len(entries)} provider(s) opérationnels"
        return CheckResult(
            "providers", status, message, metadata={"providers": entries},
        )

    async def _check_models(self) -> CheckResult:
        if self._provider_manager is None:
            return CheckResult(
                "models", Status.UNAVAILABLE, "ProviderManager non initialisé",
            )
        try:
            providers = await self._provider_manager.list_providers()
        except Exception as exc:  # noqa: BLE001
            return CheckResult(
                "models", Status.ERROR, f"Catalogue indisponible : {exc}",
            )
        models = sorted({
            p.get("default_model") for p in providers if p.get("default_model")
        })
        if not models:
            return CheckResult(
                "models", Status.WARNING,
                "Aucun modèle par défaut configuré sur les providers",
            )
        return CheckResult(
            "models", Status.OK, f"{len(models)} modèle(s) par défaut",
            metadata={"models": models},
        )

    async def _check_knowledge(self) -> CheckResult:
        if self._rag is None:
            return CheckResult(
                "knowledge", Status.UNAVAILABLE, "Moteur RAG non initialisé",
            )
        try:
            stats = self._rag.stats()
        except Exception as exc:  # noqa: BLE001
            return CheckResult(
                "knowledge", Status.ERROR, f"Moteur RAG en échec : {exc}",
            )
        backend = stats.get("vector_backend", "memory")
        docs = stats.get("documents", 0)
        if backend not in ("memory", ""):
            # Backend externe : vérifier qu'il est réellement joignable.
            try:
                await asyncio.wait_for(self._rag.list_documents(), timeout=3.0)
            except Exception as exc:  # noqa: BLE001
                return CheckResult(
                    "knowledge", Status.ERROR,
                    f"Base vectorielle {backend} injoignable : {exc}",
                    metadata={"backend": backend},
                )
        if docs == 0:
            return CheckResult(
                "knowledge", Status.WARNING,
                "Aucun document indexé — ingérez un document pour activer le RAG",
                metadata=stats,
            )
        return CheckResult(
            "knowledge", Status.OK,
            f"{docs} document(s), {stats.get('chunks', 0)} chunks "
            f"(backend {backend})",
            metadata=stats,
        )

    async def _check_tools(self) -> CheckResult:
        if self._tool_manager is None:
            return CheckResult(
                "tools", Status.UNAVAILABLE, "ToolManager non initialisé",
            )
        try:
            tools = self._tool_manager.list_tools()
        except Exception as exc:  # noqa: BLE001
            return CheckResult(
                "tools", Status.ERROR, f"Registry des tools en échec : {exc}",
            )
        if not tools:
            return CheckResult("tools", Status.WARNING, "Aucun tool enregistré")
        available = [t for t in tools if getattr(t, "is_available", True)]
        return CheckResult(
            "tools", Status.OK,
            f"{len(available)}/{len(tools)} tool(s) disponibles",
        )

    async def _check_mcp(self) -> CheckResult:
        if self._tool_servers is None:
            return CheckResult(
                "mcp", Status.UNAVAILABLE, "ToolServerManager non initialisé",
            )
        try:
            servers = await self._tool_servers.list()
        except Exception as exc:  # noqa: BLE001
            return CheckResult(
                "mcp", Status.ERROR, f"Liste des serveurs MCP échouée : {exc}",
            )
        if not servers:
            return CheckResult(
                "mcp", Status.OK, "Aucun serveur MCP configuré (optionnel)",
            )
        entries = [
            {
                "name": s.get("name"),
                "url": s.get("url"),
                "enabled": bool(s.get("enabled")),
                "status": s.get("status", "disconnected"),
            }
            for s in servers
        ]
        errored = [e for e in entries if e["enabled"] and e["status"] == "error"]
        if errored:
            return CheckResult(
                "mcp", Status.ERROR,
                f"{len(errored)} serveur(s) MCP en erreur : "
                + ", ".join(str(e["name"]) for e in errored),
                metadata={"servers": entries},
            )
        return CheckResult(
            "mcp", Status.OK,
            f"{len(entries)} serveur(s) MCP configuré(s)",
            metadata={"servers": entries},
        )

    async def _check_plugins(self) -> CheckResult:
        if self._plugins is None:
            return CheckResult(
                "plugins", Status.UNAVAILABLE, "PluginRegistry non initialisée",
            )
        try:
            plugins = await self._plugins.list_plugins()
        except Exception as exc:  # noqa: BLE001
            return CheckResult(
                "plugins", Status.ERROR, f"Catalogue des plugins échoué : {exc}",
            )
        active = [p for p in plugins if p.get("status") == "active"]
        installed = [p for p in plugins if p.get("installed")]
        return CheckResult(
            "plugins", Status.OK,
            f"{len(installed)} installé(s), {len(active)} actif(s) "
            f"sur {len(plugins)} du catalogue",
            metadata={"active": len(active), "installed": len(installed)},
        )

    async def _check_filesystem(self) -> CheckResult:
        path = self._workspace_dir
        if not os.path.isdir(path):
            return CheckResult(
                "filesystem", Status.ERROR,
                f"Répertoire workspace introuvable : {path}",
            )
        probe = os.path.join(path, ".ethan-diag-probe")
        try:
            with open(probe, "w", encoding="utf-8") as fh:
                fh.write("ok")
            os.remove(probe)
        except OSError as exc:
            return CheckResult(
                "filesystem", Status.ERROR,
                f"Workspace non inscriptible : {exc}",
                detail=path,
            )
        return CheckResult(
            "filesystem", Status.OK, "Workspace accessible en lecture/écriture",
            metadata={"path": path},
        )
