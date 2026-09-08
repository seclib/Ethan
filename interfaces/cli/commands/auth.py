"""ETHAN auth — user & admin management.

Usage:
    ethan auth create-admin          Create an interactive admin account
    ethan auth list                  List existing users
    ethan auth reset-password <user> Reset a user's password
"""
import os
import asyncio
import asyncpg
import bcrypt
from interfaces.cli.registry import register
from interfaces.cli.core.ux import UX

KNOWN_AUTH_SUBS = ["create-admin", "list", "reset-password"]


def _get_db_url() -> str:
    """Resolve DATABASE_URL for local CLI execution.

    Inside Docker the host is ``postgres``; for local CLI usage we need
    ``localhost``.  We honour an explicit ``$DATABASE_URL`` and only rewrite
    the default when the env var is unset.
    """
    url = os.getenv("DATABASE_URL")
    if url:
        return url.replace("@postgres:", "@localhost:")
    password = os.getenv("POSTGRES_PASSWORD", "change-me-in-prod")
    return f"postgresql://ethan:{password}@localhost:5432/ethan"


def _hash_password(password: str) -> str:
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


def cmd_create_admin(args):
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
        conn = await asyncio.wait_for(asyncpg.connect(_get_db_url()), timeout=5.0)
        try:
            existing = await conn.fetchrow(
                "SELECT id FROM users WHERE username = $1", username
            )
            if existing:
                print(f"Error: User '{username}' already exists.")
                return 1
            await conn.execute(
                "INSERT INTO users (username, password_hash, roles, is_active) VALUES ($1, $2, $3, $4)",
                username, password_hash, ["admin"], True,
            )
            print(f"\n✓ Admin user '{username}' created successfully.")
            print(f"  Role: admin")
            print(f"  Login at: http://localhost:3001")
            return 0
        finally:
            await conn.close()

    try:
        return asyncio.run(_create())
    except Exception as exc:
        print(f"Error: Failed to create admin — {exc}")
        return 1


def cmd_list_users(args):
    """List existing users."""
    async def _list():
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


def cmd_reset_password(args):
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
        conn = await asyncio.wait_for(asyncpg.connect(_get_db_url()), timeout=5.0)
        try:
            result = await conn.execute(
                "UPDATE users SET password_hash = $1, updated_at = NOW() WHERE username = $2",
                password_hash, username,
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


@register("auth")
def cmd_auth(args):
    if not args:
        print("usage: ethan auth [create-admin|list|reset-password <user>]")
        return 1
    sub = args[0]
    if sub == "create-admin":
        return cmd_create_admin(args[1:])
    elif sub == "list":
        return cmd_list_users(args[1:])
    elif sub == "reset-password":
        return cmd_reset_password(args[1:])
    else:
        suggestion = UX.suggest_command(sub, KNOWN_AUTH_SUBS)
        msg = f"Did you mean? {suggestion}" if suggestion else "usage: ethan auth [create-admin|list|reset-password <user>]"
        print(f"Unknown subcommand: {sub}\n  {msg}")
        return 1
