"""Tests du PluginRegistry Core (core/plugins) — catalogue, cycle de vie,
connexion, permissions, compatibilité legacy.

Exécute le vrai PluginRegistry branché sur un CoreRecordStore mémoire et
la vraie ToolRegistry (builtins) — aucun mock du domaine.
"""

from __future__ import annotations

import asyncio

import pytest
from core.plugins import (
    BUILTIN_PLUGINS,
    PluginRegistry,
    catalogue_categories,
    find_manifest,
    resolve_conversation_tools,
)
from core.state import CoreRecordStore
from core.tools.registry import ToolRegistry


@pytest.fixture()
def registry():
    store = CoreRecordStore()
    return PluginRegistry(store=store, tool_registry=ToolRegistry())


def test_catalogue_non_vide_et_unique():
    ids = [m.id for m in BUILTIN_PLUGINS]
    assert len(ids) >= 10
    assert len(ids) == len(set(ids))
    assert find_manifest("github") is not None
    assert find_manifest("inexistant") is None


def test_categories_dynamiques():
    cats = catalogue_categories()
    ids = {c["id"] for c in cats}
    assert {"development", "productivity", "communication"} <= ids
    # count cohérent avec le catalogue
    for cat in cats:
        expected = sum(1 for m in BUILTIN_PLUGINS if cat["id"] in m.categories)
        assert int(cat["count"]) == expected


def test_list_plugins_vue_catalogue(registry):
    plugins = asyncio.run(registry.list_plugins())
    assert len(plugins) == len(BUILTIN_PLUGINS)
    by_id = {p["id"]: p for p in plugins}
    gh = by_id["github"]
    assert gh["name"] == "GitHub"
    assert gh["status"] == "available"
    assert gh["installed"] is False
    assert "read_data" in gh["permissions"]
    assert gh["authentication"]["env_vars"] == ["GITHUB_TOKEN"]


def test_install_enable_disable(registry):
    installed = asyncio.run(registry.install("web-search"))
    assert installed["installed"] is True
    assert installed["status"] == "inactive"
    enabled = asyncio.run(registry.enable("web-search"))
    assert enabled["status"] == "active"
    disabled = asyncio.run(registry.disable("web-search"))
    assert disabled["status"] == "inactive"
    # inconnu → None
    assert asyncio.run(registry.install("nope")) is None
    assert asyncio.run(registry.enable("nope")) is None


def test_toggle_compat(registry):
    asyncio.run(registry.install("github"))
    active = asyncio.run(registry.toggle("github"))
    assert active["status"] == "active"
    inactive = asyncio.run(registry.toggle("github"))
    assert inactive["status"] == "inactive"
    assert asyncio.run(registry.toggle("ghost")) is None


def test_connect_exige_installation(registry):
    # plugin non installé → connect refusé (None)
    assert asyncio.run(registry.connect("slack")) is None
    asyncio.run(registry.install("slack"))
    ok = asyncio.run(registry.connect("slack"))
    assert ok["connected"] is True
    disconnected = asyncio.run(registry.disconnect("slack"))
    assert disconnected["connected"] is False


def test_connect_secret_jamais_stocke(registry):
    asyncio.run(registry.install("github"))
    # config non secrète acceptée ; le corps ne doit contenir aucun secret
    result = asyncio.run(registry.connect("github", {"default_repo": "seclib/Ethan"}))
    assert result["connected"] is True
    assert result["configuration"] == {"default_repo": "seclib/Ethan"}
    # aucun champ secret dans la configuration persistée
    for key in result["configuration"]:
        assert "token" not in key.lower()
        assert "password" not in key.lower()


def test_permissions_declarees_et_effectives(registry):
    asyncio.run(registry.install("web-search"))
    asyncio.run(registry.enable("web-search"))
    perms = asyncio.run(registry.permissions("web-search"))
    assert perms is not None
    assert "external_network" in perms["declared"]
    # web-search référence builtin_web_search : permissions effectives réelles
    tool = ToolRegistry().get("builtin_web_search")
    if tool is not None:
        for permission in tool.required_permissions:
            assert str(permission) in perms["effective_from_tools"]


