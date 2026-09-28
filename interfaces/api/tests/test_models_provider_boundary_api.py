"""Tests API — frontière Provider / Modèle sur le routeur /models.

Ces tests verrouillent la distinction exigée par ETHAN :
- un PROVIDER est un service (connexion, endpoint, auth) ;
- un MODÈLE est une entrée exposée par un provider (ou une fiche custom Core).

Régressions couvertes :
- une fiche custom plaçait un identifiant de MODÈLE (``base_model_id``) dans
  le champ ``provider`` → filtre par provider, routage et regroupement du
  sélecteur de chat cassés silencieusement ;
- la joignabilité d'une fiche custom est invérifiable par le Core : elle ne
  doit pas être déduite de l'activation administrative ;
- les écritures (PUT/DELETE/toggle) doivent exiger la même permission que la
  création, sur le même objet.
"""

# Ruff : les imports suivent l'insertion de ROOT dans sys.path.
# ruff: noqa: E402

from __future__ import annotations

import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
import pytest_asyncio
from core.auth import Permission
from core.llm.model_store import ModelStore
from core.llm.provider_manager import ProviderManager
from core.llm.store import ProviderStore
from core.state.record_store import CoreRecordStore
from interfaces.api.routers import models as models_router


@pytest_asyncio.fixture()
async def store():
    """ModelStore sur un RecordStore en mémoire (persistance réelle)."""
    st = ModelStore(store=CoreRecordStore())
    models_router.set_model_store(st)
    models_router.set_provider_manager(ProviderManager(store=ProviderStore()))
    yield st
    models_router.set_model_store(None)  # type: ignore[arg-type]
    models_router.set_provider_manager(None)  # type: ignore[arg-type]


# ── Frontière Provider / Modèle ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_custom_card_exposes_real_provider_not_base_model(store: ModelStore):
    """`provider` est le SERVICE qui sert le modèle, pas le modèle de base."""
    card = await store.create_model(
        {
            "name": "Mon preset",
            "provider": "ollama",
            "model": "llama3.2-custom",
            "base_model_id": "llama3.2",
        }
    )
    payload = models_router._custom_model_payload(card)

    assert payload["provider"] == "ollama"
    assert payload["base_model_id"] == "llama3.2"
    # Le nom du modèle ne doit JAMAIS apparaître comme un service.
    assert payload["provider"] != payload["base_model_id"]


@pytest.mark.asyncio
async def test_custom_card_provider_persisted_and_updatable(store: ModelStore):
    """Le provider survit à la lecture, à l'édition et à la recherche."""
    card = await store.create_model({"name": "P", "provider": "vllm", "model": "m"})
    assert (await store.get_model(card["id"]))["provider"] == "vllm"

    await store.update_model(card["id"], {"provider": "lmstudio"})
    assert (await store.get_model(card["id"]))["provider"] == "lmstudio"

    # Une recherche par provider retrouve la fiche.
    assert [m["id"] for m in await store.search_models("lmstudio")] == [card["id"]]


@pytest.mark.asyncio
async def test_custom_card_without_provider_is_honest(store: ModelStore):
    """Fiche sans provider : chaîne vide, jamais un modèle présenté en service."""
    card = await store.create_model({"name": "Legacy", "base_model_id": "llama3.2"})
    payload = models_router._custom_model_payload(card)
    assert payload["provider"] == ""
    assert payload["base_model_id"] == "llama3.2"


# ── Joignabilité vs activation ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_custom_card_exposes_activation_separately(store: ModelStore):
    """`is_active` (administratif) est distinct de `is_available` (joignable)."""
    card = await store.create_model({"name": "P", "provider": "ollama", "is_active": False})
    payload = models_router._custom_model_payload(card)

    # Le Core ne peut PAS tester la joignabilité d'une fiche : il reflète
    # l'activation et l'expose explicitement pour que l'interface sache
    # quelle notion elle affiche.
    assert payload["is_active"] is False
    assert payload["is_available"] is False

    toggled = await store.toggle_model(card["id"])
    assert toggled["is_active"] is True
    assert models_router._custom_model_payload(toggled)["is_active"] is True


