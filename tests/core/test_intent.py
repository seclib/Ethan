"""Tests — Intent Model (ADR-1003)"""

from datetime import datetime
from unittest.mock import patch
import pytest

from core.context.intent import (
    Intent,
    IntentParser,
    TextIntentParser,
    APIIntentParser,
    VoiceIntentParser,
    AutomationIntentParser,
    IntentRouter,
)


@pytest.fixture
def fixed_time():
    return datetime(2024, 1, 1, 12, 0, 0)


class TestIntent:
    def test_intent_default_timestamp(self, fixed_time):
        with patch("core.context.intent.datetime") as mock_dt:
            mock_dt.utcnow.return_value = fixed_time
            intent = Intent(source="text", user_input="hello", context={}, timestamp=None)
            assert intent.timestamp == fixed_time

    def test_intent_explicit_timestamp(self):
        ts = datetime(2024, 6, 1, 10, 0, 0)
        intent = Intent(source="text", user_input="hello", context={}, timestamp=ts)
        assert intent.timestamp == ts


class TestTextIntentParser:
    @pytest.mark.asyncio
    async def test_parse(self):
        parser = TextIntentParser()
        intent = await parser.parse("Hello world")
        assert intent.source == "text"
        assert intent.user_input == "Hello world"
        assert intent.context == {}


class TestAPIIntentParser:
    @pytest.mark.asyncio
    async def test_parse_with_context(self):
        parser = APIIntentParser()
        raw = {"input": "API call", "context": {"user_id": "123"}}
        intent = await parser.parse(raw)
        assert intent.source == "api"
        assert intent.user_input == "API call"
        assert intent.context == {"user_id": "123"}

    @pytest.mark.asyncio
    async def test_parse_missing_fields(self):
        parser = APIIntentParser()
        intent = await parser.parse({})
        assert intent.source == "api"
        assert intent.user_input == ""
        assert intent.context == {}


class TestVoiceIntentParser:
    @pytest.mark.asyncio
    async def test_parse(self):
        parser = VoiceIntentParser()
        raw = {
            "transcript": "Turn on lights",
            "language": "fr",
            "confidence": 0.95,
            "audio_metadata": {"duration": 2.3},
        }
        intent = await parser.parse(raw)
        assert intent.source == "voice"
        assert intent.user_input == "Turn on lights"
        assert intent.context["language"] == "fr"
        assert intent.context["confidence"] == 0.95
        assert intent.context["audio_metadata"]["duration"] == 2.3

    @pytest.mark.asyncio
    async def test_parse_defaults(self):
        parser = VoiceIntentParser()
        intent = await parser.parse({"transcript": "test"})
        assert intent.context["language"] == "en"
        assert intent.context["confidence"] == 1.0
        assert intent.context["audio_metadata"] == {}


class TestAutomationIntentParser:
    @pytest.mark.asyncio
    async def test_parse(self):
        parser = AutomationIntentParser()
        raw = {
            "trigger": "daily_report",
            "automation_id": "auto_001",
            "trigger_type": "scheduled",
            "payload": {"time": "08:00"},
        }
        intent = await parser.parse(raw)
        assert intent.source == "automation"
        assert intent.user_input == "daily_report"
        assert intent.context["automation_id"] == "auto_001"
        assert intent.context["trigger_type"] == "scheduled"
        assert intent.context["payload"]["time"] == "08:00"

    @pytest.mark.asyncio
    async def test_parse_defaults(self):
        parser = AutomationIntentParser()
        intent = await parser.parse({"trigger": "backup"})
        assert intent.context["automation_id"] is None
        assert intent.context["trigger_type"] == "scheduled"
        assert intent.context["payload"] == {}


class TestIntentRouter:
    @pytest.mark.asyncio
    async def test_route_text(self):
        router = IntentRouter()
        intent = await router.parse("text", "Hello")
        assert intent.source == "text"
        assert intent.user_input == "Hello"

    @pytest.mark.asyncio
    async def test_route_api(self):
        router = IntentRouter()
        intent = await router.parse("api", {"input": "ping", "context": {}})
        assert intent.source == "api"
        assert intent.user_input == "ping"

    @pytest.mark.asyncio
    async def test_route_voice(self):
        router = IntentRouter()
        intent = await router.parse("voice", {"transcript": "hello"})
        assert intent.source == "voice"
        assert intent.user_input == "hello"

    @pytest.mark.asyncio
    async def test_route_automation(self):
        router = IntentRouter()
        intent = await router.parse("automation", {"trigger": "job"})
        assert intent.source == "automation"
        assert intent.user_input == "job"

    @pytest.mark.asyncio
    async def test_route_unknown_source(self):
        router = IntentRouter()
        with pytest.raises(ValueError, match="Unknown intent source"):
            await router.parse("unknown", {})