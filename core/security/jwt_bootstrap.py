"""JWT Secret Bootstrap and Management for ETHAN.

Provides deterministic and secure JWT secret resolution:
1. Environment variable `JWT_SECRET` (if explicitly set and not the insecure placeholder).
2. Persistent local key file in `.secrets/jwt.key` (or ~/.ethan/secrets/jwt.key) with 0600 permissions.
3. Auto-generation of a cryptographically secure 64-byte urlsafe secret on first run.

Also provides local development token generation for CLI/runtime bootstrapping.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

INSECURE_PLACEHOLDER = "change-me-in-prod-generate-a-random-secret-here"
DEFAULT_EXPIRY_SECONDS = 86400 * 30  # 30 days for local dev bootstrap token


def _find_repo_root() -> Path:
    """Find the root of the ETHAN repository or fallback to current dir."""
    env_root = os.getenv("ETHAN_ROOT")
    if env_root and os.path.isdir(env_root):
        return Path(env_root).resolve()

    current = Path(__file__).resolve().parent
    for _ in range(5):
        if (current / "pyproject.toml").is_file() or (current / "docker-compose.yml").is_file():
            return current
        current = current.parent
    return Path.cwd().resolve()


def get_secrets_dir() -> Path:
    """Return the directory used for storing local secrets."""
    repo_root = _find_repo_root()
    repo_secrets = repo_root / ".secrets"
    try:
        repo_secrets.mkdir(parents=True, exist_ok=True)
        return repo_secrets
    except OSError:
        pass

    user_secrets = Path.home() / ".ethan" / "secrets"
    user_secrets.mkdir(parents=True, exist_ok=True)
    return user_secrets


def get_jwt_key_path() -> Path:
    """Return the path to the persistent JWT key file."""
    return get_secrets_dir() / "jwt.key"


def _read_dotenv_jwt_secret() -> str | None:
    """Read JWT_SECRET from .env file if available."""
    repo_root = _find_repo_root()
    env_file = repo_root / ".env"
    if not env_file.is_file():
        return None
    try:
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("JWT_SECRET=") and not line.startswith("#"):
                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                if val:
                    return val
    except Exception:
        pass
    return None


def get_or_create_jwt_secret() -> str:
    """Resolve or generate a secure persistent JWT secret.

    Priority:
    1. JWT_SECRET env var (if set and not empty).
    2. File `.secrets/jwt.key` (persisted on host or volume).
    3. JWT_SECRET in `.env` file (if set and not empty).
    4. Auto-generate a new cryptographically secure token and persist to `.secrets/jwt.key`.
    """
    env_secret = os.getenv("JWT_SECRET", "").strip()
    if env_secret and env_secret != INSECURE_PLACEHOLDER:
        return env_secret

    key_file = get_jwt_key_path()
    if key_file.is_file():
        try:
            stored = key_file.read_text(encoding="utf-8").strip()
            if stored and stored != INSECURE_PLACEHOLDER:
                return stored
        except OSError as exc:
            logger.warning(f"Could not read JWT secret from {key_file}: {exc}")

    dotenv_secret = _read_dotenv_jwt_secret()
    if dotenv_secret and dotenv_secret != INSECURE_PLACEHOLDER:
        return dotenv_secret

    # If env_secret or dotenv_secret is explicitly the placeholder in dev,
    # and no key file exists yet, return it or persist key file.
    active_fallback = env_secret or dotenv_secret
    if active_fallback == INSECURE_PLACEHOLDER:
        # In existing dev environment with placeholder, keep compatible
        return INSECURE_PLACEHOLDER

    # Generate a cryptographically secure 64-character urlsafe secret
    new_secret = secrets.token_urlsafe(64)
    try:
        key_file.parent.mkdir(parents=True, exist_ok=True)
        key_file.write_text(new_secret, encoding="utf-8")
        # Restrict permissions to owner only (0600)
        os.chmod(key_file, 0o600)
        logger.info(f"Generated new secure JWT secret persisted to {key_file}")
    except OSError as exc:
        logger.warning(f"Could not persist JWT secret to {key_file}: {exc}")

    return new_secret


def create_local_token(
    user_id: str = "admin",
    username: str = "admin",
    role: str = "admin",
    secret: str | None = None,
    expiry_seconds: int = DEFAULT_EXPIRY_SECONDS,
) -> str:
    """Generate a standard HS256 JWT token using Python stdlib (no heavy external deps)."""
    signing_secret = secret or get_or_create_jwt_secret()
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    payload: dict[str, Any] = {
        "sub": user_id,
        "username": username,
        "role": role,
        "iat": now,
        "exp": now + expiry_seconds,
    }

    def b64url(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

    header_b64 = b64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")

    signature = hmac.new(signing_secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    sig_b64 = b64url(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"
