# Jarvis OS — Authentication & Authorization
# Système d'authentification unifié avec support JWT, API Keys et RBAC

import hashlib
import hmac
import logging
import secrets
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

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
class User:
    """Utilisateur."""
    id: str
    username: str
    roles: list[str] = field(default_factory=list)
    permissions: list[Permission] = field(default_factory=list)
    api_keys: list[str] = field(default_factory=list)
    is_active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Role:
    """Rôle avec permissions associées."""
    name: str
    permissions: list[Permission] = field(default_factory=list)
    description: str = ""


class AuthSystem:
    """Système d'authentification et d'autorisation.

    Supporte :
    - API Keys (Bearer token)
    - JWT Tokens
    - RBAC (Role-Based Access Control)
    - Rate limiting par utilisateur
    """

    def __init__(self):
        self._users: dict[str, User] = {}
        self._roles: dict[str, Role] = {}
        self._api_keys: dict[str, str] = {}  # key_hash -> user_id
        self._rate_limits: dict[str, list[float]] = {}  # user_id -> [timestamps]

        # Default roles
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

    def create_user(self, username: str, roles: list[str] | None = None) -> User:
        """Create a new user."""
        user_id = f"user_{secrets.token_hex(8)}"
        user = User(
            id=user_id,
            username=username,
            roles=roles or ["user"],
        )
        # Assign permissions from roles
        for role_name in user.roles:
            if role_name in self._roles:
                for perm in self._roles[role_name].permissions:
                    if perm not in user.permissions:
                        user.permissions.append(perm)

        self._users[user_id] = user
        logger.info(f"Created user: {username} ({user_id})")
        return user

    def generate_api_key(self, user_id: str) -> str:
        """Generate an API key for a user."""
        if user_id not in self._users:
            raise ValueError(f"User '{user_id}' not found")

        api_key = f"jarvis_{secrets.token_hex(32)}"
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        self._api_keys[key_hash] = user_id
        self._users[user_id].api_keys.append(api_key[:16])  # Store partial for display

        logger.info(f"Generated API key for user {user_id}")
        return api_key

    def validate_api_key(self, api_key: str) -> User | None:
        """Validate an API key and return the associated user."""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        user_id = self._api_keys.get(key_hash)
        if user_id and user_id in self._users:
            user = self._users[user_id]
            if user.is_active:
                return user
        return None

    def check_permission(self, user: User, permission: Permission) -> bool:
        """Check if a user has a specific permission."""
        return permission in user.permissions

    def check_permissions(self, user: User, permissions: list[Permission], require_all: bool = True) -> bool:
        """Check if a user has multiple permissions."""
        if require_all:
            return all(p in user.permissions for p in permissions)
        return any(p in user.permissions for p in permissions)

    def add_role(self, name: str, permissions: list[Permission], description: str = "") -> Role:
        """Create or update a role."""
        role = Role(name=name, permissions=permissions, description=description)
        self._roles[name] = role
        return role

    def assign_role(self, user_id: str, role_name: str) -> bool:
        """Assign a role to a user."""
        if user_id not in self._users or role_name not in self._roles:
            return False

        user = self._users[user_id]
        if role_name not in user.roles:
            user.roles.append(role_name)
            for perm in self._roles[role_name].permissions:
                if perm not in user.permissions:
                    user.permissions.append(perm)
        return True

    def revoke_role(self, user_id: str, role_name: str) -> bool:
        """Revoke a role from a user."""
        if user_id not in self._users:
            return False

        user = self._users[user_id]
        if role_name in user.roles:
            user.roles.remove(role_name)
            # Recalculate permissions from remaining roles
            user.permissions = []
            for r in user.roles:
                if r in self._roles:
                    for perm in self._roles[r].permissions:
                        if perm not in user.permissions:
                            user.permissions.append(perm)
            return True
        return False

    def check_rate_limit(self, user_id: str, max_requests: int = 60, window: int = 60) -> bool:
        """Check if a user has exceeded their rate limit.

        Args:
            user_id: The user to check
            max_requests: Maximum requests allowed in the window
            window: Time window in seconds

        Returns:
            True if the request is allowed, False if rate limited
        """
        now = time.time()
        if user_id not in self._rate_limits:
            self._rate_limits[user_id] = []

        # Remove old entries
        self._rate_limits[user_id] = [
            t for t in self._rate_limits[user_id]
            if now - t < window
        ]

        if len(self._rate_limits[user_id]) >= max_requests:
            return False

        self._rate_limits[user_id].append(now)
        return True


# Global auth system instance
system = AuthSystem()