"""Router API — Knowledge (dédié, extrait de v1.py).

Toute la logique métier réside dans ``core.knowledge.Manager`` et
``core.knowledge.collections.KnowledgeCollectionManager``.
Ce router est une passerelle HTTP mince.

Routes (préfixe /v1) :
    GET     /v1/knowledge                              → liste des nodes
    GET     /v1/knowledge/search                       → recherche
    GET     /v1/knowledge/collections                  → collections utilisateur
    POST    /v1/knowledge/collections                  → créer collection
    GET     /v1/knowledge/collections/tree             → arborescence
    POST    /v1/knowledge/collections/retrieve-multi   → récupération multi-collections
    GET     /v1/knowledge/collections/{id}             → détail collection
"""

from __future__ import annotations

from typing import Any

from core.knowledge import KnowledgeCollectionManager, KnowledgeManager
from fastapi import APIRouter, HTTPException, Request

from interfaces.api.auth import current_user_id, resolve_user_scope

router = APIRouter(prefix="/v1", tags=["knowledge"])

# ── Dépendances (injection au démarrage via main.py) ──────────────────────

_knowledge_manager: KnowledgeManager | None = None
_knowledge_collections: KnowledgeCollectionManager | None = None


def set_knowledge_manager(manager: KnowledgeManager) -> None:
    global _knowledge_manager
    _knowledge_manager = manager


def get_knowledge_manager() -> KnowledgeManager:
    if _knowledge_manager is None:
        raise HTTPException(status_code=503, detail="Knowledge manager not initialized")
    return _knowledge_manager


def set_knowledge_collections(manager: KnowledgeCollectionManager) -> None:
    global _knowledge_collections
    _knowledge_collections = manager


def get_knowledge_collections() -> KnowledgeCollectionManager:
    if _knowledge_collections is None:
        raise HTTPException(
            status_code=503, detail="Knowledge collections not initialized"
        )
    return _knowledge_collections


# ── Routes ────────────────────────────────────────────────────────────────

@router.get("/knowledge")
async def list_knowledge():
    return [node.to_dict() for node in await get_knowledge_manager().list()]


@router.get("/knowledge/search")
async def search_knowledge(q: str = ""):
    return [node.to_dict() for node in await get_knowledge_manager().search(q)]


@router.get("/knowledge/collections")
async def list_collections(request: Request = None, user_id: str | None = None):
    """Collections de l'utilisateur courant (identité issue du JWT).

    ``user_id`` n'est qu'un repli pour les clients internes sans JWT : les
    collections sont isolées par utilisateur, un client ne peut pas lister
    celles d'un autre compte.
    """
    return await get_knowledge_collections().list_collections(
        user_id=resolve_user_scope(request, user_id)
    )


@router.post("/knowledge/collections")
async def create_collection(data: dict[str, Any], request: Request = None):
    try:
        return await get_knowledge_collections().create_collection(
            name=data.get("name", ""),
            description=data.get("description", ""),
            user_id=resolve_user_scope(request, data.get("user_id")),
            metadata=data.get("metadata"),
            parent_id=data.get("parent_id"),
            icon=data.get("icon"),
            order=data.get("order", 0),
            retrieval_strategy=data.get("retrieval_strategy"),
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/knowledge/collections/tree")
async def list_collections_tree(request: Request = None, user_id: str | None = None):
    """Liste les collections en arborescence (dossiers organisables).

    Identité issue du JWT (isolation par utilisateur) ; ``user_id`` ne sert
    que de repli pour les clients internes.
    """
    return await get_knowledge_collections().list_tree(
        user_id=resolve_user_scope(request, user_id)
    )


@router.post("/knowledge/collections/retrieve-multi")
async def retrieve_collections_multi(data: dict[str, Any]):
    """Retrieve RAG scopé sur plusieurs collections en un seul passage."""
    query = data.get("query", "")
    collection_ids = data.get("collection_ids", [])
    top_k = data.get("top_k")
    try:
        return await get_knowledge_collections().retrieve_multi(
            query, collection_ids, top_k=top_k
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/knowledge/collections/{collection_id}")
async def get_collection(collection_id: str):
    collection = await get_knowledge_collections().get_collection(collection_id)
    if collection is None:
        raise HTTPException(404, f"Collection {collection_id} not found")
    return collection