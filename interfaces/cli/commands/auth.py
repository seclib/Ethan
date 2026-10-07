"""ETHAN auth — login session (API) + admin management.

Usage:
    ethan auth login                  Login via Core API (stores JWT locally)
    ethan auth status                 Show the current session (who am I)
    ethan auth logout                 Invalidate the local session
    ethan auth create-admin           Create an interactive admin account (legacy, direct DB)
    ethan auth list                   List existing users (legacy, direct DB)
    ethan auth reset-password <user>  Reset a user's password (legacy, direct DB)

`login/status/logout` pass through the Core API (`/auth/*`) — the interface
never talks to PostgreSQL for sessions.  The create/list/reset trio still
uses direct DB access and is a known architecture debt (see audit) until a
first-admin bootstrap endpoint exists in Core.
"""

import asyncio
import os
import sys

from interfaces.cli.registry import register
from interfaces.cli.core.ux import UX

KNOWN_AUTH_SUBS = ["login", "logout", "status", "create-admin", "list", "reset-password"]


def _direct_db_guard(rest: list) -> int | None:
    """Garde-fou P1 : l'administration DB directe contourne la frontière API.

    Refusée par défaut (mot de passe `change-me-in-prod` ou flag absent) :
    seul `--i-understand-direct-db` l'autorise, en attendant le bootstrap
    admin côté Core API. Retourne un exit code en cas de refus, None sinon.
    """
    if "--i-understand-direct-db" in rest:
        return None
    print(
        "Error: direct database administration is disabled by default — "
        "it bypasses the Core API boundary.",
        file=sys.stderr,
    )
    print(
        "Hint: wait for the Core first-admin bootstrap endpoint, or re-run "
        "with --i-understand-direct-db after setting a real POSTGRES_PASSWORD.",
        file=sys.stderr,
    )
    return 4


def _get_db_url() -> str:
    """Resolve DATABASE_URL for local CLI execution.

    Inside Docker the host is ``postgres``; for local CLI usage we need
    ``localhost``.  We honour an explicit ``$DATABASE_URL`` and only rewrite
    the default when the env var is unset.
    """
    url = os.getenv("DATABASE_URL")
    if url:
        return url.replace("@postgres:", "@localhost:")
    password = os.getenv("POSTGRES_PASSWORD")
    if not password or password == "change-me-in-prod":
        raise RuntimeError(
            "refusing direct DB access with the default POSTGRES_PASSWORD "
            "(set a real POSTGRES_PASSWORD or DATABASE_URL)"
        )
    return f"postgresql://ethan:{password}@localhost:5432/ethan"


