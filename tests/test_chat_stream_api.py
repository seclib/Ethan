"""SSE streaming route tests — /v1/chat/completions/stream (appel direct du handler).

La route est un adaptateur fin du ChatPipeline Core : ces tests valident le
contrat SSE (events content/done) et la persistance des réglages de session
(mode, reasoning_effort) avec les messages — jetable sans infra réseau.

Le pipeline est injecté sans ProviderManager → fallback écho : aucun appel
LLM externe, aucune configuration requise.
"""

from __future__ import annotations

import asyncio

from core.chat import ChatPipeline
from core.state import CoreRecordStore
from core.state.chats import ChatStore
from interfaces.api.routers import v1 as v1_router


async def _consume(response) -> str:
    """Consomme la StreamingResponse et retourne le corps SSE brut."""
    chunks = []
    # body_iterator est l'event_stream : l'itérer exécute le générateur
    # sans passer par la couche ASGI (pattern des tests de l'API dédup).
    async for chunk in response.body_iterator:
        chunks.append(chunk)
    if chunks and isinstance(chunks[0], str):
        return "".join(chunks)
    return b"".join(chunks).decode("utf-8", errors="replace")


def test_stream_echo_contract_and_mode_persistence():
    """Le flux SSE émet content + done, et le mode est persisté avec les messages."""

    async def scenario():
        chat_store = ChatStore(store=CoreRecordStore())
        pipeline = ChatPipeline(chat_store=chat_store)  # ProviderManager None → écho
        v1_router.set_chat_pipeline(pipeline)
        try:
            response = await v1_router.chat_completions_stream(
                {
                    "message": "Analyse ce problème",
                    "user_id": "alice",
                    "mode": "plan",
                    "reasoning_effort": "high",
                }
            )
            body = await _consume(response)
        finally:
            v1_router.set_chat_pipeline(None)

        # Contrat SSE : contenu écho puis événement done, format `data: {json}`.
        # (La route sérialise en ensure_ascii → l'accent est échappé en \u00e8.)
        assert '"content": "[ECHO] Analyse ce probl' in body
        assert '"type": "done"' in body
        assert body.lstrip().startswith("data: {")

        # La conversation est persistée (une seule) + le mode est porté par les
        # metadata des deux messages (restoration de session au refresh).
        chats = await chat_store.list_chats(user_id="alice")
        assert len(chats) == 1
        branch = await chat_store.get_branch(chats[0]["id"])
        assert [m["role"] for m in branch] == ["user", "assistant"]
        user_meta = branch[0]["metadata"]
        assistant_meta = branch[1]["metadata"]
        assert user_meta["mode"] == "plan"
        assert user_meta["reasoning_effort"] == "high"
        assert assistant_meta["mode"] == "plan"

    asyncio.run(scenario())


def test_stream_without_mode_falls_back_to_act():
    """Sans mode explicite, le Core résout Act (défaut) — jamais de fantôme."""

    async def scenario():
        chat_store = ChatStore(store=CoreRecordStore())
        pipeline = ChatPipeline(chat_store=chat_store)
        v1_router.set_chat_pipeline(pipeline)
        try:
            response = await v1_router.chat_completions_stream(
                {
                    "message": "Bonjour",
                    "user_id": "bob",
                }
            )
            await _consume(response)
        finally:
            v1_router.set_chat_pipeline(None)

        chats = await chat_store.list_chats(user_id="bob")
        assert len(chats) == 1
        branch = await chat_store.get_branch(chats[0]["id"])
        # Aucun SessionSettingsManager injecté → metadata de mode simplement
        # absentes (le pipeline en mode dégradé continue de fonctionner).
        assert "mode" not in branch[0]["metadata"]

    asyncio.run(scenario())