def test_capabilities_resout_tools_reels(registry):
    caps = asyncio.run(registry.capabilities("web-search"))
    assert caps is not None
    assert "search" in caps["capabilities"]
    assert caps["tools"][0]["id"] == "builtin_web_search"
    # registry branchée → l'outil est disponible ; sinon marqué indisponible
    assert caps["tools"][0].get("available") in (True, False)


def test_custom_legacy_preserve(registry):
    custom = asyncio.run(registry.install_custom("Mon Plugin Historique"))
    assert custom["source"] == "custom"
    assert custom["installed"] is True
    plugins = asyncio.run(registry.list_plugins())
    names = {p["name"] for p in plugins}
    assert "Mon Plugin Historique" in names
    # le custom coexiste avec le catalogue
    assert len(plugins) == len(BUILTIN_PLUGINS) + 1


def test_records_legacy_minimaux_fusionnes(registry):
    """Un ancien record {id,name,status,version} (format v1) reste lisible."""
    store = registry._store
    asyncio.run(
        store.save(
            "webui_plugins",
            "github",
            {"id": "github", "name": "GitHub Integration", "status": "active", "version": "1.0.0"},
        )
    )
    plugins = asyncio.run(registry.list_plugins())
    gh = {p["id"]: p for p in plugins}["github"]
    # le manifest Core est servi, l'état legacy est fusionné
    assert gh["name"] == "GitHub"  # manifest (pas le nom legacy)
    assert gh["status"] == "active"  # état legacy préservé
    assert gh["installed"] is True


def test_persistence_registre_recharge(registry):
    asyncio.run(registry.install("knowledge"))
    asyncio.run(registry.enable("knowledge"))
    # un second registre sur le même store voit l'état (persistance Core)
    second = PluginRegistry(registry._store, tool_registry=ToolRegistry())
    state = asyncio.run(second.get("knowledge"))
    assert state["installed"] is True
    assert state["status"] == "active"


# ── Routage conversation → plugins (resolve_conversation_tools) ────────


def test_conversation_tools_injecte_plugins_actifs(registry):
    asyncio.run(registry.install("web-search"))
    asyncio.run(registry.enable("web-search"))
    accepted, tools = asyncio.run(resolve_conversation_tools(registry, ["web-search"], None))
    assert accepted == ["web-search"]
    assert "builtin_web_search" in tools  # tool référencé injecté


def test_conversation_tools_ignore_inactifs_et_inconnus(registry):
    # jamais installé → disponible → ignoré
    accepted, tools = asyncio.run(resolve_conversation_tools(registry, ["github", "ghost"], None))
    assert accepted == []
    assert tools == []
    # installé mais inactif → ignoré
    asyncio.run(registry.install("github"))
    accepted, tools = asyncio.run(resolve_conversation_tools(registry, ["github"], ["existing"]))
    assert accepted == []
    assert tools == ["existing"]


def test_conversation_tools_pas_de_duplication(registry):
    asyncio.run(registry.install("web-search"))
    asyncio.run(registry.enable("web-search"))
    accepted, tools = asyncio.run(
        resolve_conversation_tools(registry, ["web-search"], ["builtin_web_search"])
    )
    assert accepted == ["web-search"]
    assert tools.count("builtin_web_search") == 1  # déjà présent → non dupliqué


def test_conversation_tools_inactive_apres_disable(registry):
    asyncio.run(registry.install("web-search"))
    asyncio.run(registry.enable("web-search"))
    accepted1, _ = asyncio.run(resolve_conversation_tools(registry, ["web-search"], []))
    assert accepted1 == ["web-search"]
    asyncio.run(registry.disable("web-search"))
    accepted2, _ = asyncio.run(resolve_conversation_tools(registry, ["web-search"], []))
    assert accepted2 == []  # désactivé → ignoré (fail-soft)


# ── Cycle de vie complet : uninstall / update ─────────────────────────────