def test_discovered_payload_has_no_local_activation():
    """Un modèle découvert n'a pas d'activation locale (son état suit le provider)."""
    from core.llm.types import ModelInfo

    payload = models_router._discovered_model_payload(
        ModelInfo(id="qwen2.5", provider="ollama", name="Qwen")
    )
    # `null` et non `true` : l'interface ne doit pas croire à une activation
    # locale qui n'existe pas.
    assert payload["is_active"] is None
    assert payload["is_available"] is True
    assert payload["is_custom"] is False


# ── Permissions ───────────────────────────────────────────────────────────


def _required_permissions(func) -> set:
    """Permissions exigées par la route dont ``func`` est l'endpoint.

    FastAPI n'expose pas la route depuis la fonction : on la retrouve dans
    ``router.routes`` (identité d'endpoint), puis on lit le contrat
    d'introspection publié par ``require_permission`` (``checker.permissions``).
    """
    for route in models_router.router.routes:
        if getattr(route, "endpoint", None) is func:
            return {
                permission
                for dep in route.dependencies
                for permission in getattr(getattr(dep, "dependency", None), "permissions", ())
                or ()
            }
    return set()


@pytest.mark.parametrize(
    "name", ["create_model", "update_model", "delete_model", "toggle_model"]
)
def test_write_routes_require_permission(name: str):
    """Toute écriture sur /models exige la même permission que la création."""
    assert Permission.PLUGINS in _required_permissions(
        getattr(models_router, name)
    ), (
        f"{name} écrit une fiche modèle sans exiger Permission.PLUGINS : "
        "asymétrie d'autorisation sur le même objet que POST /models."
    )


@pytest.mark.parametrize("name", ["list_models", "search_models", "get_model"])
def test_read_routes_do_not_require_write_permission(name: str):
    """La lecture reste ouverte (le catalogue est consultable par tous)."""
    assert Permission.PLUGINS not in _required_permissions(getattr(models_router, name))


# ── Agrégation / filtres ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_models_filters_by_provider(store: ModelStore):
    """Le filtre provider_id ne renvoie pas les fiches d'un autre service."""
    await store.create_model(
        {"name": "Preset Ollama", "provider": "ollama", "model": "m", "base_model_id": "b"}
    )

    # Provider inconnu côté Core : aucun modèle découvert.
    assert await models_router.list_models(provider_id="inexistant") == []

    # Provider sans modèle découvert : la fiche de CE provider est incluse.
    found = await models_router.list_models(provider_id="ollama", include_custom=True)
    assert [f["provider"] for f in found] == ["ollama"]

    # include_custom=false : aucune fiche custom dans le résultat.
    assert await models_router.list_models(provider_id="ollama", include_custom=False) == []


@pytest.mark.asyncio
async def test_list_models_never_invents_entries(store: ModelStore):
    """Sans provider actif, le catalogue est vide — jamais de fiche fictive."""
    assert await models_router.list_models() == []


@pytest.mark.asyncio
async def test_search_includes_custom_by_provider_name(store: ModelStore):
    """La recherche Core couvre le provider des fiches custom."""
    await store.create_model({"name": "Preset", "provider": "ollama", "model": "m"})
    found = await models_router.search_models("ollama")
    assert [f["provider"] for f in found] == ["ollama"]


@pytest.mark.asyncio
async def test_get_model_404_for_unknown_id(store: ModelStore):
    """Un id inconnu remonte un 404 explicite (jamais une fiche vide)."""
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as excinfo:
        await models_router.get_model("inexistant")
    assert excinfo.value.status_code == 404


# ── Garde-fous ────────────────────────────────────────────────────────────


def test_custom_payload_never_exposes_raw_card_secrets() -> None:
    """La sérialisation ne laisse passer aucun champ parasite de la fiche."""
    payload = models_router._custom_model_payload(
        {
            "id": "c-1",
            "name": "P",
            "provider": "ollama",
            "model": "m",
            "base_model_id": "b",
            "params": {},
            "meta": {},
            "acl": [],
            "api_key": "sk-secret",  # champ parasite : ne doit jamais fuiter
        }
    )
    assert "api_key" not in payload
    assert "sk-secret" not in str(payload)


def test_list_models_signature_exposes_provider_filter() -> None:
    """Le filtre provider_id existe réellement dans la signature de la route."""
    assert "provider_id" in inspect.signature(models_router.list_models).parameters
