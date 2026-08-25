"""Secrets loader with Vault/Docker fallback.

Fournit :
- ``get_secrets()`` : loader legacy (dataclass ``Secrets``) — utilisé par le code production.
- ``SecretManager`` : gestionnaire de secrets avec cache, convention ``ETHAN_<NAME>``,
  utilisé par les interfaces et les tests.

Aucun secret n'est jamais persisté en base ni exposé — uniquement une résolution
depuis l'environnement (env / Vault / Docker secrets).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


class SecretNotFoundError(Exception):
    """Levée lorsqu'un secret demandé n'existe pas."""


@dataclass
class Secrets:
    postgres_password: str
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None


# ─────────────────────────────────────────────────────────────────────────────
# Loader bas niveau (production) — récupère un "blob" de secrets connus
# ─────────────────────────────────────────────────────────────────────────────

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


# ─────────────────────────────────────────────────────────────────────────────
# SecretManager (gestionnaire avec cache)
#
# Conventions de résolution pour ``get("nom-secret")`` :
#   1. ``ETHAN_NOM_SECRET`` (nom converti en MAJUSCULES, ``-`` → ``_``, préfixe ``ETHAN_``)
#   2. ``NOM_SECRET``           (nom direct en MAJUSCULES, même conversion)
#   3. Vault (si ``VAULT_ADDR`` + ``VAULT_TOKEN`` fournis)
#   4. Valeur par défaut ou ``SecretNotFoundError``
# ─────────────────────────────────────────────────────────────────────────────

class SecretManager:
    """Gestionnaire de secrets avec cache mémoire.

    Exemples::

        mgr = SecretManager()

        value = mgr.get("openai-api-key")          # lit ``ETHAN_OPENAI_API_KEY``
        value = mgr.get("my-secret", default="x")  # ``ETHAN_MY_SECRET`` / ``MY_SECRET``
        value = mgr.get_or_none("clef-absente")    # None si absent
        mgr.clear_cache()
    """

    def __init__(self, cache: dict[str, str] | None = None) -> None:
        self._cache: dict[str, str] = dict(cache) if cache else {}

    # ── Résolution ──────────────────────────────────────────────────────────

    def get(self, name: str, default: str | None = None) -> str:
        """Résout un secret.

        Priorité :
        1. Cache mémoire ;
        2. Variable d'environnement ``ETHAN_<NAME>`` ;
        3. Variable d'environnement ``<NAME>`` (directe) ;
        4. Vault (si configuré) ;
        5. ``default`` si fournie, sinon ``SecretNotFoundError``.
        """
        value = self._resolve_lookup(name)
        if value is not None:
            self._cache[name] = value
            return value
        if default is not None:
            self._cache[name] = default
            return default
        raise SecretNotFoundError(f"Secret '{name}' introuvable dans env/Vault")

    def get_or_none(self, name: str) -> str | None:
        """Retourne ``None`` si le secret n'existe pas (jamais d'exception)."""
        value = self._resolve_lookup(name)
        if value is not None:
            self._cache[name] = value
        return value

    # ── Cache ───────────────────────────────────────────────────────────────

    def clear_cache(self) -> None:
        """Vide le cache mémoire."""
        self._cache.clear()

    @property
    def cache_size(self) -> int:
        return len(self._cache)

    # ── Helpers internes ─────────────────────────────────────────────────────

    def _resolve_lookup(self, name: str) -> str | None:
        """Cherche dans cache, puis env (``ETHAN_<NAME>`` puis ``<NAME>``), puis Vault."""
        if name in self._cache:
            return self._cache[name]

        env_key = self._to_env_key(name)
        direct_key = self._to_env_directive(name)

        # Env prioritaire (ETHAN_<NAME>)
        if env_key and os.getenv(env_key) is not None:
            return os.getenv(env_key)

        # Env directe (<NAME>)
        if os.getenv(direct_key) is not None:
            return os.getenv(direct_key)

        # Vault fallback
        vault_secrets = _load_from_vault()
        if vault_secrets:
            # Mapper les clés vault connues vers la demande
            mapping = {
                "postgres-password": vault_secrets.postgres_password,
                "openai-api-key": vault_secrets.openai_api_key,
                "anthropic-api-key": vault_secrets.anthropic_api_key,
            }
            value = mapping.get(name)
            if value:
                return value

        return None

    @staticmethod
    def _to_env_key(name: str) -> str:
        """``openai-api-key`` -> ``ETHAN_OPENAI_API_KEY``."""
        return "ETHAN_" + name.upper().replace("-", "_")

    @staticmethod
    def _to_env_directive(name: str) -> str:
        """``my-secret`` -> ``MY_SECRET``."""
        return name.upper().replace("-", "_")

    def __repr__(self) -> str:
        return f"SecretManager(cache_size={len(self._cache)})"