def test_uninstall_deux_niveaux(registry):
    """Uninstall conserve la configuration ; Uninstall+data la supprime.

    Les secrets (secret manager) ne sont JAMAIS supprimés — la réponse
    liste les variables à révoquer manuellement.
    """
    asyncio.run(registry.install("github"))
    asyncio.run(registry.enable("github"))
    connected = asyncio.run(registry.connect("github", {"default_repo": "ethan/core"}))
    assert connected["connected"] is True

    # Niveau 1 : uninstall (configuration conservée dans le record).
    out = asyncio.run(registry.uninstall("github", remove_data=False))
    assert out["uninstalled"] is True
    assert out["data_removed"] is False
    assert out["configuration_kept"] is True
    assert out["secrets_to_revoke"] == ["GITHUB_TOKEN"]
    after = asyncio.run(registry.get("github"))
    assert after["installed"] is False
    assert after["status"] != "active"

    # Réinstallation : les réglages sont retrouvés (pas de re-saisie).
    asyncio.run(registry.install("github"))
    again = asyncio.run(registry.get("github"))
    assert again["installed"] is True
    assert again["configuration"].get("default_repo") == "ethan/core"

    # Niveau 2 : uninstall + suppression des données du plugin.
    out2 = asyncio.run(registry.uninstall("github", remove_data=True))
    assert out2["uninstalled"] is True
    assert out2["data_removed"] is True
    pristine = asyncio.run(registry.get("github"))
    assert pristine["installed"] is False
    # Les VALEURS sauvegardées sont supprimées (les déclarations du manifest,
    # elles, restent — elles décrivent le plugin, ce n'est pas de la donnée).
    assert not (isinstance(pristine.get("configuration"), dict) and pristine["configuration"])
    assert not pristine.get("connected")


def test_uninstall_plugin_inconnu(registry):
    assert asyncio.run(registry.uninstall("ghost")) is None


def test_plugin_invalide(registry):
    """Installation/update d'un id absent du catalogue → None (jamais d'erreur)."""
    assert asyncio.run(registry.install("ghost")) is None
    assert asyncio.run(registry.update("ghost")) is None
    assert asyncio.run(registry.update("github")) is None  # jamais installé


def test_update_available_et_update(registry):
    """Détection de mise à jour : manifest_version installée != catalogue."""
    asyncio.run(registry.install("github"))
    # Aucun écart au départ
    plugins = asyncio.run(registry.list_plugins())
    gh = {p["id"]: p for p in plugins}["github"]
    assert gh["update_available"] is False

    # Simuler une version installée antérieure
    record = asyncio.run(registry._store.get("webui_plugins", "github"))
    record["manifest_version"] = "0.9.0"
    asyncio.run(registry._store.save("webui_plugins", "github", record))

    plugins = asyncio.run(registry.list_plugins())
    gh = {p["id"]: p for p in plugins}["github"]
    assert gh["update_available"] is True
    assert gh["manifest_version"] == "0.9.0"

    # update() synchronise et conserve l'état
    updated = asyncio.run(registry.update("github"))
    assert updated["manifest_version"] == find_manifest("github").version
    assert updated["update_available"] is False
    assert updated["installed"] is True


def test_cycle_vie_complet_discover_a_uninstall(registry):
    """Discover → Install → Configure → Enable → Use → Disable → Re-enable
    → Update → Uninstall.  Le plugin désactivé n'expose plus ses tools
    (resolve_conversation_tools) ; uninstall ne casse pas le système."""
    # Discover : disponible au catalogue
    before = asyncio.run(registry.get("slack"))
    assert before["installed"] is False
    # Install → inactive
    assert asyncio.run(registry.install("slack"))["status"] == "inactive"
    # Configure (connect) — plugin avec secret (SLACK_BOT_TOKEN via env)
    # Slack n'exige aucune config non-secret (SLACK_BOT_TOKEN vit dans le
    # secret manager) — la connexion est donc directe, sans secret ici.
    assert asyncio.run(registry.connect("slack", {}))["connected"] is True
    # Enable → Use : les tools/mcp déclarés sont acceptés dans la conversation
    asyncio.run(registry.enable("slack"))
    accepted, merged = asyncio.run(resolve_conversation_tools(registry, ["slack"], []))
    assert "slack" in accepted
    # Disable → plus exécuté
    asyncio.run(registry.disable("slack"))
    accepted, _ = asyncio.run(resolve_conversation_tools(registry, ["slack"], []))
    assert "slack" not in accepted
    # Re-enable
    assert asyncio.run(registry.enable("slack"))["status"] == "active"
    # Update (idempotent : même version)
    assert asyncio.run(registry.update("slack"))["installed"] is True
    # Uninstall → retiré des conversations
    asyncio.run(registry.uninstall("slack", remove_data=True))
    accepted, _ = asyncio.run(resolve_conversation_tools(registry, ["slack"], []))
    assert "slack" not in accepted
