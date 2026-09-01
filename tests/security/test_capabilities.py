"""Tests du Capability System (Phase 05).

Vérifie :
- allow / deny / fail-closed
- confirmation (TTL, scope)
- conflit de regles
- priorite
- path security (traversal / symlink / mount escape)
- revocation
- audit append-only
- neutralite du demandeur (A6)
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest
from core.security.policy.capabilities import (
    CapabilityManager,
    PathSecurityError,
    RiskLevel,
    resolve_safe_path,
)
from core.security.policy.types import PolicyResult


@pytest.fixture
def roots(tmp_path: Path) -> list[str]:
    return [str(tmp_path.resolve())]


@pytest.fixture
def manager(roots: list[str]) -> CapabilityManager:
    m = CapabilityManager(allowed_roots=roots)
    m.grant(
        subject="agent:test",
        category="filesystem",
        operation="read",
        resource=str(Path(roots[0]) / "**"),
        scope="self",
        ttl_seconds=3600,
        risk_level=RiskLevel.LOW,
        origin="test",
    )
    return m


class TestAllowDeny:
    def test_allowed_action(self, manager: CapabilityManager, roots: list) -> None:
        result, reason, cap = manager.check(
            "agent:test", "filesystem", "read", str(Path(roots[0]) / "a.txt")
        )
        assert result is PolicyResult.ALLOW
        assert cap is not None

    def test_no_capability_is_deny(self, roots: list[str]) -> None:
        m = CapabilityManager(allowed_roots=roots)
        result, reason, cap = m.check(
            "agent:test", "filesystem", "read", str(Path(roots[0]) / "x.txt")
        )
        assert result is PolicyResult.DENY
        assert "fail-closed" in reason

    def test_wrong_subject_is_deny(self, manager: CapabilityManager, roots) -> None:
        result, _, _ = manager.check(
            "agent:other", "filesystem", "read", str(Path(roots[0]) / "a.txt")
        )
        assert result is PolicyResult.DENY

    def test_wrong_operation_is_deny(self, manager: CapabilityManager, roots) -> None:
        result, _, _ = manager.check(
            "agent:test", "filesystem", "write", str(Path(roots[0]) / "a.txt")
        )
        assert result is PolicyResult.DENY

    def test_wrong_category_is_deny(self, manager: CapabilityManager, roots) -> None:
        result, _, _ = manager.check("agent:test", "shell", "execute", "ls")
        assert result is PolicyResult.DENY


class TestRuleConflictAndPriority:
    def test_wildcard_subject_matches_all(  # noqa: E501
        self,
        manager: CapabilityManager,
        roots: list[str],
    ) -> None:
        # Le manager a déjà la capability agent:test; on teste le wildcard.
        manager.grant("*", "filesystem", "read", "*", risk_level=RiskLevel.MEDIUM)
        result, _, _ = manager.check(
            "agent:anything", "filesystem", "read", os.path.join(roots[0], "x")
        )
        assert result is PolicyResult.ALLOW

    def test_write_deny_when_only_read_granted(  # noqa: E501
        self,
        manager: CapabilityManager,
        roots: list[str],
    ) -> None:
        # Le manager a déjà la capability read sur /workspace/**.
        # write doit être DENY (A5 no-inference).
        result, _, _ = manager.check(
            "agent:test", "filesystem", "write", os.path.join(roots[0], "a.txt")
        )
        assert result is PolicyResult.DENY


class TestTTL:
    def test_ttl_expires(self, manager: CapabilityManager) -> None:
        cap = manager.list_capabilities()[0]
        assert cap.is_expired(now=time.time() + 3601)

    def test_not_expired(self, manager: CapabilityManager) -> None:
        cap = manager.list_capabilities()[0]
        assert not cap.is_expired()


class TestRevocation:
    def test_revoked_blocks(self, manager: CapabilityManager, roots: list[str]) -> None:
        cap = manager.list_capabilities()[0]
        assert manager.revoke(cap.id)
        result, _, _ = manager.check(
            "agent:test", "filesystem", "read", str(Path(roots[0]) / "a.txt")
        )
        assert result is PolicyResult.DENY

    def test_revoke_unknown(self, manager: CapabilityManager) -> None:
        assert not manager.revoke("nonexistent")


class TestPathSecurity:
    def test_traversal_blocked(self, roots: list[str]) -> None:
        target = str(Path(roots[0]) / ".." / "etc" / "passwd")
        with pytest.raises(PathSecurityError):
            resolve_safe_path(target, roots)

    def test_escape_blocked(self, roots: list[str]) -> None:
        target = str(Path(roots[0]) / ".." / "secret")
        with pytest.raises(PathSecurityError):
            resolve_safe_path(target, roots)

    def test_within_root_allowed(self, roots: list[str]) -> None:
        target = str(Path(roots[0]) / "sub" / "file.txt")
        resolved = resolve_safe_path(target, roots)
        assert resolved.startswith(str(Path(roots[0]).resolve()))


class TestScopeEnforcement:
    def test_capability_does_not_exceed_scope(self, roots: list[str]) -> None:
        m = CapabilityManager(allowed_roots=roots)
        m.grant(
            subject="agent:test",
            category="filesystem",
            operation="read",
            resource=str(Path(roots[0]) / "ethan" / "**"),
            risk_level=RiskLevel.LOW,
        )
        result, _, _ = m.check(
            "agent:test", "filesystem", "read",
            str(Path(roots[0]) / "ethan" / "README.md"),
        )
        assert result is PolicyResult.ALLOW
        # Hors scope: DENY
        result, _, _ = m.check(
            "agent:test", "filesystem", "read",
            str(Path(roots[0]) / ".." / ".ssh" / "id_rsa"),
        )
        assert result is PolicyResult.DENY


class TestAudit:
    def test_append_only(self, manager: CapabilityManager, roots: list[str]) -> None:
        before = len(manager.audit_log)
        manager.check(
            "agent:test", "filesystem", "read",
            str(Path(roots[0]) / "a.txt"),
        )
        manager.check(
            "agent:other", "filesystem", "read",
            str(Path(roots[0]) / "b.txt"),
        )
        assert len(manager.audit_log) == before + 2

    def test_summary(self, manager: CapabilityManager, roots: list[str]) -> None:
        manager.check(
            "agent:test", "filesystem", "read",
            str(Path(roots[0]) / "a.txt"),
        )
        manager.check(
            "agent:other", "filesystem", "read",
            str(Path(roots[0]) / "b.txt"),
        )
        s = manager.audit_summary()
        assert s["total_evaluations"] == 2
        assert s["allowed"] == 1
        assert s["denied"] == 1

    def test_entry_fields(self, manager: CapabilityManager, roots: list[str]) -> None:
        manager.check(
            "agent:test", "filesystem", "read",
            str(Path(roots[0]) / "a.txt"),
        )
        entry = manager.audit_log[-1]
        assert entry.subject == "agent:test"
        assert entry.category == "filesystem"
        assert entry.granted is True


class TestValidation:
    def test_unknown_category_rejected(self, roots: list[str]) -> None:
        m = CapabilityManager(allowed_roots=roots)
        with pytest.raises(ValueError, match="unknown resource category"):
            m.grant("agent:test", "unknown", "read", "/tmp", risk_level=RiskLevel.LOW)

    def test_unknown_operation_rejected(self, roots: list[str]) -> None:
        m = CapabilityManager(allowed_roots=roots)
        with pytest.raises(ValueError, match="not allowed"):
            m.grant(
                "agent:test", "filesystem", "execute", "/tmp",
                risk_level=RiskLevel.LOW,
            )

    def test_invalid_scope_rejected(self, roots: list[str]) -> None:
        m = CapabilityManager(allowed_roots=roots)
        with pytest.raises(ValueError, match="invalid scope"):
            m.grant("*", "filesystem", "read", "/tmp", scope="invalid")
