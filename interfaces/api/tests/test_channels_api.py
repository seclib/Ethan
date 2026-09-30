"""Tests réels Channels — POST /v1/channels/{id}/messages (mapping rôle/contenu).

Contexte : le gateway HTTP passait le contenu du message en position ``role``
et un ``metadata`` non supporté par ``ChannelStore.add_message`` — tout appel
réel échouait donc en TypeError (500) côté API, alors que l'endpoint était
annoncé. Ces tests verrouillent la correspondance exacte gateway ↔ Core, avec
le VRAI ChannelStore (core/state/channels.py) sur un CoreRecordStore en
mémoire (pattern test_analytics.py), sans mock de la logique métier.

Le Core reste l'unique propriétaire des canaux et des messages : le gateway ne
fait que mapper le JSON HTTP sur la signature du ChannelStore.
"""

from __future__ import annotations

import pytest
from core.state.channels import ChannelStore
from core.state.record_store import CoreRecordStore
from fastapi import HTTPException
from routers.capabilities import (
    CapabilityManagers,
    add_channel_message,
    create_channel,
    get_channel,
    list_channel_messages,
    list_channels,
    set_capability_managers,
)


@pytest.fixture()
def channels():
    """ChannelStore réel sur store mémoire + injection dans le router."""
    store = CoreRecordStore()
    managers = CapabilityManagers(channels=ChannelStore(store=store))
    set_capability_managers(managers)
    return managers


@pytest.mark.asyncio
async def test_created_channel_is_readable(channels):
    channel = await create_channel(
        {"name": "équipe-core", "description": "canal de test"}, request=None
    )

    listed = await list_channels()
    assert [c["id"] for c in listed] == [channel["id"]]
    assert (await get_channel(channel["id"]))["name"] == "équipe-core"


@pytest.mark.asyncio
async def test_message_content_is_stored_in_content_not_role(channels):
    """Le champ ``content`` HTTP arrive bien dans ``content`` (et non ``role``)."""
    channel = await create_channel({"name": "fil"}, request=None)

    message = await add_channel_message(
        channel["id"],
        {"content": "bonjour ETHAN", "role": "assistant"},
        request=None,
    )

    assert message["content"] == "bonjour ETHAN"
    assert message["role"] == "assistant"
    assert message["channel_id"] == channel["id"]


@pytest.mark.asyncio
async def test_message_defaults_to_user_role(channels):
    channel = await create_channel({"name": "sans-role"}, request=None)

    message = await add_channel_message(channel["id"], {"content": "salut"}, request=None)

    assert message["role"] == "user"
    assert message["content"] == "salut"


@pytest.mark.asyncio
async def test_messages_are_scoped_to_their_channel(channels):
    first = await create_channel({"name": "un"}, request=None)
    second = await create_channel({"name": "deux"}, request=None)

    await add_channel_message(first["id"], {"content": "message-1", "role": "user"}, request=None)
    await add_channel_message(second["id"], {"content": "message-2", "role": "agent"}, request=None)

    first_messages = await list_channel_messages(first["id"])
    assert [m["content"] for m in first_messages] == ["message-1"]


@pytest.mark.asyncio
async def test_unknown_channel_returns_404(channels):
    with pytest.raises(HTTPException) as exc_info:
        await add_channel_message("inconnu", {"content": "x"}, request=None)

    assert exc_info.value.status_code == 404
