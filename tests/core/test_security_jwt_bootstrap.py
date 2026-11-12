"""Unit tests for JWT secret bootstrap and local token generator."""

from __future__ import annotations

import json
import base64
import os
from pathlib import Path

import pytest

from core.security.jwt_bootstrap import (
    create_local_token,
    get_or_create_jwt_secret,
    INSECURE_PLACEHOLDER,
)


def test_create_local_token_structure() -> None:
    token = create_local_token(user_id="user_test", username="testuser", role="admin")
    parts = token.split(".")
    assert len(parts) == 3

    # Decode header
    header_json = base64.urlsafe_b64decode(parts[0] + "==").decode("utf-8")
    header = json.loads(header_json)
    assert header["alg"] == "HS256"
    assert header["typ"] == "JWT"

    # Decode payload
    payload_json = base64.urlsafe_b64decode(parts[1] + "==").decode("utf-8")
    payload = json.loads(payload_json)
    assert payload["sub"] == "user_test"
    assert payload["username"] == "testuser"
    assert payload["role"] == "admin"
    assert "exp" in payload
    assert "iat" in payload


def test_get_or_create_jwt_secret_uses_env(monkeypatch: pytest.MonkeyPatch) -> None:
    custom_secret = "super_custom_secret_key_123456789"
    monkeypatch.setenv("JWT_SECRET", custom_secret)

    resolved = get_or_create_jwt_secret()
    assert resolved == custom_secret


def test_token_with_custom_secret() -> None:
    secret = "test_custom_secret_987654321"
    token = create_local_token(user_id="alice", secret=secret)
    assert token.startswith("eyJ")

