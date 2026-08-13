"""Tests for the new Core domain stores and managers.

These tests verify that the Open-WebUI backend functions have been
correctly migrated into ETHAN Core, following the principle that
ETHAN Core is the single source of truth.
"""

import pytest

from core.state.chats import ChatStore
from core.state.files import FileStore
from core.state.channels import ChannelStore
from core.state.notes import NoteStore
from core.auth.users import UserManager
from core.auth.groups import GroupManager
from core.auth.oauth import OAuthManager
from core.auth.ldap import LDAPManager
from core.auth.api_keys import APIKeyManager
from core.auth.scim import SCIMManager
from core.scheduler.automations import AutomationManager
from core.scheduler.calendar import CalendarManager
from core.tools.servers import ToolServerManager
from core.tools.functions import FunctionManager
from core.llm.tts import TTSEngine
from core.llm.images import ImageGenerator
from core.learning.evaluations import EvaluationManager
from core.metrics.analytics import AnalyticsManager


@pytest.fixture
def chat_store():
    return ChatStore()


@pytest.fixture
def file_store():
    return FileStore()


@pytest.fixture
def user_manager():
    return UserManager()


@pytest.fixture
def group_manager():
    return GroupManager()


@pytest.fixture
def channel_store():
    return ChannelStore()


@pytest.fixture
def note_store():
    return NoteStore()


@pytest.fixture
def automation_manager():
    return AutomationManager()


@pytest.fixture
def calendar_manager():
    return CalendarManager()


@pytest.fixture
def tool_server_manager():
    return ToolServerManager()


@pytest.fixture
def function_manager():
    return FunctionManager()


@pytest.fixture
def tts_engine():
    return TTSEngine()


@pytest.fixture
def image_generator():
    return ImageGenerator()


@pytest.fixture
def evaluation_manager():
    return EvaluationManager()


@pytest.fixture
def analytics_manager():
    return AnalyticsManager()


@pytest.fixture
def oauth_manager():
    return OAuthManager()


@pytest.fixture
def ldap_manager():
    return LDAPManager()


@pytest.fixture
def api_key_manager():
    return APIKeyManager()


@pytest.fixture
def scim_manager():
    return SCIMManager()


# ── ChatStore ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_chat_store_create_and_get(chat_store):
    chat = await chat_store.create_chat("Test Chat", user_id="user-1")
    assert chat["title"] == "Test Chat"
    assert chat["user_id"] == "user-1"
    assert chat["archived"] is False
    assert chat["pinned"] is False
    assert chat["share_id"] is None

    fetched = await chat_store.get_chat(chat["id"])
    assert fetched["title"] == "Test Chat"


@pytest.mark.asyncio
async def test_chat_store_list_and_filter(chat_store):
    await chat_store.create_chat("Chat A", user_id="user-1")
    await chat_store.create_chat("Chat B", user_id="user-2")
    await chat_store.create_chat("Chat C", user_id="user-1")

    all_chats = await chat_store.list_chats()
    assert len(all_chats) == 3

    user1_chats = await chat_store.list_chats(user_id="user-1")
    assert len(user1_chats) == 2


@pytest.mark.asyncio
async def test_chat_store_add_and_list_messages(chat_store):
    chat = await chat_store.create_chat("Test Chat")
    msg = await chat_store.add_message(chat["id"], "user", "Hello")
    assert msg["role"] == "user"
    assert msg["content"] == "Hello"

    messages = await chat_store.list_messages(chat["id"])
    assert len(messages) == 1


@pytest.mark.asyncio
async def test_chat_store_update_and_delete(chat_store):
    chat = await chat_store.create_chat("Test Chat")
    updated = await chat_store.update_chat(chat["id"], {"title": "Updated", "pinned": True})
    assert updated["title"] == "Updated"
    assert updated["pinned"] is True

    assert await chat_store.delete_chat(chat["id"]) is True
    assert await chat_store.get_chat(chat["id"]) is None


