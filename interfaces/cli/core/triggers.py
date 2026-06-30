"""Presets & Triggers — Déclenchement automatique de skills/plugins par mots-clés.

Système de "presets" inspiré de Jarvis-OS : certains mots-clés dans la conversation
déclenchent automatiquement des actions spécifiques sans que l'utilisateur ait
à taper une commande explicite.

Exemples :
- "météo demain" → déclenche le skill météo
- "traduis hello en français" → déclenche le skill traduction
- "check docker" → déclenche le diagnostic Docker

Les triggers sont configurés dans `~/.config/ethan/triggers.yaml` ou via
le manifeste des plugins (champ `triggers` dans ETHAN_PLUGIN).
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Type pour un trigger
TriggerAction = dict[str, Any]

# Chemin du fichier de configuration des triggers
_TRIGGERS_DIR = Path.home() / ".config" / "ethan"
_TRIGGERS_FILE = _TRIGGERS_DIR / "triggers.yaml"


class TriggerRegistry:
    """Registre des triggers — mots-clés → actions.

    Les triggers sont chargés depuis :
    1. `~/.config/ethan/triggers.yaml` (configuration utilisateur)
    2. Les plugins déclarant un champ `triggers` dans ETHAN_PLUGIN
    3. Les presets installés dans skills/installed/
    """

    _instance = None
    _triggers: list[dict[str, Any]] = []

    def __init__(self) -> None:
        self._triggers = []
        self._loaded = False

    @classmethod
    def get_instance(cls) -> TriggerRegistry:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_all(self) -> None:
        """Charge tous les triggers disponibles."""
        self._triggers = []

        # 1. Fichier utilisateur
        self._load_user_triggers()

        # 2. Plugins avec triggers dans ETHAN_PLUGIN
        self._load_plugin_triggers()

        self._loaded = True
        logger.info("TriggerRegistry: %d triggers chargés", len(self._triggers))

    def _load_user_triggers(self) -> None:
        """Charge les triggers depuis le fichier YAML utilisateur."""
        if not _TRIGGERS_FILE.exists():
            return

        try:
            import yaml
            with _TRIGGERS_FILE.open() as f:
                data = yaml.safe_load(f) or {}
            for trigger in data.get("triggers", []):
                self._register(trigger)
        except Exception as e:
            logger.warning("TriggerRegistry: erreur chargement %s: %s", _TRIGGERS_FILE, e)

    def _load_plugin_triggers(self) -> None:
        """Scanne les plugins installés pour leurs triggers."""
        plugins_dir = Path.home() / ".local" / "share" / "ethan" / "plugins"
        if not plugins_dir.exists():
            return

        for plugin_dir in plugins_dir.iterdir():
            manifest_path = plugin_dir / "manifest.json"
            if not manifest_path.exists():
                continue
            try:
                import json
                with manifest_path.open() as f:
                    manifest = json.load(f)
                triggers = manifest.get("triggers", [])
                for trigger in triggers:
                    trigger["source"] = f"plugin:{manifest.get('name', plugin_dir.name)}"
                    self._register(trigger)
            except Exception as e:
                logger.warning("TriggerRegistry: plugin %s: %s", plugin_dir.name, e)

    def _register(self, trigger: dict[str, Any]) -> None:
        """Enregistre un trigger validé."""
        if "pattern" not in trigger and "keywords" not in trigger:
            return
        if "action" not in trigger:
            return
        # Normaliser
        if "pattern" in trigger:
            trigger["type"] = "regex"
        elif "keywords" in trigger:
            trigger["type"] = "keyword"
            trigger["keywords"] = [k.lower() for k in trigger["keywords"]]
        trigger.setdefault("source", "user")
        trigger.setdefault("priority", 0)
        trigger.setdefault("description", "")
        self._triggers.append(trigger)

    def match(self, text: str) -> list[dict[str, Any]]:
        """Trouve les triggers correspondant à un texte.

        Retourne une liste de triggers matchés, triés par priorité.
        """
        if not self._loaded:
            self.load_all()

        text_lower = text.lower()
        matches = []

        for trigger in self._triggers:
            score = self._match_single(trigger, text_lower)
            if score > 0:
                matches.append({
                    **trigger,
                    "match_score": score,
                })

        # Trier par priorité puis score
        matches.sort(key=lambda m: (-m.get("priority", 0), -m.get("match_score", 0)))
        return matches

    def _match_single(self, trigger: dict[str, Any], text: str) -> float:
        """Score de matching pour un trigger (0 = pas match)."""
        ttype = trigger.get("type", "keyword")

        if ttype == "regex":
            pattern = trigger.get("pattern", "")
            try:
                if re.search(pattern, text, re.IGNORECASE):
                    return 1.0
            except re.error:
                pass
            return 0.0

        if ttype == "keyword":
            keywords = trigger.get("keywords", [])
            if not keywords:
                return 0.0
            found = sum(1 for kw in keywords if kw in text)
            if found == 0:
                return 0.0
            # Score proportionnel aux mots-clés trouvés
            return found / len(keywords)

        return 0.0

    def find_best_match(self, text: str) -> dict[str, Any] | None:
        """Trouve le meilleur trigger pour un texte."""
        matches = self.match(text)
        return matches[0] if matches else None

    def list_triggers(self) -> list[dict[str, Any]]:
        """Liste tous les triggers enregistrés."""
        if not self._loaded:
            self.load_all()
        return list(self._triggers)

    def reload(self) -> None:
        """Recharge tous les triggers."""
        self._loaded = False
        self.load_all()

    def add_user_trigger(
        self,
        keywords: list[str],
        action: str,
        command: str = "",
        description: str = "",
    ) -> bool:
        """Ajoute un trigger utilisateur."""
        trigger = {
            "keywords": keywords,
            "action": action,
            "command": command,
            "description": description,
            "source": "user",
            "priority": 0,
        }
        self._register(trigger)
        self._save_user_triggers()
        return True

    def _save_user_triggers(self) -> None:
        """Sauvegarde les triggers utilisateur dans le fichier YAML."""
        user_triggers = [t for t in self._triggers if t.get("source") == "user"]
        try:
            _TRIGGERS_DIR.mkdir(parents=True, exist_ok=True)
            import yaml
            with _TRIGGERS_FILE.open("w") as f:
                yaml.dump({"triggers": user_triggers}, f, default_flow_style=False)
        except Exception as e:
            logger.warning("TriggerRegistry: sauvegarde échouée: %s", e)


# Instance globale
trigger_registry = TriggerRegistry.get_instance()


def check_triggers(text: str) -> str | None:
    """Vérifie si un texte déclenche un preset.

    Retourne la commande à exécuter, ou None si pas de match.
    """
    match = trigger_registry.find_best_match(text)
    if match is None:
        return None

    action = match.get("action", "")
    command = match.get("command", "")

    logger.info(
        "Trigger match: '%s' → %s (action=%s, source=%s)",
        text[:50], match.get("description", "?"), action, match.get("source", "?"),
    )

    if action == "command":
        return command
    if action == "skill":
        # Format: /run <skill_name>
        return f"Skill détecté : {match.get('description', '?')}"
    # action == "notify" : ne pas intercepter, juste logger
    return None