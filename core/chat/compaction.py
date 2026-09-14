"""ETHAN Core — Auto Compact (compaction intelligente du contexte).

Surveille la fenêtre de contexte du modèle et compacte l'historique quand la
requête s'approche de la limite (§14/§16).  La compaction est **préservante** :
elle ne tronque pas aveuglément — elle résume les messages anciens en gardant
en clair les éléments critiques (§16) :

    instructions système · mode actif · exigences utilisateur · tâche en cours ·
    décisions importantes · fichiers en cours de modification · erreurs
    pertinentes · état des outils · actions en attente

Les stratégies (§15) ne changent que les seuils de déclenchement et le volume
d'historique résumé — il n'existe qu'UN SEUL moteur de compaction (Core).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from core.chat.modes import CompactionStrategy

logger = logging.getLogger(__name__)

# Approximation standard chars ≈ tokens/4 (heuristic, provider-agnostic).
_CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    """Estimation du nombre de tokens (heuristique chars/4)."""
    return max(0, len(text or "")) // _CHARS_PER_TOKEN


@dataclass
class CompactionThresholds:
    """Seuils de déclenchement par stratégie (fraction de la fenêtre)."""

    # Fraction de la fenêtre qui déclenche la compaction.
    trigger: float
    # Fraction de l'historique (messages anciens) résumée.
    summarize_fraction: float
    # Nombre de messages récents TOUJOURS conservés en clair.
    keep_recent: int


STRATEGY_THRESHOLDS: dict[str, CompactionThresholds] = {
    CompactionStrategy.CONSERVATIVE.value: CompactionThresholds(
        trigger=0.90, summarize_fraction=0.30, keep_recent=8
    ),
    CompactionStrategy.BALANCED.value: CompactionThresholds(
        trigger=0.75, summarize_fraction=0.50, keep_recent=6
    ),
    CompactionStrategy.AGGRESSIVE.value: CompactionThresholds(
        trigger=0.55, summarize_fraction=0.70, keep_recent=4
    ),
}


@dataclass
class CompactionResult:
    """Outcome d'une compaction (journalisée dans le chat)."""

    compacted: bool = False
    strategy: str = CompactionStrategy.BALANCED.value
    estimated_tokens_before: int = 0
    estimated_tokens_after: int = 0
    summarized_messages: int = 0
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "compacted": self.compacted,
            "strategy": self.strategy,
            "estimated_tokens_before": self.estimated_tokens_before,
            "estimated_tokens_after": self.estimated_tokens_after,
            "summarized_messages": self.summarized_messages,
            "summary": self.summary,
        }


# Marqueurs prioritaires — le résumé cite ces éléments en clair (§16).
_PRIORITY_MARKERS = (
    "[Instructions système]", "[Mode", "[Exigences", "[Décision", "[Fichier",
    "[Erreur", "[Outil", "[Action en attente", "[Tâche", "[Correctif",
)


