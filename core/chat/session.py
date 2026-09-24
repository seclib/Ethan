"""ETHAN Core — Session settings (chat).

Réglages de session du chat : source de vérité unique côté Core.  Le WebUI
affiche et envoie des intents via l'API — il ne détient aucun état métier.

Modèle de priorité (§26 du cahier des charges) :

    request context  >  session (par conversation)  >  mode profile  >  global

Chaque niveau n'ajoute que ce qu'il a le droit de surcharger ; la résolution
produit :class:`ResolvedSessionSettings` — la configuration effective que le
pipeline applique réellement (reasoning borné aux capacités du modèle).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, replace
from typing import Any

from core.chat.modes import (
    AutoApproval,
    ChatMode,
    CompactionStrategy,
    DebugLevel,
    ModeProfile,
    ReasoningEffort,
    SystemAccess,
    TerminalCommandPolicy,
    TerminalPermission,
    default_mode_profiles,
    mode_system_instructions,
    resolve_reasoning,
)

logger = logging.getLogger(__name__)

_DOMAIN = "chat_session"


@dataclass
class ResolvedSessionSettings:
    """Configuration effective d'une requête de chat (résolue)."""

    chat_id: str = ""
    mode: ChatMode = ChatMode.ACT
    provider_id: str = ""
    model: str = ""
    reasoning: dict[str, Any] = field(
        default_factory=lambda: {"effort": ReasoningEffort.NONE.value, "supported": True}
    )
    auto_compact: bool = True
    compaction_strategy: CompactionStrategy = CompactionStrategy.BALANCED
    system_access: SystemAccess = SystemAccess.WORKSPACE
    debug_level: DebugLevel = DebugLevel.DIAGNOSE
    terminal: TerminalCommandPolicy = field(default_factory=TerminalCommandPolicy)
    auto_approval: AutoApproval = AutoApproval.OFF
    language: str = ""
    permissions: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "chat_id": self.chat_id,
            "mode": self.mode.value,
            "provider_id": self.provider_id,
            "model": self.model,
            "reasoning": dict(self.reasoning),
            "auto_compact": self.auto_compact,
            "compaction_strategy": self.compaction_strategy.value,
            "system_access": self.system_access.value,
            "debug_level": self.debug_level.value,
            "terminal": self.terminal.to_dict(),
            "auto_approval": self.auto_approval.value,
            "language": self.language,
            "permissions": dict(self.permissions),
        }


