"""Secrets loader with Vault/Docker fallback."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Secrets:
    postgres_password: str
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None


def _load_from_vault() -> Secrets | None:
    addr = os.getenv("VAULT_ADDR")
    token = os.getenv("VAULT_TOKEN")
    if not addr or not token:
        return None
    try:
        import requests
    except ImportError:
        return None

    import time
    
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            secrets: dict[str, str] = {}
            for path in ("secret/ethan/postgres", "secret/ethan/openai", "secret/ethan/anthropic"):
                resp = requests.get(
                    f"{addr}/v1/{path}",
                    headers={"X-Vault-Token": token},
                    timeout=2,
                )
                if resp.ok:
                    data = resp.json().get("data", {})
                    secrets.update(data)
            if secrets:
                return Secrets(
                    postgres_password=secrets.get("postgres_password", ""),
                    openai_api_key=secrets.get("openai_api_key"),
                    anthropic_api_key=secrets.get("anthropic_api_key"),
                )
            break  # Reached Vault but no secrets found, fallback to env
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                return None
    return None


def _load_from_env() -> Secrets:
    return Secrets(
        postgres_password=os.getenv("POSTGRES_PASSWORD", ""),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    )


def get_secrets() -> Secrets:
    vault_secrets = _load_from_vault()
    if vault_secrets:
        return vault_secrets
    return _load_from_env()