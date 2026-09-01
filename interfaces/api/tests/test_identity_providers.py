"""Tests réels Identity Providers — SCIM / LDAP / OAuth (routes /v1/scim/*, /v1/ldap/*, /v1/oauth/*).

Utilise les VRAIS managers du Core (SCIMManager, LDAPManager, OAuthManager,
core/auth/{scim,ldap,oauth}.py) sur un CoreRecordStore en mémoire : aucune
donnée factice, les routes sont appelées directement (pattern test_groups.py /
test_plugins.py / test_analytics.py) après injection via set_capability_managers.

Point central vérifié : la POLITIQUE SECRETS. Aucune réponse GET ne contient
le secret en clair — uniquement un booléen `<champ>_set`. Un POST avec champ
secret vide préserve la valeur stockée par le Core (write-only).
"""

import pytest

from core.auth.ldap import LDAPManager
from core.auth.oauth import OAuthManager
from core.auth.scim import SCIMManager
from core.state.record_store import CoreRecordStore
from routers.capabilities import (
    CapabilityManagers,
    configure_ldap,
    configure_scim,
    disable_oauth_provider,
    get_ldap_config,
    get_ldap_status,
    get_scim_config,
    get_scim_status,
    list_oauth_providers,
    register_oauth_provider,
    set_capability_managers,
)


@pytest.fixture()
def core_managers():
    """Managers Core réels sur store mémoire + injection dans le router."""
    store = CoreRecordStore()
    managers = CapabilityManagers(
        scim=SCIMManager(store=store),
        ldap=LDAPManager(store=store),
        oauth=OAuthManager(store=store),
    )
    set_capability_managers(managers)
    yield managers
    set_capability_managers(CapabilityManagers())


@pytest.fixture()
def uninitialized():
    """Aucun manager injecté — les routes doivent répondre 503."""
    set_capability_managers(CapabilityManagers())
    yield
    set_capability_managers(CapabilityManagers())


@pytest.mark.asyncio
async def test_scim_503_without_manager(uninitialized):
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await get_scim_config()
    assert exc.value.status_code == 503


@pytest.mark.asyncio
async def test_scim_config_secret_never_returned(core_managers):
    # Avant configuration : dict vide (pas de secret).
    assert await get_scim_config() == {}

    config = await configure_scim(
        {
            "enabled": True,
            "base_url": "https://idp.example.com/scim/v2",
            "bearer_token": "super-secret-token",
        }
    )
    # Le secret n'est JAMAIS dans la réponse — uniquement le booléen.
    assert "bearer_token" not in config
    assert config["bearer_token_set"] is True
    assert config["base_url"] == "https://idp.example.com/scim/v2"

    # Relecture GET : même politique.
    read_back = await get_scim_config()
    assert "bearer_token" not in read_back
    assert read_back["bearer_token_set"] is True

    # Le Core, lui, conserve bien la valeur (source de vérité).
    stored = await core_managers.scim.get_config()
    assert stored["bearer_token"] == "super-secret-token"

    # Statut reflète la configuration.
    assert await get_scim_status() == {"enabled": True}


@pytest.mark.asyncio
async def test_scim_empty_secret_preserves_existing(core_managers):
    await configure_scim({"enabled": False, "bearer_token": "first-secret"})
    # Réconfiguration SANS secret : le Core conserve l'ancien.
    config = await configure_scim({"enabled": True, "base_url": "https://x"})
    assert config["bearer_token_set"] is True
    stored = await core_managers.scim.get_config()
    assert stored["bearer_token"] == "first-secret"


@pytest.mark.asyncio
async def test_ldap_config_secret_never_returned(core_managers):
    assert await get_ldap_config() == {}

    config = await configure_ldap(
        {
            "server_url": "ldaps://ldap.example.com",
            "bind_dn": "cn=admin,dc=example,dc=com",
            "bind_password": "ldap-secret",
            "user_search_base": "ou=users,dc=example,dc=com",
            "tls_enabled": True,
        }
    )
    assert "bind_password" not in config
    assert config["bind_password_set"] is True
    assert config["server_url"] == "ldaps://ldap.example.com"

    read_back = await get_ldap_config()
    assert "bind_password" not in read_back
    assert read_back["bind_password_set"] is True

    stored = await core_managers.ldap.get_config()
    assert stored["bind_password"] == "ldap-secret"
    assert await get_ldap_status() == {"enabled": True}


@pytest.mark.asyncio
async def test_ldap_empty_secret_preserves_existing(core_managers):
    await configure_ldap(
        {"server_url": "ldap://a", "bind_dn": "cn=a", "bind_password": "keep-me"}
    )
    config = await configure_ldap({"server_url": "ldap://b", "bind_dn": "cn=b"})
    assert config["bind_password_set"] is True
    stored = await core_managers.ldap.get_config()
    assert stored["bind_password"] == "keep-me"


@pytest.mark.asyncio
async def test_oauth_register_hides_client_secret(core_managers):
    assert await list_oauth_providers() == []

    provider = await register_oauth_provider(
        {
            "name": "github",
            "client_id": "abc123",
            "client_secret": "oauth-secret",
            "authorize_url": "https://github.com/login/oauth/authorize",
            "token_url": "https://github.com/login/oauth/access_token",
            "userinfo_url": "https://api.github.com/user",
        }
    )
    assert "client_secret" not in provider
    assert provider["client_secret_set"] is True
    assert provider["client_id"] == "abc123"

    # Liste : aucun secret en clair.
    providers = await list_oauth_providers()
    assert len(providers) == 1
    assert "client_secret" not in providers[0]
    assert providers[0]["client_secret_set"] is True

    # Persistance réelle dans le Core.
    stored = await core_managers.oauth.get_provider("github")
    assert stored["client_secret"] == "oauth-secret"


@pytest.mark.asyncio
async def test_oauth_register_requires_name(core_managers):
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        await register_oauth_provider({"client_id": "x"})
    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_oauth_disable(core_managers):
    from fastapi import HTTPException

    await register_oauth_provider(
        {"name": "google", "client_id": "g", "client_secret": "s"}
    )
    disabled = await disable_oauth_provider("google")
    assert disabled["enabled"] is False
    assert "client_secret" not in disabled

    # 404 sur un provider inconnu.
    with pytest.raises(HTTPException) as exc:
        await disable_oauth_provider("unknown")
    assert exc.value.status_code == 404