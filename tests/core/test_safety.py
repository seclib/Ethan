"""Tests — Safety & Permission Model (ADR-1009)"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from core.events import Event, EventBus, EventType
from core.safety import (
    AuditEvent,
    AuditLogger,
    DefaultAuditLogger,
    DefaultRoleRegistry,
    DefaultSafetyChecker,
    Effect,
    Permission,
    Role,
    RoleRegistry,
    RiskLevel,
    SafetyChecker,
    SafetyContext,
)


@pytest.fixture
def role_registry():
    registry = DefaultRoleRegistry()
    # Setup default roles
    registry.register_role(Role(
        name="user",
        permissions=[
            Permission("read", "read"),
            Permission("write", "write"),
        ]
    ))
    registry.register_role(Role(
        name="admin",
        permissions=[
            Permission("read", "read"),
            Permission("write", "write"),
            Permission("delete", "delete"),
        ],
        inherits=["user"]
    ))
    return registry


@pytest.fixture
def safety_checker(role_registry):
    return DefaultSafetyChecker(role_registry)


@pytest.fixture
def event_bus():
    return EventBus(record_history=True)


@pytest.fixture
def audit_logger(event_bus):
    return DefaultAuditLogger(event_bus)


class TestPermission:
    """Tests for Permission dataclass."""

    def test_create_permission(self):
        """Test permission creation."""
        perm = Permission(resource="file", action="read")
        assert perm.resource == "file"
        assert perm.action == "read"
        assert perm.effect == Effect.ALLOW

    def test_permission_with_deny(self):
        """Test permission with deny effect."""
        perm = Permission(resource="admin", action="delete", effect=Effect.DENY)
        assert perm.effect == Effect.DENY


class TestRole:
    """Tests for Role dataclass."""

    def test_create_role(self):
        """Test role creation."""
        role = Role(
            name="editor",
            permissions=[Permission("doc", "edit")]
        )
        assert role.name == "editor"
        assert len(role.permissions) == 1
        assert role.inherits == []

    def test_role_with_inheritance(self):
        """Test role with inheritance."""
        role = Role(
            name="admin",
            permissions=[Permission("all", "manage")],
            inherits=["user", "editor"]
        )
        assert role.inherits == ["user", "editor"]


class TestSafetyContext:
    """Tests for SafetyContext dataclass."""

    def test_create_context(self):
        """Test safety context creation."""
        context = SafetyContext(
            user_id="user_123",
            roles=["user"]
        )
        assert context.user_id == "user_123"
        assert context.roles == ["user"]
        assert context.risk_level == RiskLevel.LOW
        assert context.metadata is None

    def test_context_with_metadata(self):
        """Test safety context with metadata."""
        context = SafetyContext(
            user_id="user_123",
            roles=["admin"],
            risk_level=RiskLevel.HIGH,
            metadata={"ip": "192.168.1.1"}
        )
        assert context.risk_level == RiskLevel.HIGH
        assert context.metadata == {"ip": "192.168.1.1"}


class TestRoleRegistry:
    """Tests for RoleRegistry."""

    def test_register_role(self, role_registry):
        """Test role registration."""
        role = Role(name="guest", permissions=[Permission("public", "read")])
        role_registry.register_role(role)
        assert "guest" in role_registry.list_roles()

    def test_get_role(self, role_registry):
        """Test getting a role."""
        role = role_registry.get_role("user")
        assert role.name == "user"
        assert len(role.permissions) == 2

    def test_get_role_not_found(self, role_registry):
        """Test getting a non-existent role."""
        with pytest.raises(ValueError, match="Role 'nonexistent' not found"):
            role_registry.get_role("nonexistent")

    def test_list_roles(self, role_registry):
        """Test listing roles."""
        roles = role_registry.list_roles()
        assert "user" in roles
        assert "admin" in roles


class TestSafetyChecker:
    """Tests for SafetyChecker."""

    @pytest.mark.asyncio
    async def test_check_permission_allowed(self, safety_checker):
        """Test permission check - allowed."""
        context = SafetyContext(user_id="user_123", roles=["user"])
        
        allowed = await safety_checker.check_permission(context, "read", "read")
        assert allowed is True

    @pytest.mark.asyncio
    async def test_check_permission_denied(self, safety_checker):
        """Test permission check - denied."""
        context = SafetyContext(user_id="user_123", roles=["user"])
        
        allowed = await safety_checker.check_permission(context, "delete", "delete")
        assert allowed is False

    @pytest.mark.asyncio
    async def test_check_permission_admin(self, safety_checker):
        """Test permission check - admin role."""
        context = SafetyContext(user_id="admin_123", roles=["admin"])
        
        allowed = await safety_checker.check_permission(context, "delete", "delete")
        assert allowed is True

    @pytest.mark.asyncio
    async def test_check_permission_deny_by_default(self, safety_checker):
        """Test permission check - deny by default."""
        context = SafetyContext(user_id="user_123", roles=["user"])
        
        allowed = await safety_checker.check_permission(context, "admin", "manage")
        assert allowed is False

    @pytest.mark.asyncio
    async def test_check_permission_role_inheritance(self, safety_checker):
        """Test permission check with role inheritance."""
        context = SafetyContext(user_id="admin_123", roles=["admin"])
        
        # Admin inherits from user, so should have read permission
        allowed = await safety_checker.check_permission(context, "read", "read")
        assert allowed is True

    @pytest.mark.asyncio
    async def test_assess_risk_low(self, safety_checker):
        """Test risk assessment - low risk."""
        context = SafetyContext(user_id="user_123", roles=["user"])
        
        risk = await safety_checker.assess_risk(context, "read")
        assert risk == RiskLevel.LOW

    @pytest.mark.asyncio
    async def test_assess_risk_high(self, safety_checker):
        """Test risk assessment - high risk."""
        context = SafetyContext(user_id="user_123", roles=["user"])
        
        risk = await safety_checker.assess_risk(context, "delete_data")
        assert risk == RiskLevel.HIGH

    @pytest.mark.asyncio
    async def test_assess_risk_critical_user(self, safety_checker):
        """Test risk assessment - critical user."""
        context = SafetyContext(
            user_id="user_123",
            roles=["user"],
            risk_level=RiskLevel.CRITICAL
        )
        
        risk = await safety_checker.assess_risk(context, "read")
        assert risk == RiskLevel.CRITICAL


class TestAuditLogger:
    """Tests for AuditLogger."""

    @pytest.mark.asyncio
    async def test_audit_log(self, audit_logger, event_bus):
        """Test audit logging."""
        await audit_logger.log(
            user_id="user_123",
            action="read",
            resource="file",
            result="success",
            risk_level=RiskLevel.LOW
        )
        
        # Check that event was published
        history = event_bus.get_history(EventType.SECURITY_AUDIT)
        assert len(history) == 1
        assert history[0].data["user_id"] == "user_123"
        assert history[0].data["action"] == "read"

    @pytest.mark.asyncio
    async def test_audit_log_with_metadata(self, audit_logger, event_bus):
        """Test audit logging with metadata."""
        await audit_logger.log(
            user_id="user_123",
            action="write",
            resource="file",
            result="success",
            risk_level=RiskLevel.MEDIUM,
            metadata={"size": 1024}
        )
        
        history = event_bus.get_history(EventType.SECURITY_AUDIT)
        assert len(history) == 1
        assert history[0].data["metadata"] == {"size": 1024}

    @pytest.mark.asyncio
    async def test_audit_log_high_risk(self, audit_logger, event_bus):
        """Test audit logging for high risk action."""
        await audit_logger.log(
            user_id="admin_123",
            action="delete",
            resource="database",
            result="success",
            risk_level=RiskLevel.HIGH
        )
        
        history = event_bus.get_history(EventType.SECURITY_AUDIT)
        assert len(history) == 1
        assert history[0].data["risk_level"] == RiskLevel.HIGH


class TestSafetyIntegration:
    """Integration tests for safety system."""

    @pytest.mark.asyncio
    async def test_full_safety_flow(self, role_registry, event_bus):
        """Test complete safety flow: check permission + audit."""
        safety_checker = DefaultSafetyChecker(role_registry)
        audit_logger = DefaultAuditLogger(event_bus)
        
        # User context
        context = SafetyContext(user_id="user_123", roles=["user"])
        
        # Check permission
        allowed = await safety_checker.check_permission(context, "read", "read")
        assert allowed is True
        
        # Assess risk
        risk = await safety_checker.assess_risk(context, "read")
        assert risk == RiskLevel.LOW
        
        # Audit
        await audit_logger.log(
            user_id="user_123",
            action="read",
            resource="file",
            result="success",
            risk_level=risk
        )
        
        # Verify audit event
        history = event_bus.get_history(EventType.SECURITY_AUDIT)
        assert len(history) == 1

    @pytest.mark.asyncio
    async def test_admin_workflow(self, role_registry, event_bus):
        """Test admin workflow with high-risk action."""
        safety_checker = DefaultSafetyChecker(role_registry)
        audit_logger = DefaultAuditLogger(event_bus)
        
        context = SafetyContext(user_id="admin_123", roles=["admin"])
        
        # Check permission for delete
        allowed = await safety_checker.check_permission(context, "delete", "delete")
        assert allowed is True
        
        # Assess risk
        risk = await safety_checker.assess_risk(context, "delete")
        assert risk == RiskLevel.HIGH
        
        # Audit
        await audit_logger.log(
            user_id="admin_123",
            action="delete",
            resource="database",
            result="success",
            risk_level=risk
        )
        
        history = event_bus.get_history(EventType.SECURITY_AUDIT)
        assert len(history) == 1
        assert history[0].data["risk_level"] == RiskLevel.HIGH