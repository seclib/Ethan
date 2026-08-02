# ETHAN OS — Role-Based Access Control (RBAC) Engine
# Système d'autorisation interne du Kernel.

import logging
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class Permission(Enum):
    """Permissions disponibles."""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    CHAT = "chat"
    AGENTS = "agents"
    MEMORY = "memory"
    PLUGINS = "plugins"
    SETTINGS = "settings"
    FILES = "files"
    EXECUTE = "execute"


@dataclass
class Role:
    """Rôle avec permissions associées."""
    name: str
    permissions: list[Permission] = field(default_factory=list)
    description: str = ""


class RBACEngine:
    """Moteur de règles RBAC (Role-Based Access Control).
    
    Ce système gère uniquement la définition des rôles et de leurs permissions.
    L'authentification des utilisateurs (JWT, API Keys) est gérée au niveau de l'API Gateway.
    """

    def __init__(self):
        self._roles: dict[str, Role] = {}
        self._init_default_roles()

    def _init_default_roles(self) -> None:
        """Initialize default roles."""
        self._roles["admin"] = Role(
            name="admin",
            permissions=list(Permission),
            description="Full access to all resources",
        )
        self._roles["user"] = Role(
            name="user",
            permissions=[Permission.READ, Permission.WRITE, Permission.CHAT, Permission.MEMORY],
            description="Standard user access",
        )
        self._roles["viewer"] = Role(
            name="viewer",
            permissions=[Permission.READ, Permission.CHAT],
            description="Read-only access",
        )

    def add_role(self, name: str, permissions: list[Permission], description: str = "") -> Role:
        """Create or update a role."""
        role = Role(name=name, permissions=permissions, description=description)
        self._roles[name] = role
        return role

    def get_role(self, name: str) -> Role | None:
        """Get a role by name."""
        return self._roles.get(name)

    def has_permission(self, role_name: str, permission: Permission) -> bool:
        """Check if a role has a specific permission."""
        role = self._roles.get(role_name)
        if not role:
            return False
        return permission in role.permissions

    def has_permissions(self, role_name: str, permissions: list[Permission], require_all: bool = True) -> bool:
        """Check if a role has multiple permissions."""
        role = self._roles.get(role_name)
        if not role:
            return False
            
        if require_all:
            return all(p in role.permissions for p in permissions)
        return any(p in role.permissions for p in permissions)


# Global RBAC engine instance
rbac = RBACEngine()