class AutoCompactManager:
    """Surveillance + compaction du contexte conversationnel (Core-owned).

    Args:
        provider_manager: ProviderManager Core — le résumé est produit par
            le provider actif (aucun second LLM, aucun moteur parallèle).
    """

    def __init__(self, provider_manager: Any | None = None) -> None:
        self._manager = provider_manager

    def set_provider_manager(self, manager: Any) -> None:
        self._manager = manager

    @staticmethod
    def thresholds(strategy: CompactionStrategy | str) -> CompactionThresholds:
        strategy_value = strategy.value if isinstance(strategy, CompactionStrategy) else str(strategy)
        try:
            return STRATEGY_THRESHOLDS[CompactionStrategy(strategy_value).value]
        except ValueError:
            return STRATEGY_THRESHOLDS[CompactionStrategy.BALANCED.value]

    @staticmethod
    def estimate_history_tokens(history: list[dict[str, Any]], attached_context: str = "") -> int:
        """Tokens estimés pour l'historique + le contexte attaché (§14)."""
        total = 0
        for message in history:
            total += estimate_tokens(str(message.get("content") or ""))
            total += estimate_tokens(str(message.get("metadata") or ""))
        total += estimate_tokens(attached_context)
        return total

    def should_compact(
        self,
        *,
        history: list[dict[str, Any]],
        model_context_length: int,
        strategy: CompactionStrategy | str = CompactionStrategy.BALANCED,
        attached_context: str = "",
        request_tokens: int = 0,
    ) -> tuple[bool, int, CompactionThresholds]:
        """Déclencher la compaction ?

        Returns:
            (should, estimated_tokens, thresholds appliqués).
        """
        th = self.thresholds(strategy)
        estimated = self.estimate_history_tokens(history, attached_context) + request_tokens
        limit = max(1, model_context_length or 0) * th.trigger
        return (estimated >= limit and len(history) > th.keep_recent), estimated, th

    @staticmethod
    def _select_messages(
        history: list[dict[str, Any]], th: CompactionThresholds
    ) -> list[dict[str, Any]]:
        """Messages anciens à résumer (les récents + prioritaires restent)."""
        if len(history) <= th.keep_recent:
            return []
        candidates = history[:-th.keep_recent]
        target = max(1, int(len(candidates) * th.summarize_fraction))
        return candidates[:target]

    async def compact(
        self,
        *,
        history: list[dict[str, Any]],
        model_context_length: int,
        strategy: CompactionStrategy | str = CompactionStrategy.BALANCED,
        attached_context: str = "",
        provider_id: str | None = None,
        model: str | None = None,
    ) -> CompactionResult:
        """Compacter l'historique si nécessaire.

        Résume les messages anciens via le provider actif en préservant les
        éléments critiques ; les messages récents restent en clair.
        """
        from core.llm.types import ChatMessage as LLMChatMessage

        should, estimated, th = self.should_compact(
            history=history,
            model_context_length=model_context_length,
            strategy=strategy,
            attached_context=attached_context,
        )
        result = CompactionResult(
            strategy=strategy.value if isinstance(strategy, CompactionStrategy) else str(strategy),
            estimated_tokens_before=estimated,
        )
        if not should:
            result.estimated_tokens_after = estimated
            return result

        to_summarize = self._select_messages(history, th)
        if not to_summarize:
            result.estimated_tokens_after = estimated
            return result

        # Les éléments prioritaires restent cités en clair dans le résumé.
        priority_lines = [
            f"- {m.get('role', '?')}: {str(m.get('content') or '')[:200]}"
            for m in to_summarize
            if any(marker in str(m.get("content") or "") for marker in _PRIORITY_MARKERS)
        ]

        transcript = "\n".join(
            f"[{m.get('role', '?')}] {str(m.get('content') or '')[:1500]}"
            for m in to_summarize
        )
        summary_instruction = (
            "Résume fidèlement la conversation suivante pour libérer du contexte. "
            "Préserve en priorité : instructions système, mode actif, exigences "
            "utilisateur, tâche en cours, décisions importantes, fichiers en "
            "cours de modification, erreurs pertinentes, état des outils, "
            "actions en attente.  Sois dense et factuel.\n\n" + transcript
        )

        if self._manager is None:
            # Fallback extraction : jamais de perte silencieuse — on garde
            # le transcript prioritaire comme résumé de secours.
            summary = "[Résumé de secours (provider indisponible)]\n" + "\n".join(
                priority_lines or transcript.splitlines()[:20]
            )
        else:
            try:
                from core.llm.types import LLMRequirements

                requirements = LLMRequirements(
                    task_type="summarize",
                    preferred_providers=[provider_id] if provider_id else [],
                )
                response = await self._manager.chat(
                    [LLMChatMessage(role="user", content=summary_instruction)],
                    requirements,
                )
                summary = f"[Compaction {result.strategy}]\n{response.content}"
            except Exception as exc:
                logger.warning("Compaction summary failed: %s", exc)
                summary = "[Résumé de secours (provider indisponible)]\n" + "\n".join(
                    priority_lines or transcript.splitlines()[:20]
                )

        if priority_lines:
            summary += "\n[Éléments préservés en clair]\n" + "\n".join(priority_lines)

        summarized_message = {
            "role": "system",
            "content": summary,
            "metadata": {"compacted": True, "strategy": result.strategy,
                         "summarized": len(to_summarize)},
        }
        kept_recent = history[-th.keep_recent:]
        new_history = [summarized_message, *kept_recent]

        result.compacted = True
        result.summarized_messages = len(to_summarize)
        result.summary = summary
        result.estimated_tokens_after = self.estimate_history_tokens(new_history, attached_context)
        result.new_history = new_history  # type: ignore[attr-defined]
        return result


__all__ = [
    "AutoCompactManager",
    "CompactionResult",
    "CompactionThresholds",
    "STRATEGY_THRESHOLDS",
    "estimate_tokens",
]
