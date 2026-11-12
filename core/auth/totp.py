"""Core-owned TOTP two-factor authentication (RFC 6238).

ETHAN Core owns the 2FA secret lifecycle: generation, verification and
enrollment state.  The API only exposes HTTP bindings; the WebUI only
renders the enrollment flow.

Implemented with the standard library only (no pyotp dependency):
HMAC-SHA1 over a base32 secret, 30-second step, 6-digit codes,
±1 step clock skew tolerance.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote

STEP_SECONDS = 30
CODE_DIGITS = 6
SKEW_STEPS = 1


def generate_secret() -> str:
    """Generate a random base32 secret (160 bits, no padding)."""
    raw = secrets.token_bytes(20)
    return base64.b32encode(raw).decode("ascii").rstrip("=")


def _decode_secret(secret: str) -> bytes:
    padded = secret.upper().rstrip("=")
    padded += "=" * ((8 - len(padded) % 8) % 8)
    return base64.b32decode(padded)


def _hotp(secret: str, counter: int) -> str:
    key = _decode_secret(secret)
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code = (
        ((digest[offset] & 0x7F) << 24)
        | (digest[offset + 1] << 16)
        | (digest[offset + 2] << 8)
        | digest[offset + 3]
    )
    return str(code % (10**CODE_DIGITS)).zfill(CODE_DIGITS)


def verify_code(secret: str, code: str, at_time: float | None = None) -> bool:
    """Verify a TOTP code with ±SKEW_STEPS clock skew tolerance."""
    if not code or not code.strip().isdigit():
        return False
    now = time.time() if at_time is None else at_time
    counter = int(now // STEP_SECONDS)
    expected = code.strip().zfill(CODE_DIGITS)
    for offset in range(-SKEW_STEPS, SKEW_STEPS + 1):
        if hmac.compare_digest(_hotp(secret, counter + offset), expected):
            return True
    return False


def provisioning_uri(secret: str, username: str, issuer: str = "ETHAN") -> str:
    """Build the otpauth:// URI for authenticator-app enrollment."""
    label = quote(f"{issuer}:{username}")
    params = (
        f"secret={secret}&issuer={quote(issuer)}"
        f"&algorithm=SHA1&digits={CODE_DIGITS}&period={STEP_SECONDS}"
    )
    return f"otpauth://totp/{label}?{params}"
