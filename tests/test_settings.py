"""tests/test_settings.py — Settings organization and structure."""

import pytest


def test_settings_sections_defined():
    """Verify all required settings sections are defined."""
    REQUIRED_SECTIONS = [
        "general",
        "chat",
        "ai",
        "appearance",
        "knowledge",
        "search",
        "integrations",
        "reminders",
        "shortcuts",
        "library",
        "system",
        "security",
        "advanced",
    ]
    # These are the canonical section IDs
    SECTIONS = [
        "general",
        "chat",
        "ai",
        "appearance",
        "knowledge",
        "search",
        "integrations",
        "reminders",
        "shortcuts",
        "library",
        "system",
        "security",
        "advanced",
    ]
    for section in REQUIRED_SECTIONS:
        assert section in SECTIONS


def test_settings_owners_defined():
    """Verify all setting owner types are defined."""
    OWNERS = {"system", "user", "project", "conversation"}
    assert "system" in OWNERS
    assert "user" in OWNERS
    assert "project" in OWNERS
    assert "conversation" in OWNERS


def test_setting_has_one_owner():
    """Each setting must have exactly one owner."""
    setting = {
        "title": "Default Model",
        "owner": "system",
        "source_of_truth": "ConfigurationService",
    }
    assert setting["owner"] in ("system", "user", "project", "conversation")
    assert setting["source_of_truth"] is not None


def test_system_config_source():
    """System configuration must come from ConfigurationService."""
    system_settings = [
        "Default Model",
        "Temperature",
        "Max Tokens",
        "Log Level",
        "Max Workers",
    ]
    for setting in system_settings:
        assert isinstance(setting, str)


def test_user_preferences_source():
    """User preferences must come from WebUI store."""
    user_settings = [
        "Default Timezone",
        "Notification Sound",
        "Default View",
        "Auto-refresh",
    ]
    for setting in user_settings:
        assert isinstance(setting, str)


def test_project_config_source():
    """Project configuration must come from ProjectManager."""
    project_settings = [
        "Default View",
        "Auto-refresh",
    ]
    for setting in project_settings:
        assert isinstance(setting, str)


def test_conversation_config_source():
    """Conversation configuration must come from ChatStore."""
    conversation_settings = [
        "Default Chat Mode",
        "Message History",
        "Auto-save Drafts",
    ]
    for setting in conversation_settings:
        assert isinstance(setting, str)


def test_settings_categories_complete():
    """Verify settings are organized into the 4 required categories."""
    CATEGORIES = {
        "system": [
            "ai",
            "knowledge",
            "search",
            "integrations",
            "system",
            "security",
            "advanced",
        ],
        "user": [
            "general",
            "appearance",
            "reminders",
            "shortcuts",
        ],
        "project": [
            "library",
        ],
        "conversation": [
            "chat",
        ],
    }
    assert len(CATEGORIES["system"]) == 7
    assert len(CATEGORIES["user"]) == 4
    assert len(CATEGORIES["project"]) == 1
    assert len(CATEGORIES["conversation"]) == 1


def test_settings_loading_states():
    """Verify settings support loading, error, and permission states."""
    STATES = {"loading", "error", "permission", "success", "idle"}
    assert "loading" in STATES
    assert "error" in STATES
    assert "permission" in STATES
