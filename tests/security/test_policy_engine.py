"""Tests du Policy Engine et du Policy Guard.

Vérifie les axiomes A1..A6 de `docs/security/03-policy-hierarchy.md` :
- A1 ordre total (niveau le plus fort gagne)
- A2 non-annulation (un niveau inférieur ne peut pas annuler un supérieur)
- A3 conflit intra-niveau (la plus restrictive gagne)
- A4 fail-closed (silence = refus)
- A5 pas d'inférence (lire ≠ écrire)
- A6 neutralité du demandeur

Vérifie aussi que le garde est **non contournable** : une action interdite
ne déclenche jamais le callback d'exécution.
"""

from __future__ import annotations

import asyncio

import pytest
from core.security.policy import (
    ActionCategory,
    Policy,
    PolicyConfirmationRequiredError,
    PolicyDecision,
    PolicyDeniedError,
    PolicyEffect,
    PolicyEngine,
    PolicyGuard,
    PolicyLevel,
    PolicyRequest,
    PolicyResult,
)

# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def engine() -> PolicyEngine:
    """Moteur avec les règles par défaut (CORE + SECURITY)."""
    return PolicyEngine()


@pytest.fixture
def guard(engine: PolicyEngine) -> PolicyGuard:
    """Garde sans approver : REQUIRE_CONFIRMATION → refus (fail-closed)."""
    return PolicyGuard(engine)


# ── ALLOW ─────────────────────────────────────────────────────────────


class TestAllow:
    def test_read_workspace_allowed(self, engine: PolicyEngine) -> None:
        """Lecture dans /workspace : ALLOW."""
        d = engine.check("filesystem", "read", "/workspace/README.md")
        assert d.result is PolicyResult.ALLOW
        assert d.allowed
        assert d.reason

    def test_memory_read_allowed(self, engine: PolicyEngine) -> None:
        """Lecture mémoire utilisateur : ALLOW."""
        d = engine.check("memory", "read", "user:alice")
        assert d.result is PolicyResult.ALLOW

    def test_guard_executes_allowed_action(self, guard: PolicyGuard) -> None:
        """ALLOW → le callback est exécuté."""
        ran: list = []

        async def read_file(path: str) -> str:
            ran.append(path)
            return f"content:{path}"

        result = asyncio.run(
            guard.execute("filesystem", "read", "/workspace/a.txt", read_file,
                          params={"path": "/workspace/a.txt"})
        )
        assert result == "content:/workspace/a.txt"
        assert ran == ["/workspace/a.txt"]


# ── DENY ──────────────────────────────────────────────────────────────


class TestDeny:
    def test_shell_destructive_denied(self, engine: PolicyEngine) -> None:
        """Commande destructive : DENY (CORE)."""
        d = engine.check("shell", "execute", "rm -rf /tmp")
        assert d.result is PolicyResult.DENY
        assert d.level is PolicyLevel.CORE

    def test_docker_denied_by_default(self, engine: PolicyEngine) -> None:
        """Docker : DENY par défaut (aucun accès élargi)."""
        d = engine.check("docker", "execute", "run nginx")
        assert d.result is PolicyResult.DENY

    def test_config_constitution_denied(self, engine: PolicyEngine) -> None:
        """Modification de la Constitution : DENY (CORE, PR-4)."""
        d = engine.check("configuration", "write", "constitution:core-1")
        assert d.result is PolicyResult.DENY
        assert d.level is PolicyLevel.CORE

    def test_guard_blocks_denied_and_never_calls(self, guard: PolicyGuard) -> None:
        """DENY → exception levée et callback JAMAIS appelé."""
        ran: list = []

        def dangerous(path: str) -> str:
            ran.append(path)
            return "executed"

        with pytest.raises(PolicyDeniedError):
            asyncio.run(
                guard.execute("shell", "execute", "rm -rf /tmp", dangerous,
                              params={"path": "/tmp"})
            )
        assert ran == [], "le callback ne doit jamais être exécuté sur DENY"


# ── REQUIRE_CONFIRMATION ──────────────────────────────────────────────


