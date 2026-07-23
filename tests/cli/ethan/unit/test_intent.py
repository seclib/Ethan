"""Tests for cli/core/intent.py — prompt intelligence."""
from __future__ import annotations

import pytest


class TestPromptIntelligence:
    """PromptIntelligence class tests."""

    def test_classify_empty_string(self) -> None:
        from cli.core.intent import PromptIntelligence
        intent = PromptIntelligence.classify("")
        assert intent.kind == "chat"
        assert intent.confidence == 0.0

    def test_classify_chat(self) -> None:
        from cli.core.intent import PromptIntelligence
        intent = PromptIntelligence.classify("Hello, how are you?")
        assert intent.kind == "chat"

    def test_classify_exact_command(self) -> None:
        from cli.core.intent import PromptIntelligence
        intent = PromptIntelligence.classify("status")
        assert intent.kind == "command"
        assert intent.confidence == 1.0

    def test_classify_smart_command(self) -> None:
        from cli.core.intent import PromptIntelligence
        intent = PromptIntelligence.classify("logs --follow")
        assert intent.kind == "smart_cmd"
        assert intent.confidence == 0.95

    def test_classify_fix_intent(self) -> None:
        from cli.core.intent import PromptIntelligence
        intent = PromptIntelligence.classify("fix docker")
        assert intent.kind == "intent"
        assert intent.params["target"] == "docker"

    def test_classify_check_intent(self) -> None:
        from cli.core.intent import PromptIntelligence
        intent = PromptIntelligence.classify("check api health")
        assert intent.kind == "intent"
        assert intent.params["target"] == "api"
        assert intent.params["aspect"] == "health"

    def test_classify_run_intent(self) -> None:
        from cli.core.intent import PromptIntelligence
        intent = PromptIntelligence.classify("run tests")
        assert intent.kind == "intent"
        assert intent.params["cmd"] == "tests"

    def test_classify_deploy_intent(self) -> None:
        from cli.core.intent import PromptIntelligence
        intent = PromptIntelligence.classify("deploy app to prod")
        assert intent.kind == "intent"
        assert intent.params["target"] == "app"
        assert intent.params["env"] == "prod"

    def test_classify_logs_intent(self) -> None:
        from cli.core.intent import PromptIntelligence
        intent = PromptIntelligence.classify("logs")
        # "logs" matches smart_cmd via FUZZY_MAP
        assert intent.kind == "smart_cmd"

    def test_classify_status_intent(self) -> None:
        from cli.core.intent import PromptIntelligence
        intent = PromptIntelligence.classify("status")
        assert intent.kind == "command"

    def test_classify_help_intent(self) -> None:
        from cli.core.intent import PromptIntelligence
        intent = PromptIntelligence.classify("help")
        assert intent.kind == "command"  # 'help' is in KNOWN_COMMANDS

    def test_suggest_next_for_intent(self) -> None:
        from cli.core.intent import PromptIntelligence
        intent = PromptIntelligence.classify("fix docker")
        suggestions = PromptIntelligence.suggest_next([], intent)
        assert len(suggestions) > 0
        assert isinstance(suggestions[0], str)

    def test_suggest_next_for_logs(self) -> None:
        from cli.core.intent import PromptIntelligence
        intent = PromptIntelligence.classify("logs")
        suggestions = PromptIntelligence.suggest_next([], intent)
        assert len(suggestions) > 0

    def test_suggest_next_for_status(self) -> None:
        from cli.core.intent import PromptIntelligence
        intent = PromptIntelligence.classify("status")
        suggestions = PromptIntelligence.suggest_next([], intent)
        assert len(suggestions) > 0

    def test_suggest_next_limited_to_three(self) -> None:
        from cli.core.intent import PromptIntelligence
        intent = PromptIntelligence.classify("fix api")
        suggestions = PromptIntelligence.suggest_next([], intent)
        assert len(suggestions) <= 3

    def test_autocomplete_from_fuzzy_map(self) -> None:
        from cli.core.intent import PromptIntelligence
        completions = PromptIntelligence.autocomplete("lo", [])
        assert len(completions) > 0
        assert "logs" in completions

    def test_autocomplete_from_history(self) -> None:
        from cli.core.intent import PromptIntelligence
        completions = PromptIntelligence.autocomplete("ch", ["chat", "check", "run"])
        assert "chat" in completions

    def test_autocomplete_limited_to_five(self) -> None:
        from cli.core.intent import PromptIntelligence
        completions = PromptIntelligence.autocomplete("c", ["chat", "check", "config", "cmd1", "cmd2", "cmd3"])
        assert len(completions) <= 5

    def test_confidence_label_high(self) -> None:
        from cli.core.intent import PromptIntelligence
        assert PromptIntelligence.confidence_label(0.95) == "high"

    def test_confidence_label_medium(self) -> None:
        from cli.core.intent import PromptIntelligence
        assert PromptIntelligence.confidence_label(0.75) == "medium"

    def test_confidence_label_low(self) -> None:
        from cli.core.intent import PromptIntelligence
        assert PromptIntelligence.confidence_label(0.3) == "low"

    def test_prompt_intent_repr(self) -> None:
        from cli.core.intent import PromptIntent
        intent = PromptIntent("chat", 0.5, {"text": "hi"}, "hi")
        assert "PromptIntent" in repr(intent)
        assert "chat" in repr(intent)