def _hash_password(password: str) -> str:
    import bcrypt

    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _validate_password(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    if not (has_upper and has_lower and has_digit):
        return False, "Password must contain uppercase, lowercase, and a digit."
    return True, ""


def _create_admin(args):
    """Interactively create an admin user."""
    import getpass

    print("\n── Create ETHAN Admin Account ──\n")
    username = input("Username: ").strip()
    if not username:
        print("Error: Username is required.")
        return 1

    password = getpass.getpass("Password: ")
    if not password:
        print("Error: Password is required.")
        return 1

    is_valid, error = _validate_password(password)
    if not is_valid:
        print(f"Error: {error}")
        return 1

    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("Error: Passwords do not match.")
        return 1

    password_hash = _hash_password(password)

    async def _create():
        import asyncpg

        conn = await asyncio.wait_for(asyncpg.connect(_get_db_url()), timeout=5.0)
        try:
            existing = await conn.fetchrow("SELECT id FROM users WHERE username = $1", username)
            if existing:
                print(f"Error: User '{username}' already exists.")
                return 1
            await conn.execute(
                "INSERT INTO users (username, password_hash, roles, is_active) VALUES ($1, $2, $3, $4)",  # noqa: E501
                username,
                password_hash,
                ["admin"],
                True,
            )
            print(f"\n✓ Admin user '{username}' created successfully.")
            print("  Role: admin")
            print("  Login at: http://localhost:3001")
            return 0
        finally:
            await conn.close()

    try:
        return asyncio.run(_create())
    except Exception as exc:
        print(f"Error: Failed to create admin — {exc}")
        return 1


def _list_users(args):
    """List existing users."""

    async def _list():
        import asyncpg

        conn = await asyncio.wait_for(asyncpg.connect(_get_db_url()), timeout=5.0)
        try:
            rows = await conn.fetch(
                "SELECT username, roles, is_active, created_at FROM users ORDER BY created_at"
            )
            if not rows:
                print("No users found.")
                return 0
            print(f"\n{'Username':<25} {'Roles':<15} {'Active':<8} {'Created'}")
            print("─" * 70)
            for row in rows:
                roles = ", ".join(row["roles"])
                active = "✓" if row["is_active"] else "✗"
                created = row["created_at"].strftime("%Y-%m-%d %H:%M")
                print(f"{row['username']:<25} {roles:<15} {active:<8} {created}")
            print()
            return 0
        finally:
            await conn.close()

    try:
        return asyncio.run(_list())
    except Exception as exc:
        print(f"Error: Failed to list users — {exc}")
        return 1


def _reset_password(args):
    """Reset a user's password."""
    import getpass

    if not args:
        print("Usage: ethan auth reset-password <username>")
        return 1
    username = args[0]

    password = getpass.getpass(f"New password for '{username}': ")
    if not password:
        print("Error: Password is required.")
        return 1
    is_valid, error = _validate_password(password)
    if not is_valid:
        print(f"Error: {error}")
        return 1
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("Error: Passwords do not match.")
        return 1

    password_hash = _hash_password(password)

    async def _reset():
        import asyncpg

        conn = await asyncio.wait_for(asyncpg.connect(_get_db_url()), timeout=5.0)
        try:
            result = await conn.execute(
                "UPDATE users SET password_hash = $1, updated_at = NOW() WHERE username = $2",
                password_hash,
                username,
            )
            if result == "UPDATE 0":
                print(f"Error: User '{username}' not found.")
                return 1
            print(f"✓ Password reset for '{username}'.")
            return 0
        finally:
            await conn.close()

    try:
        return asyncio.run(_reset())
    except Exception as exc:
        print(f"Error: Failed to reset password — {exc}")
        return 1


# ── Session via l'API Core (le seul flux d'authentification d'une interface) ──


def _save_session(token: str, user: dict) -> None:
    from interfaces.cli.config import config

    config.set("token", token)
    config.set("token_user", user.get("username", ""))
    config.set("token_role", user.get("role", ""))


def _clear_session() -> None:
    from interfaces.cli.config import config

    for key in ("token", "token_user", "token_role"):
        if key in config.config:
            config.set(key, "")


def _login(args):
    """Login against the Core API and store the JWT locally."""
    import getpass

    from interfaces.cli.core.client import APIError, request_json

    username = args[0] if args and not args[0].startswith("-") else ""
    if not username:
        try:
            username = input("Username: ").strip()
        except EOFError:
            print("Error: Username is required.")
            return 1
    if not username:
        print("Error: Username is required.")
        return 1
    try:
        password = getpass.getpass("Password: ")
    except EOFError:
        print("Error: Password is required.")
        return 1
    if not password:
        print("Error: Password is required.")
        return 1
    try:
        data = request_json("POST", "/auth/login", {"username": username, "password": password})
    except APIError as exc:
        print(f"Error: Login failed — {exc.detail}")
        return 1
    except ConnectionError as exc:
        print(f"Error: {exc}")
        return 1
    token = data.get("access_token") or data.get("token")
    if not token:
        print("Error: API returned no token.")
        return 1
    user = data.get("user", {"username": username})
    _save_session(token, user)
    print(
        f"✓ Logged in as {user.get('username', username)}"
        + (f" ({user.get('role')})" if user.get("role") else "")
    )
    return 0


def _logout(args):
    """Invalidate the local session (best-effort server-side, always local)."""
    from interfaces.cli.core.client import APIError, get_token, request_json

    token = get_token()
    if token:
        try:
            request_json("POST", "/auth/logout", token=token)
        except (APIError, ConnectionError):
            pass  # le nettoyage local reste garanti
    _clear_session()
    print("✓ Logged out")
    return 0


def _show_status(args):
    """Show the current session (GET /auth/me)."""
    from interfaces.cli.core.client import APIError, get_token, request_json

    token = get_token()
    if not token:
        print("Not logged in — run: ethan auth login")
        return 1
    try:
        me = request_json("GET", "/auth/me", token=token)
    except APIError as exc:
        if exc.status in (401, 403):
            print("Session expired or invalid — run: ethan auth login")
            return 1
        print(f"Error: {exc.detail}")
        return 1
    except ConnectionError as exc:
        print(f"Error: {exc}")
        return 1
    user = me.get("user", me)
    username = user.get("username", user.get("sub", "?"))
    role = user.get("role", "")
    print(f"✓ Logged in as {username}" + (f" ({role})" if role else ""))
    return 0


@register("auth", group="system", description="Login session and user administration")
def cmd_auth(args):
    if not args:
        print("usage: ethan auth [login|status|logout|create-admin|list|reset-password <user>]")
        return 1
    sub = args[0]
    if sub == "login":
        return _login(args[1:])
    elif sub == "status":
        return _show_status(args[1:])
    elif sub == "logout":
        return _logout(args[1:])
    elif sub == "create-admin":
        refused = _direct_db_guard(args[1:])
        if refused is not None:
            return refused
        return _create_admin([a for a in args[1:] if a != "--i-understand-direct-db"])
    elif sub == "list":
        refused = _direct_db_guard(args[1:])
        if refused is not None:
            return refused
        return _list_users([a for a in args[1:] if a != "--i-understand-direct-db"])
    elif sub == "reset-password":
        refused = _direct_db_guard(args[1:])
        if refused is not None:
            return refused
        return _reset_password([a for a in args[1:] if a != "--i-understand-direct-db"])
    else:
        suggestion = UX.suggest_command(sub, KNOWN_AUTH_SUBS)
        msg = (
            f"Did you mean? {suggestion}"
            if suggestion
            else "usage: ethan auth [login|status|logout|create-admin|list|reset-password]"
        )
        print(f"Unknown subcommand: {sub}\n  {msg}")
        return 1
