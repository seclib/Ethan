"""Tests basiques pour le module Triggers."""

import pytest
from interfaces.cli.core.triggers import TriggerRegistry, check_triggers


@pytest.fixture
def registry():
    """TriggerRegistry frais pour chaque test."""
    reg = TriggerRegistry()
    reg._triggers = []
    reg._loaded = True
    return reg


def test_keyword_match(registry):
    registry._register({
        "keywords": ["docker", "conteneur"],
        "action": "command",
        "command": "docker status",
        "description": "Docker",
        "source": "test",
        "priority": 5,
    })
    matches = registry.match("check docker status")
    assert len(matches) >= 1
    assert matches[0]["command"] == "docker status"


def test_regex_match(registry):
    registry._register({
        "pattern": r"météo.*demain",
        "action": "command",
        "command": "weather tomorrow",
        "description": "Météo",
        "source": "test",
        "priority": 10,
    })
    matches = registry.match("météo pour demain")
    assert len(matches) >= 1
    assert "tomorrow" in matches[0]["command"]


def test_priority_ordering(registry):
    registry._register({
        "keywords": ["test"],
        "action": "command",
        "command": "low",
        "source": "test",
        "priority": 1,
    })
    registry._register({
        "keywords": ["test"],
        "action": "command",
        "command": "high",
        "source": "test",
        "priority": 10,
    })
    matches = registry.match("test")
    assert len(matches) == 2
    assert matches[0]["command"] == "high"  # priorité 10 d'abord


def test_no_match(registry):
    registry._register({
        "keywords": ["docker"],
        "action": "command",
        "command": "docker",
        "source": "test",
    })
    matches = registry.match("complètement autre chose")
    assert len(matches) == 0


def test_check_triggers_helper():
    """Test de la fonction utilitaire check_triggers."""
    # Pas de trigger configuré → None
    result = check_triggers("texte sans trigger")
    assert result is None