class TestRequireConfirmation:
    def test_filesystem_delete_requires_confirmation(
        self, engine: PolicyEngine
    ) -> None:
        """Suppression de fichier : REQUIRE_CONFIRMATION (PR-7)."""
        d = engine.check("filesystem", "delete", "/workspace/a.txt")
        assert d.result is PolicyResult.REQUIRE_CONFIRMATION

    def test_network_write_requires_confirmation(self, engine: PolicyEngine) -> None:
        """Transfert réseau : REQUIRE_CONFIRMATION (CR-4)."""
        d = engine.check("network", "write", "https://ext.example.com")
        assert d.result is PolicyResult.REQUIRE_CONFIRMATION

    def test_mcp_execute_requires_confirmation(self, engine: PolicyEngine) -> None:
        """Outil MCP : REQUIRE_CONFIRMATION (source non fiable)."""
        d = engine.check("mcp", "execute", "send_email")
        assert d.result is PolicyResult.REQUIRE_CONFIRMATION

    def test_guard_fail_closed_without_approver(self, guard: PolicyGuard) -> None:
        """Sans approver, REQUIRE_CONFIRMATION → refus, callback non appelé."""
        ran: list = []

        def delete(path: str) -> str:
            ran.append(path)
            return "deleted"

        with pytest.raises(PolicyConfirmationRequiredError):
            asyncio.run(
                guard.execute("filesystem", "delete", "/workspace/a.txt", delete,
                              params={"path": "/workspace/a.txt"})
            )
        assert ran == [], "sans confirmation humaine, jamais d'exécution"

    def test_guard_with_approver_confirming(self, engine: PolicyEngine) -> None:
        """Avec un approver qui approuve, REQUIRE_CONFIRMATION → exécution."""

        async def approving_approver(
            request: PolicyRequest, decision: PolicyDecision
        ) -> bool:
            return True

        guard = PolicyGuard(engine, approver=approving_approver)
        ran: list = []

        def delete(path: str) -> str:
            ran.append(path)
            return "deleted"

        result = asyncio.run(
            guard.execute("filesystem", "delete", "/workspace/a.txt", delete,
                          params={"path": "/workspace/a.txt"})
        )
        assert result == "deleted"
        assert ran == ["/workspace/a.txt"]

    def test_guard_with_approver_rejecting(self, engine: PolicyEngine) -> None:
        """Avec un approver qui refuse → refus, callback non appelé."""

        async def rejecting_approver(
            request: PolicyRequest, decision: PolicyDecision
        ) -> bool:
            return False

        guard = PolicyGuard(engine, approver=rejecting_approver)
        ran: list = []

        def delete(path: str) -> str:
            ran.append(path)
            return "deleted"

        with pytest.raises(PolicyConfirmationRequiredError):
            asyncio.run(
                guard.execute("filesystem", "delete", "/workspace/a.txt", delete,
                              params={"path": "/workspace/a.txt"})
            )
        assert ran == []



# ── CONFLIT DE RÈGLES (A3) ────────────────────────────────────────────


class TestRuleConflict:
    def test_same_level_most_restrictive_wins(self) -> None:
        """À niveau égal, DENY gagne sur ALLOW (A3)."""
        engine = PolicyEngine(rules=[])
        engine.add_rule(Policy(
            id="t.allow", level=PolicyLevel.USER, category="filesystem",
            action="read", resource="/tmp/**", effect=PolicyEffect.ALLOW,
            reason="autorise",
        ))
        engine.add_rule(Policy(
            id="t.deny", level=PolicyLevel.USER, category="filesystem",
            action="read", resource="/tmp/secret*", effect=PolicyEffect.DENY,
            reason="interdit",
        ))
        # Lecture d'un fichier secret : les deux règles matchent,
        # la plus restrictive (DENY) gagne.
        d = engine.check("filesystem", "read", "/tmp/secret.txt")
        assert d.result is PolicyResult.DENY
        assert d.policy_id == "t.deny"

    def test_same_level_confirm_beats_allow(self) -> None:
        """À niveau égal, REQUIRE_CONFIRMATION gagne sur ALLOW."""
        engine = PolicyEngine(rules=[])
        engine.add_rule(Policy(
            id="t.allow", level=PolicyLevel.USER, category="network",
            action="write", resource="*", effect=PolicyEffect.ALLOW,
        ))
        engine.add_rule(Policy(
            id="t.confirm", level=PolicyLevel.USER, category="network",
            action="write", resource="https://*.example.com",
            effect=PolicyEffect.REQUIRE_CONFIRMATION,
        ))
        d = engine.check("network", "write", "https://x.example.com")
        assert d.result is PolicyResult.REQUIRE_CONFIRMATION
        assert d.policy_id == "t.confirm"


# ── PRIORITÉ (A1/A2) ──────────────────────────────────────────────────


class TestPriority:
    def test_higher_level_wins_over_lower(self) -> None:
        """Un niveau supérieur (CORE) gagne sur un niveau inférieur (SECURITY ALLOW)."""
        engine = PolicyEngine(rules=[])
        engine.add_rule(Policy(
            id="sec.allow", level=PolicyLevel.SECURITY, category="configuration",
            action="write", resource="*", effect=PolicyEffect.ALLOW,
            reason="sec autorise",
        ))
        engine.add_rule(Policy(
            id="core.deny", level=PolicyLevel.CORE, category="configuration",
            action="write", resource="constitution:*", effect=PolicyEffect.DENY,
            reason="core interdit",
        ))
        d = engine.check("configuration", "write", "constitution:core-1")
        assert d.result is PolicyResult.DENY
        assert d.level is PolicyLevel.CORE
        assert d.policy_id == "core.deny"

    def test_lower_level_cannot_annul_higher_deny(self) -> None:
        """Un niveau inférieur ne peut pas annuler un DENY du niveau supérieur."""
        engine = PolicyEngine(rules=[])
        engine.add_rule(Policy(
            id="core.deny", level=PolicyLevel.CORE, category="docker",
            action="execute", resource="*", effect=PolicyEffect.DENY,
        ))
        engine.add_rule(Policy(
            id="user.allow", level=PolicyLevel.USER, category="docker",
            action="execute", resource="*", effect=PolicyEffect.ALLOW,
            reason="l'utilisateur autorise",
        ))
        d = engine.check("docker", "execute", "run x")
        assert d.result is PolicyResult.DENY
        assert d.policy_id == "core.deny"

    def test_default_rules_priority(self, engine: PolicyEngine) -> None:
        """Priorité réelle : la Constitution (CORE) domine la config (SECURITY)."""
        # security.config.write = REQUIRE_CONFIRMATION ; core.config.constitution = DENY
        d = engine.check("configuration", "write", "constitution:core-1")
        assert d.result is PolicyResult.DENY
        assert d.level is PolicyLevel.CORE



