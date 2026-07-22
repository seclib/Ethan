"""Rate limiting middleware for ETHAN API Gateway.

Uses slowapi to limit API requests and prevent abuse.
Limits can be configured via environment variables.

Configuration (via env vars):
    - RATE_LIMIT_REQUESTS: Number of requests allowed per window (default: 100)
    - RATE_LIMIT_WINDOW: Window in seconds (default: 60)
    - RATE_LIMIT_ENABLED: Enable/disable rate limiting (default: true)
"""

from __future__ import annotations

import os
import logging
from typing import Optional

from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────

RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() in ("true", "1", "yes")
DEFAULT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
DEFAULT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

# Create limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{DEFAULT_REQUESTS} per {DEFAULT_WINDOW} seconds"] if RATE_LIMIT_ENABLED else [],
)

# Specific limits for sensitive endpoints
LOGIN_LIMITS = "5 per minute"  # Strict limit for authentication
MESSAGES_LIMITS = "30 per minute"  # For message posting
STATE_LIMITS = "60 per minute"  # For state queries


def get_limiter() -> Limiter:
    """Get the configured rate limiter instance."""
    return limiter


async def rate_limit_exceeded_handler(request, exc):
    """Custom handler for rate limit exceeded responses.

    Returns a JSON response with retry information.
    """
    from fastapi import Response
    import json

    retry_after = getattr(exc, "retry_after", 60) if hasattr(exc, "retry_after") else DEFAULT_WINDOW

    logger.warning(
        f"Rate limit exceeded for {get_remote_address(request)} on {request.url.path}"
    )

    return Response(
        content=json.dumps({
            "error": "Rate limit exceeded",
            "detail": "Too many requests. Please retry after the specified time.",
            "retry_after": retry_after,
        }),
        status_code=429,
        media_type="application/json",
        headers={"Retry-After": str(retry_after)},
    )