@pytest.mark.asyncio
async def test_chat_store_share(chat_store):
    chat = await chat_store.create_chat("Test Chat")
    shared = await chat_store.share_chat(chat["id"])
    assert shared["share_id"] is not None


# ── FileStore ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_file_store_register_and_get(file_store):
    file = await file_store.register("test.txt", "text/plain", 1024, user_id="user-1")
    assert file["filename"] == "test.txt"
    assert file["size"] == 1024

    fetched = await file_store.get(file["id"])
    assert fetched["filename"] == "test.txt"


@pytest.mark.asyncio
async def test_file_store_list_and_delete(file_store):
    await file_store.register("a.txt", "text/plain", 100, user_id="user-1")
    await file_store.register("b.txt", "text/plain", 200, user_id="user-2")

    all_files = await file_store.list()
    assert len(all_files) == 2

    user1_files = await file_store.list(user_id="user-1")
    assert len(user1_files) == 1


# ── UserManager ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_user_manager_create_and_get(user_manager):
    user = await user_manager.create("alice", "alice@example.com", role="admin")
    assert user["username"] == "alice"
    assert user["email"] == "alice@example.com"
    assert user["role"] == "admin"
    assert user["active"] is True

    fetched = await user_manager.get(user["id"])
    assert fetched["username"] == "alice"


@pytest.mark.asyncio
async def test_user_manager_find_by_email(user_manager):
    await user_manager.create("bob", "bob@example.com")
    found = await user_manager.find_by_email("bob@example.com")
    assert found is not None
    assert found["username"] == "bob"


@pytest.mark.asyncio
async def test_user_manager_update_and_delete(user_manager):
    user = await user_manager.create("carol", "carol@example.com")
    updated = await user_manager.update(user["id"], {"role": "admin", "active": False})
    assert updated["role"] == "admin"
    assert updated["active"] is False

    assert await user_manager.delete(user["id"]) is True
    assert await user_manager.get(user["id"]) is None


# ── GroupManager ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_group_manager_create_and_members(group_manager):
    group = await group_manager.create("admins", "Admin group")
    assert group["name"] == "admins"
    assert group["members"] == []

    await group_manager.add_member(group["id"], "user-1")
    members = await group_manager.list_members(group["id"])
    assert "user-1" in members

    await group_manager.remove_member(group["id"], "user-1")
    members = await group_manager.list_members(group["id"])
    assert "user-1" not in members


# ── ChannelStore ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_channel_store_create_and_messages(channel_store):
    channel = await channel_store.create_channel("general", user_id="user-1")
    assert channel["name"] == "general"
    assert "user-1" in channel["members"]

    msg = await channel_store.add_message(channel["id"], "user", "Hello channel")
    assert msg["role"] == "user"
    assert msg["content"] == "Hello channel"

    messages = await channel_store.list_messages(channel["id"])
    assert len(messages) == 1


# ── NoteStore ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_note_store_create_and_search(note_store):
    note = await note_store.create("My Note", "This is a test note", user_id="user-1", pinned=True)
    assert note["title"] == "My Note"
    assert note["pinned"] is True

    results = await note_store.search("test")
    assert len(results) == 1
    assert results[0]["title"] == "My Note"


# ── AutomationManager ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_automation_manager_create_and_trigger(automation_manager):
    rule = await automation_manager.create(
        "Daily Report",
        trigger={"type": "schedule", "cron": "0 9 * * *"},
        actions=[{"type": "email", "to": "admin@example.com"}],
    )
    assert rule["name"] == "Daily Report"
    assert rule["enabled"] is True

    triggered = await automation_manager.trigger(rule["id"])
    assert triggered["trigger_count"] == 1


# ── CalendarManager ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_calendar_manager_create_and_list(calendar_manager):
    event = await calendar_manager.create("Team Meeting", "2026-08-12T09:00:00Z")
    assert event["title"] == "Team Meeting"

    events = await calendar_manager.list()
    assert len(events) == 1


