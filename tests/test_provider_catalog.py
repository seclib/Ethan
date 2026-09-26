"""tests/test_provider_catalog.py — catalogue Core des providers.

Ces tests n'exercent AUCUN service externe (pas de NATS, Redis, Postgres,
ni provider cloud) : le ProviderStore est en mémoire et les providers
réseau sont injoignables par construction (port fermé local).

Ils valident la source de vérité exposée aux interfaces :
- la liste des types supportés vient de la factory (aucune duplication) ;
- chaque type déclare ses méthodes d'authentification et ses capacités
  canoniques (jamais inventées par une interface) ;
- les URLs par défaut proviennent d'une table unique Core ;
- aucun secret n'est exposé.
"""

# ruff: noqa: E402 — `sys.path` est préparé après la docstring, avant les imports.
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.llm.provider_factory import (
    DEFAULT_BASE_URLS,
    SUPPORTED_PROVIDER_TYPES,
    create_provider_from_config,
    default_base_url,
)
from core.llm.provider_manager import ProviderManager
from core.llm.store import ProviderStore
from core.llm.types import ProviderCapability


def _new_manager() -> ProviderManager:
    """ProviderManager avec un store en mémoire (pas de Redis/Postgres)."""
    return ProviderManager(store=ProviderStore())


# ── Catalogue : source unique ─────────────────────────────────────────────


def test_catalog_lists_every_supported_type_once():
    """Le catalogue expose exactement les types de la factory Core."""
    catalog = _new_manager().get_catalog()
    ids = [entry["id"] for entry in catalog["types"]]
    assert ids == sorted(SUPPORTED_PROVIDER_TYPES)
    assert len(ids) == len(set(ids))  # aucun doublon


def test_catalog_default_base_urls_come_from_core_table():
    """Les URLs par défaut exposées sont celles de la table Core unique."""
    catalog = _new_manager().get_catalog()
    by_id = {entry["id"]: entry for entry in catalog["types"]}
    for provider_type, expected in DEFAULT_BASE_URLS.items():
        assert by_id[provider_type]["default_base_url"] == expected
    # Providers cloud : aucun endpoint par défaut imposé (l'utilisateur fournit
    # son endpoint/URL officiel) — chaîne vide, jamais une URL inventée.
    for cloud_type in ("openai", "anthropic", "gemini", "azure", "openrouter", "custom"):
        assert by_id[cloud_type]["default_base_url"] == ""


def test_catalog_auth_methods_and_capabilities_are_declared():
    """Chaque type déclare auth_methods + capacités canoniques non vides."""
    catalog = _new_manager().get_catalog()
    canonical = {cap.value for cap in ProviderCapability}
    for entry in catalog["types"]:
        assert entry["auth_methods"], f"{entry['id']} sans méthode d'authentification"
        assert set(entry["auth_methods"]) <= {"api_key", "user_account"}
        assert entry["capabilities"], f"{entry['id']} sans capacité"
        assert set(entry["capabilities"]) <= canonical
        # Le chat est la capacité universelle du modèle unifié.
        assert "llm" in entry["capabilities"]


def test_catalog_provider_capabilities_vocabulary_is_canonical():
    """Le vocabulaire exposé est celui de core/llm/types.py::ProviderCapability."""
    catalog = _new_manager().get_catalog()
    assert catalog["provider_capabilities"] == [
        "llm",
        "vision",
        "embedding",
        "speech_to_text",
        "transcription",
    ]


def test_catalog_never_exposes_secrets():
    """Le catalogue ne contient ni champ clé API ni valeur secrète.

    ``api_key`` est légitime comme *nom de méthode d'authentification*
    (liste ``auth_methods``) : on vérifie l'absence de champ ``api_key``
    (donc de valeur) et de toute valeur ressemblant à un secret.
    """
    payload = str(_new_manager().get_catalog()).lower()
    assert "'api_key':" not in payload  # aucun champ clé API (donc aucune valeur)
    for forbidden in ("secret", "token", "password", "sk-"):
        assert forbidden not in payload


def test_default_base_url_unknown_type_is_empty():
    """Un type inconnu n'hérite d'aucune URL — pas d'invention."""
    assert default_base_url("does-not-exist") == ""
    assert default_base_url("") == ""


def test_factory_uses_core_default_base_urls():
    """La factory applique la même table (pas de valeur dupliquée en dur)."""
    ollama = create_provider_from_config({"type": "ollama", "name": "o"})
    assert ollama._base_url == DEFAULT_BASE_URLS["ollama"]

    generic = create_provider_from_config({"type": "openai-compatible", "name": "g"})
    assert generic._base_url == DEFAULT_BASE_URLS["openai-compatible"]

    explicit = create_provider_from_config(
        {"type": "ollama", "name": "o2", "base_url": "http://10.0.0.5:11434"}
    )
    assert explicit._base_url == "http://10.0.0.5:11434"


def test_azure_api_version_readable_from_options():
    """Azure : api_version accepté au niveau racine ou dans options (API)."""
    from_options = create_provider_from_config(
        {"type": "azure", "name": "az", "options": {"api_version": "2024-02-01"}}
    )
    assert from_options._api_version == "2024-02-01"

    from_root = create_provider_from_config(
        {"type": "azure", "name": "az2", "api_version": "2024-06-01"}
    )
    assert from_root._api_version == "2024-06-01"

    default = create_provider_from_config({"type": "azure", "name": "az3"})
    assert default._api_version == "2023-05-15"


# ── Provider indisponible : comportement réel, jamais d'invention ─────────


def test_disabled_unknown_type_falls_back_to_llm_only():
    """Provider désactivé de type inconnu : capacités = [llm] (pas d'invention)."""

    async def run():
        manager = _new_manager()
        config = {"name": "mystery", "type": "does-not-exist", "enabled": False}
        await manager._store.save("mystery", dict(config))
        manager._providers_config["mystery"] = dict(config)

        described = await manager.describe_provider("mystery")
        assert described["capabilities"] == ["llm"]
        assert described["status"] == "unknown"
        assert described["models"] == []
        assert described["has_api_key"] is False

    asyncio.run(run())


def test_unreachable_provider_reports_error_without_raising():
    """Un provider activé mais injoignable renvoie un statut d'erreur explicite."""
    import socket

    # Port fermé de façon fiable : on ouvre puis ferme un socket local.
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    async def run():
        manager = _new_manager()
        config = {
            "name": "down-ollama",
            "type": "ollama",
            "enabled": True,
            "base_url": f"http://127.0.0.1:{port}",
            "default_model": "",
        }
        await manager._store.save("down-ollama", dict(config))
        manager._providers_config["down-ollama"] = dict(config)

        result = await manager.test_connection("down-ollama")
        assert result["connected"] is False
        assert result["status"] == "error"
        assert result["message"]  # cause racine transmise à l'interface

        described = await manager.describe_provider("down-ollama")
        assert described["status"] == "error"
        assert described["models"] == []
        # Les capacités déclarées par le type restent exposées (elles ne
        # dépendent pas de la joignabilité) — l'interface peut les afficher.
        assert "llm" in described["capabilities"]

    asyncio.run(run())


def test_test_connection_unknown_provider_raises_value_error():
    """Un provider inconnu lève une erreur claire (mappée 404 par l'API)."""

    async def run():
        manager = _new_manager()
        try:
            await manager.test_connection("ghost")
        except ValueError as exc:
            assert "ghost" in str(exc)
        else:  # pragma: no cover - échec explicite si aucune exception
            raise AssertionError("ValueError attendue pour un provider inconnu")

    asyncio.run(run())
