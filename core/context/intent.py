"""Intent Model — Ethan OS

Toutes les entrées sont normalisées en Intent.
Le Planner ne reçoit que des Intent objects.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class Intent:
    """Structure unifiée pour toutes les entrées."""
    source: str  # "voice", "text", "api", "automation"
    user_input: str
    context: dict
    timestamp: datetime

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class IntentParser(ABC):
    """Interface pour normaliser les entrées en Intent."""

    @abstractmethod
    async def parse(self, raw_input: Any) -> Intent:
        pass


class TextIntentParser(IntentParser):
    async def parse(self, raw_input: str) -> Intent:
        return Intent(
            source="text",
            user_input=raw_input,
            context={},
            timestamp=datetime.utcnow(),
        )


class APIIntentParser(IntentParser):
    async def parse(self, raw_input: dict) -> Intent:
        return Intent(
            source="api",
            user_input=raw_input.get("input", ""),
            context=raw_input.get("context", {}),
            timestamp=datetime.utcnow(),
        )


class VoiceIntentParser(IntentParser):
    async def parse(self, raw_input: dict) -> Intent:
        return Intent(
            source="voice",
            user_input=raw_input.get("transcript", ""),
            context={
                "language": raw_input.get("language", "en"),
                "confidence": raw_input.get("confidence", 1.0),
                "audio_metadata": raw_input.get("audio_metadata", {}),
            },
            timestamp=datetime.utcnow(),
        )


class AutomationIntentParser(IntentParser):
    async def parse(self, raw_input: dict) -> Intent:
        return Intent(
            source="automation",
            user_input=raw_input.get("trigger", ""),
            context={
                "automation_id": raw_input.get("automation_id"),
                "trigger_type": raw_input.get("trigger_type", "scheduled"),
                "payload": raw_input.get("payload", {}),
            },
            timestamp=datetime.utcnow(),
        )


class IntentRouter:
    """Route et normalise tous les inputs vers un Intent unifié."""

    def __init__(self):
        self._parsers = {
            "text": TextIntentParser(),
            "api": APIIntentParser(),
            "voice": VoiceIntentParser(),
            "automation": AutomationIntentParser(),
        }

    async def parse(self, source: str, raw_input: Any) -> Intent:
        parser = self._parsers.get(source)
        if parser is None:
            raise ValueError(f"Unknown intent source: {source}")
        return await parser.parse(raw_input)
