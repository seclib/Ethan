"""Tests de câblage production — Policy Engine branché sur la composition API.

Vérifie le pattern utilisé par ``interfaces/api/main.py`` :

    enforcer = build_secure_enforcer()
    ToolManager(store=…, policy_enforcer=enforcer)

Garantie : avec ce câblage, un tool interdit par la hiérarchie (ex. docker,
``rm -rf``) est renvoyé ``rejected`` par le ``ToolExecutor`` du manager —
aucun chemin (routeur /tools, skills) ne peut l'exécuter.
"""

from __future__ import annotations

import asyncio

from core.security.integration import build_secure_enforcer
from core.security.policy.capabilities import RiskLevel
from core.tools.manager import ToolManager
from core.tools.types import Tool, ToolContext


def _tool(category: str, name: str = "t", risk: str = "low") -> Tool:
    return Tool(
        id=f"{name}-{category}",
        name=name,
        description="test tool",
        category=category,
        risk_level=risk,  # type: ignore[arg-type]
    )


def _context(user: str = "alice", source: str = "llm") -> ToolContext:
    return ToolContext(query="", source=source, user_id=user)


def test_toolmanager_with_secure_enforcer_rejects_forbidden_tool() -> None:
    """Le câblage production bloque réellement un tool interdit (docker)."""

    async def _run() -> None:
        enforcer = build_secure_enforcer()
        manager = ToolManager(policy_enforcer=enforcer)
        result = await manager.executor.execute(
            _tool("docker", risk="critical"), {"command": "run nginx"}, _context()
        )
        assert result.status == "rejected"
        assert result.error  # raison explicite
        assert result.metadata.get("rejected") is True

    asyncio.run(_run())


def test_toolmanager_with_secure_enforcer_rejects_uncategorized() -> None:
    """A4 fail-closed : un tool sans règle applicative est rejeté (silence = deny)."""

    async def _run() -> None:
        enforcer = build_secure_enforcer()
        manager = ToolManager(policy_enforcer=enforcer)
        result = await manager.executor.execute(
            _tool("generic", name="noop"), {"x": 1}, _context()
        )
        # Aucune règle n'autorise explicitement cette catégorie/action :
        # fail-closed, l'exécution est refusée même pour un tool « inoffensif ».
        assert result.status == "rejected"

    asyncio.run(_run())


def test_toolmanager_with_secure_enforcer_allows_workspace_read() -> None:
    """ALLOW réel : lecture filesystem dans /workspace (base.fs.read.workspace)
    **et** capability accordée pour le sujet (Phase 05 : policy ALLOW + capability
    active → exécution ; policy DENY ou capability absente → rejet fail-closed."""

    async def _run() -> None:
        enforcer = build_secure_enforcer()
        # Phase 05 : accorder une capability granulaire au sujet 'user:alice'.
        enforcer._capabilities.grant(  # noqa: SLF001 — accès interne test
            subject="user:alice",
            category="filesystem",
            operation="read",
            resource="/workspace/**",
            scope="self",
            ttl_seconds=3600,
                        risk_level=RiskLevel.LOW,
        )
        manager = ToolManager(policy_enforcer=enforcer)
        result = await manager.executor.execute(
            _tool("filesystem", name="reader"),
            {"action": "read", "path": "/workspace/notes.txt"},
            _context(user="alice"),
        )
        # Builtin MVP : la simulation d'exécution réussit une fois autorisé.
        assert result.status == "success"

    asyncio.run(_run())


def test_toolmanager_capability_scope_cannot_exceed() -> None:
    """Critère de validation Phase 05 : une capability accordée pour
    ``/workspace/**`` ne permet **jamais** de lire en dehors (ex. ``~/.ssh``).
    La policy base.fs.read.workspace n'autorise que /workspace/** → la capability
    est le second contrôle et refute techniquement tout dépassement de portée."""

    async def _run() -> None:
        enforcer = build_secure_enforcer()
        enforcer._capabilities.grant(  # noqa: SLF001
            subject="user:alice", category="filesystem", operation="read",
            resource="/workspace/**", scope="self", ttl_seconds=3600, risk_level=RiskLevel.LOW,
        )
        manager = ToolManager(policy_enforcer=enforcer)
        # /workspace/notes.txt : OK (policy + capability)
        ok = await manager.executor.execute(
            _tool("filesystem", name="reader"), {"action": "read", "path": "/workspace/notes.txt"},
            _context(user="alice"),
        )
        assert ok.status == "success"
        # ../../.ssh/id_rsa → refus (capability ne couvre pas, policy non matchante,
        # resolve_safe_path / capability scope => DENY)
        bad = await manager.executor.execute(
            _tool("filesystem", name="reader"), {"action": "read", "path": "/workspace/../../.ssh/id_rsa"},
            _context(user="alice"),
        )
        assert bad.status == "rejected"
        assert "fail-closed" in (bad.error or "")

    asyncio.run(_run())


def test_toolmanager_capability_lower_than_constitution_deny() -> None:
    """A2/A6 : une capability ne peut pas annuler une règle CORE supérieure.
    rm -rf est interdit au niveau CORE(1) → capability rm (niveau plus bas) est ignorée."""

    async def _run() -> None:
        enforcer = build_secure_enforcer()
        # On tente d'accorder une capability pour rm -rf (elle doit être ignorée).
        enforcer._capabilities.grant(  # noqa: SLF001
            subject="*", category="shell", operation="execute",
            resource="rm -rf*", scope="self", ttl_seconds=3600, risk_level=RiskLevel.CRITICAL,
        )
        manager = ToolManager(policy_enforcer=enforcer)
        result = await manager.executor.execute(
            _tool("shell", name="sh"), {"command": "rm -rf /tmp/x"}, _context()
        )
        assert result.status == "rejected"
        assert "destructive" in (result.error or "").lower()

    asyncio.run(_run())