# ── ToolServerManager ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_tool_server_manager_register_and_list(tool_server_manager):
    server = await tool_server_manager.register("MCP Server", "http://localhost:8080")
    assert server["name"] == "MCP Server"
    assert server["status"] == "disconnected"

    servers = await tool_server_manager.list()
    assert len(servers) == 1


# ── FunctionManager ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_function_manager_create_and_pipeline(function_manager):
    func = await function_manager.create_function(
        "greet", "Say hello", {"name": {"type": "string"}}
    )
    assert func["name"] == "greet"

    pipeline = await function_manager.create_pipeline(
        "Greeting Pipeline", [{"function": "greet", "args": {"name": "World"}}]
    )
    assert pipeline["name"] == "Greeting Pipeline"
    assert len(pipeline["steps"]) == 1


# ── TTSEngine ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_tts_engine_configure_and_get(tts_engine):
    config = await tts_engine.configure("openai", voice="alloy")
    assert config["provider"] == "openai"
    assert config["voice"] == "alloy"

    fetched = await tts_engine.get_config()
    assert fetched["provider"] == "openai"


# ── ImageGenerator ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_image_generator_configure_and_get(image_generator):
    config = await image_generator.configure("openai", model="dall-e-3")
    assert config["provider"] == "openai"
    assert config["model"] == "dall-e-3"

    fetched = await image_generator.get_config()
    assert fetched["model"] == "dall-e-3"


# ── EvaluationManager ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_evaluation_manager_create_and_add_result(evaluation_manager):
    eval_def = await evaluation_manager.create(
        "Accuracy Test", [{"metric": "accuracy", "threshold": 0.9}]
    )
    assert eval_def["name"] == "Accuracy Test"

    updated = await evaluation_manager.add_result(eval_def["id"], {"score": 0.95})
    assert len(updated["results"]) == 1


# ── AnalyticsManager ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_analytics_manager_record_and_summary(analytics_manager):
    await analytics_manager.record_event(
        "llm_call", user_id="user-1", provider="openai", model="gpt-4",
        tokens_in=100, tokens_out=50, cost=0.005,
    )
    summary = await analytics_manager.get_usage_summary(user_id="user-1")
    assert summary["total_tokens"] == 150
    assert summary["total_cost"] == 0.005


# ── OAuthManager ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_oauth_manager_register_and_list(oauth_manager):
    provider = await oauth_manager.register_provider(
        "google", "client-id", "secret",
        "https://accounts.google.com/o/oauth2/auth",
        "https://oauth2.googleapis.com/token",
        "https://openidconnect.googleapis.com/v1/userinfo",
    )
    assert provider["name"] == "google"
    assert provider["enabled"] is True

    providers = await oauth_manager.list_providers()
    assert len(providers) == 1


# ── LDAPManager ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ldap_manager_configure_and_get(ldap_manager):
    config = await ldap_manager.configure(
        "ldap://ldap.example.com", "cn=admin,dc=example,dc=com", "secret", "ou=users,dc=example,dc=com"
    )
    assert config["server_url"] == "ldap://ldap.example.com"
    assert config["enabled"] is True

    fetched = await ldap_manager.get_config()
    assert fetched["server_url"] == "ldap://ldap.example.com"


# ── APIKeyManager ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_api_key_manager_create_and_validate(api_key_manager):
    result = await api_key_manager.create_key("user-1", "My Key")
    assert "key" in result
    assert result["key"].startswith("ethan_")

    validated = await api_key_manager.validate_key(result["key"])
    assert validated is not None
    assert validated["user_id"] == "user-1"

    assert await api_key_manager.revoke_key(result["id"]) is True
    assert await api_key_manager.validate_key(result["key"]) is None


# ── SCIMManager ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_scim_manager_configure_and_get(scim_manager):
    config = await scim_manager.configure(True, "https://scim.example.com", "token")
    assert config["enabled"] is True

    fetched = await scim_manager.get_config()
    assert fetched["enabled"] is True