class SessionSettingsManager:
    """Persistance + résolution des réglages de session (Core-owned).

    Args:
        store: CoreRecordStore (domaine ``chat_session``).
        chats: ChatStore optionnel — réglages par conversation (metadata).
    """

    def __init__(self, store: Any, chats: Any | None = None) -> None:
        self._store = store
        self._chats = chats

    # ── Global ────────────────────────────────────────────────────────────

    async def get_global(self) -> dict[str, Any]:
        record = await self._store.get(_DOMAIN, "global")
        return dict(record) if record else {}

    async def update_global(self, data: dict[str, Any]) -> dict[str, Any]:
        current = await self.get_global()
        current.update(data)
        await self._store.save(_DOMAIN, "global", current)
        return dict(current)

    # ── Mode profiles ─────────────────────────────────────────────────────

    async def get_mode_profile(self, mode: ChatMode | str) -> ModeProfile:
        """Profil d'un mode (persistance + fallback defaults)."""
        mode_value = mode.value if isinstance(mode, ChatMode) else str(mode)
        defaults = default_mode_profiles()
        try:
            profile = defaults[mode_value]
        except KeyError:
            raise ValueError(f"Unknown chat mode: {mode_value}") from None
        try:
            record = await self._store.get(_DOMAIN, f"mode:{mode_value}")
        except Exception as exc:
            logger.warning("Mode profile load failed: %s", exc)
            record = None
        if not record:
            return profile
        return self._hydrate_profile(profile, record)

    async def update_mode_profile(
        self, mode: ChatMode | str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Mettre à jour un profil de mode (validation stricte des clés)."""
        mode_value = mode.value if isinstance(mode, ChatMode) else str(mode)
        if mode_value not in [m.value for m in ChatMode]:
            raise ValueError(f"Unknown chat mode: {mode_value}")
        current = (await self.get_mode_profile(mode_value)).to_dict()
        allowed = {
            "provider_id",
            "model",
            "reasoning_effort",
            "auto_compact",
            "system_access",
            "compaction_strategy",
            "debug_level",
            "terminal",
            "auto_approval",
            "language",
        }
        for key in allowed:
            if key in data:
                current[key] = data[key]
        await self._store.save(_DOMAIN, f"mode:{mode_value}", current)
        return current

    async def list_mode_profiles(self) -> list[dict[str, Any]]:
        """Catalogue des modes (profils + instructions) pour l'API/UI."""
        result = []
        for mode in ChatMode:
            profile = await self.get_mode_profile(mode)
            result.append({**profile.to_dict(), "instructions": mode_system_instructions(mode)})
        return result

    def _hydrate_profile(self, base: ModeProfile, record: dict[str, Any]) -> ModeProfile:
        """Réhydrate un ModeProfile depuis un dict persisté."""
        try:
            terminal_data = record.get("terminal") or {}
            return replace(
                base,
                provider_id=str(record.get("provider_id") or ""),
                model=str(record.get("model") or ""),
                reasoning_effort=ReasoningEffort(
                    str(record.get("reasoning_effort") or base.reasoning_effort.value)
                ),
                auto_compact=bool(record.get("auto_compact", base.auto_compact)),
                system_access=SystemAccess(
                    str(record.get("system_access") or base.system_access.value)
                ),
                compaction_strategy=CompactionStrategy(
                    str(record.get("compaction_strategy") or base.compaction_strategy.value)
                ),
                debug_level=DebugLevel(str(record.get("debug_level") or base.debug_level.value)),
                terminal=TerminalCommandPolicy(
                    allowed=list(terminal_data.get("allowed") or []),
                    denied=list(terminal_data.get("denied") or []),
                    default=TerminalPermission(
                        str(terminal_data.get("default") or base.terminal.default.value)
                    ),
                ),
                auto_approval=AutoApproval(
                    str(record.get("auto_approval") or base.auto_approval.value)
                ),
                language=str(record.get("language") or ""),
            )
        except (ValueError, TypeError) as exc:
            logger.warning("Mode profile hydration failed, using defaults: %s", exc)
            return base

    # ── Session (par conversation) ────────────────────────────────────────

    async def get_session(self, chat_id: str) -> dict[str, Any]:
        """Réglages d'une conversation (metadata ChatStore)."""
        if not chat_id or self._chats is None:
            return {}
        chat = await self._chats.get_chat(chat_id)
        if not chat:
            return {}
        return dict(chat.get("session_settings") or {})

    async def update_session(self, chat_id: str, data: dict[str, Any]) -> dict[str, Any]:
        if self._chats is None:
            raise RuntimeError("ChatStore not injected into SessionSettingsManager")
        current = await self.get_session(chat_id)
        current.update(data)
        chat = await self._chats.update_chat(chat_id, {"session_settings": current})
        return dict(chat.get("session_settings") or current)

    # ── Résolution (§26) ─────────────────────────────────────────────────

    async def resolve(
        self,
        *,
        chat_id: str = "",
        mode: ChatMode | str | None = None,
        overrides: dict[str, Any] | None = None,
        model_capabilities: list[str] | None = None,
    ) -> ResolvedSessionSettings:
        """Résoudre la configuration effective.

        Priorité : ``overrides`` (requête) > session (conversation) >
        mode profile > global.  Le reasoning est borné aux capacités du
        modèle cible — jamais de valeur fantôme.
        """
        from core.chat.modes import effective_mode_permissions

        global_settings = await self.get_global()
        request = dict(overrides or {})
        session = await self.get_session(chat_id)
        if isinstance(mode, ChatMode):
            mode_value = mode.value
        else:
            mode_value = str(
                mode
                or request.get("mode")
                or session.get("mode")
                or global_settings.get("mode")
                or ChatMode.ACT.value
            )
        try:
            mode_enum = ChatMode(mode_value)
        except ValueError:
            mode_enum = ChatMode.ACT
        profile = await self.get_mode_profile(mode_enum)

        def pick(key: str, default: Any = "") -> Any:
            # request > session > mode profile > global
            for layer in (request, session):
                value = layer.get(key)
                if value is not None and value != "":
                    return value
            profile_value = getattr(profile, key, None)
            if profile_value not in (None, ""):
                return profile_value
            return global_settings.get(key, default)

        provider_id = str(pick("provider_id", ""))
        model = str(pick("model", ""))
        reasoning = resolve_reasoning(pick("reasoning_effort", None), model_capabilities)
        auto_compact = bool(pick("auto_compact", True))

        def enum_pick(enum_cls, key, fallback):
            try:
                return enum_cls(str(pick(key, fallback.value)))
            except (ValueError, TypeError):
                return fallback

        strategy = enum_pick(CompactionStrategy, "compaction_strategy", profile.compaction_strategy)
        access = enum_pick(SystemAccess, "system_access", profile.system_access)
        debug_level = enum_pick(DebugLevel, "debug_level", profile.debug_level)
        approval = enum_pick(AutoApproval, "auto_approval", profile.auto_approval)

        # Terminal : la session et la requête ne peuvent que SERRER la
        # politique du profil (patterns deny additionnels ; jamais élargir
        # le default) — le frontend n'est jamais une frontière de sécurité.
        terminal = profile.terminal
        for layer in (session, request):
            term = layer.get("terminal")
            if isinstance(term, dict):
                denied = list(term.get("denied") or [])
                allowed = list(term.get("allowed") or [])
                terminal = TerminalCommandPolicy(
                    allowed=allowed if allowed else terminal.allowed,
                    denied=list({*terminal.denied, *denied}) if denied else terminal.denied,
                    default=terminal.default,
                )

        perms = effective_mode_permissions(mode_enum, debug_level)

        return ResolvedSessionSettings(
            chat_id=chat_id,
            mode=mode_enum,
            provider_id=provider_id,
            model=model,
            reasoning=reasoning,
            auto_compact=auto_compact,
            compaction_strategy=strategy,
            system_access=access,
            debug_level=debug_level,
            terminal=terminal,
            auto_approval=approval,
            language=str(pick("language", profile.language)),
            permissions=perms.to_dict(),
        )


__all__ = [
    "ResolvedSessionSettings",
    "SessionSettingsManager",
]
