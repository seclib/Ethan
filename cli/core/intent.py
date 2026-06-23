"""ETHAN Prompt Intelligence — intent detection, smart suggestions, auto-execution.

Usage:
    from core.intent import PromptIntelligence

    pi = PromptIntelligence()
    intent = pi.classify("fix docker")
    if intent.confidence >= 0.9:
        pi.execute(intent)
    else:
        pi.suggest(intent)
"""

import re

# Command registry for smart_cmd detection
KNOWN_COMMANDS = ["chat", "run", "status", "logs", "plugin", "shell", "help", "daemon", "config"]

# Intent patterns: (regex, intent_type, extractor)
INTENT_PATTERNS = [
    (r"^(fix|repair|debug)\s+(\w+)$", "fix", lambda m: {"target": m.group(2)}),
    (r"^(check|health|diagnose)\s+(\w+)(?:\s+(\w+))?$", "check", lambda m: {"target": m.group(2), "aspect": m.group(3) or ""}),
    (r"^(run|execute|exec)\s+(.+)$", "run", lambda m: {"cmd": m.group(2)}),
    (r"^(deploy)\s+(\w+)(?:\s+to\s+(\w+))?$", "deploy", lambda m: {"target": m.group(2), "env": m.group(3) or ""}),
    (r"^(logs|log)\s*(?:for\s+(\w+))?$", "logs", lambda m: {"service": m.group(2) or ""}),
    (r"^(status|state|info)$", "status", lambda m: {}),
    (r"^(help|--help|-h)$", "help", lambda m: {}),
]

# Fuzzy command map (shorthand → full command)
FUZZY_MAP = {
    "logs": "logs",
    "log": "logs",
    "status": "status",
    "state": "status",
    "info": "status",
    "help": "help",
    "plugins": "plugin list",
    "plugin": "plugin list",
    "chat": "chat",
    "run": "run",
}


class PromptIntent:
    """Detected user intent with confidence and params."""

    def __init__(self, kind: str, confidence: float, params: dict, raw: str):
        self.kind = kind  # command, intent, chat, smart_cmd
        self.confidence = confidence
        self.params = params
        self.raw = raw

    def __repr__(self):
        return f"PromptIntent({self.kind}, {self.confidence:.2f}, {self.params})"


class PromptIntelligence:
    """Detect and act on user intent from natural input."""

    @staticmethod
    def classify(text: str) -> PromptIntent:
        text = text.strip()
        if not text:
            return PromptIntent("chat", 0.0, {}, text)

        # 1. Exact command match
        first = text.split()[0]
        if first in KNOWN_COMMANDS:
            return PromptIntent("command", 1.0, {"cmd": text}, text)

        # 2. Smart command (shorthand)
        if first in FUZZY_MAP:
            return PromptIntent("smart_cmd", 0.95, {"cmd": FUZZY_MAP[first], "args": text[len(first):].strip()}, text)

        # 3. Intent patterns
        for pattern, kind, extractor in INTENT_PATTERNS:
            m = re.match(pattern, text, re.IGNORECASE)
            if m:
                return PromptIntent("intent", 0.9, extractor(m), text)

        # 4. Default: chat
        return PromptIntent("chat", 0.0, {"text": text}, text)

    @staticmethod
    def suggest_next(history: list[str], current: PromptIntent) -> list[str]:
        """Suggest next actions based on history and current intent."""
        suggestions = []
        if current.kind == "intent":
            if current.params.get("target") == "docker":
                suggestions = ["check docker stats", "deploy app", "run tests"]
            elif current.params.get("target") == "api":
                suggestions = ["check api health", "run api tests", "restart api"]
            else:
                suggestions = ["run tests", "check status", "show logs"]
        elif current.kind == "smart_cmd" and current.params.get("cmd") == "logs":
            suggestions = ["logs --follow", "status", "run tests"]
        elif current.kind == "status":
            suggestions = ["run tests", "deploy staging", "show logs"]
        return suggestions[:3]

    @staticmethod
    def autocomplete(prefix: str, history: list[str]) -> list[str]:
        """Suggest completions for a partial input."""
        prefix = prefix.lower()
        # From fuzzy map
        matches = [v for k, v in FUZZY_MAP.items() if v.startswith(prefix)]
        # From history
        hist = [h for h in history if h.lower().startswith(prefix)]
        # Merge, deduplicate, limit
        seen = set()
        result = []
        for m in matches + hist:
            if m not in seen:
                seen.add(m)
                result.append(m)
            if len(result) >= 5:
                break
        return result

    @staticmethod
    def confidence_label(conf: float) -> str:
        if conf >= 0.9:
            return "high"
        if conf >= 0.6:
            return "medium"
        return "low"