# ── FAIL-CLOSED (A4) & NON-INFÉRENCE (A5) ─────────────────────────────


class TestFailClosedAndNoInference:
    def test_silence_is_deny(self, engine: PolicyEngine) -> None:
        """Aucune règle ne matche → DENY (A4)."""
        d = engine.check("process", "kill", "12345")
        assert d.result is PolicyResult.DENY

    def test_read_does_not_imply_write(self, engine: PolicyEngine) -> None:
        """Lire ≠ écrire : lecture ALLOW, écriture DENY (A5)."""
        read = engine.check("filesystem", "read", "/workspace/x.txt")
        write = engine.check("filesystem", "write", "/workspace/x.txt")
        assert read.result is PolicyResult.ALLOW
        assert write.result is PolicyResult.DENY

    def test_guard_fail_closed_on_silence(self, guard: PolicyGuard) -> None:
        """Silence = DENY → callback jamais appelé."""
        ran: list = []

        def kill(pid: str) -> str:
            ran.append(pid)
            return "killed"

        with pytest.raises(PolicyDeniedError):
            asyncio.run(
                guard.execute("process", "kill", "12345", kill, params={"pid": "12345"})
            )
        assert ran == []


# ── NEUTRALITÉ DU DEMANDEUR (A6) ──────────────────────────────────────


class TestSourceNeutrality:
    def test_llm_and_user_get_same_decision(self, engine: PolicyEngine) -> None:
        """A6 : la source ne change pas la décision."""
        d_llm = engine.evaluate(PolicyRequest(
            category="shell", action="execute", resource="rm -rf /tmp", source="llm"))
        d_user = engine.evaluate(PolicyRequest(
            category="shell", action="execute", resource="rm -rf /tmp", source="user"))
        d_agent = engine.evaluate(PolicyRequest(
            category="shell", action="execute", resource="rm -rf /tmp", source="agent"))
        d_tool = engine.evaluate(PolicyRequest(
            category="shell", action="execute", resource="rm -rf /tmp", source="tool"))
        d_mcp = engine.evaluate(PolicyRequest(
            category="shell", action="execute", resource="rm -rf /tmp", source="mcp"))

        assert d_llm.result is PolicyResult.DENY
        assert (
            d_llm.result == d_user.result == d_agent.result
            == d_tool.result == d_mcp.result
        )


# ── DÉCISION EXPLICITE & DIAGNOSTIC ───────────────────────────────────


class TestDecisionDetail:
    def test_decision_has_reason_and_matched(self, engine: PolicyEngine) -> None:
        """Chaque décision porte une raison explicite et les règles matchées."""
        d = engine.check("shell", "execute", "rm -rf /tmp")
        assert d.reason
        assert d.policy_id == "core.shell.destructive"
        assert "core.shell.destructive" in d.matched
        # Sérialisable pour l'audit.
        assert d.to_dict()["result"] == "deny"

    def test_evaluate_is_deterministic(self, engine: PolicyEngine) -> None:
        """Même requête → même décision (déterminisme)."""
        a = engine.check("filesystem", "delete", "/workspace/x")
        b = engine.check("filesystem", "delete", "/workspace/x")
        assert a.result is b.result
        assert a.policy_id == b.policy_id



# ── COUVERTURE DES 8 CATÉGORIES ───────────────────────────────────────


class TestActionCategories:
    """Chaque catégorie sensible répond au moteur (et bloque par défaut)."""

    def test_all_categories_covered(self, engine: PolicyEngine) -> None:
        categories = [
            (ActionCategory.FILESYSTEM, "write", "/tmp/x"),
            (ActionCategory.PROCESS, "kill", "12345"),
            (ActionCategory.SHELL, "execute", "curl http://x"),
            (ActionCategory.DOCKER, "execute", "run nginx"),
            (ActionCategory.NETWORK, "write", "https://x.example.com"),
            (ActionCategory.MCP, "execute", "tool_x"),
            (ActionCategory.MEMORY, "write", "user:alice"),
            (ActionCategory.CONFIGURATION, "write", "app:theme"),
        ]
        for category, action, resource in categories:
            d = engine.check(category, action, resource)
            # Aucune catégorie ne doit être ALLOW par défaut pour une action
            # à effet de bord (write/kill/execute) — toutes sont bloquées
            # ou soumises à confirmation.
            assert d.result is not PolicyResult.ALLOW, (
                f"{category}:{action}:{resource} ne doit pas être autorisé par défaut"
            )
            assert d.reason

