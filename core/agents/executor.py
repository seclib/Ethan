"""Agent executor — Adapter d'exécution Core pour les agents.

Cette logique appartient au Core : elle résout le provider LLM et le modèle
de l'agent, construit le prompt (description + skills + contexte) et appelle
le ProviderManager réel. Aucun mock : sans provider capable, l'exécution
échoue proprement.

L'injection se fait dans la composition root (interfaces/api/main.py) après
initialisation du ProviderManager.
"""

from __future__ import annotations

import logging
from typing import Any

from core.agents.types import Agent
from core.llm.types import ChatMessage

logger = logging.getLogger(__name__)


class _NoOpSkillStore:
    """Placeholder sans effet si aucun skill store n'est fourni."""

    async def get_skill(self, skill_id: str) -> dict[str, Any] | None:
        return None


async def _resolve_provider(provider_manager: Any, provider_id: str | None) -> Any | None:
    """Résout une instance de provider depuis le ProviderManager.

    Réutilise le registry s'il existe, sinon instancie depuis la config
    persistée (sans exiger qu'il soit déjà initialisé).
    """
    if provider_id is None:
        return None
    provider = provider_manager._registry.get_provider(provider_id)
    if provider is not None:
        return provider
    config = provider_manager._providers_config.get(provider_id)
    if config and config.get("enabled", False):
        from core.llm.provider_factory import create_provider_from_config

        provider = create_provider_from_config({**config, "name": provider_id})
        await provider.initialize()
        return provider
    return None


def create_agent_executor(
    provider_manager: Any,
    skill_store: Any | None = None,
) -> Any:
    """Fabrique l'exécuteur d'agents lié au runtime.

    Retourne un callable asynchrone compatible avec AgentManager.executor :
    ``(agent, task, context, skill_id) -> str``.

    Args:
        provider_manager: Instance du ProviderManager Core (LLM).
        skill_store: Store Core des skills (optionnel) — permet d'injecter
            le contenu des skills assignés dans le prompt de l'agent.
    """
    skills = skill_store or _NoOpSkillStore()

    async def execute(
        agent: Agent,
        task: str,
        *,
        context: dict[str, Any] | None = None,
        skill_id: str | None = None,
    ) -> str:
        provider = await _resolve_provider(provider_manager, agent.provider)
        if provider is None:
            raise RuntimeError(
                f"Provider '{agent.provider}' for agent '{agent.name}' "
                "is not available or not enabled"
            )

        model = agent.model or getattr(provider, "default_model", None)
        if not model:
            raise RuntimeError(
                f"No model configured for agent '{agent.name}' and provider "
                f"'{agent.provider}' has no default model"
            )

        # ── Construction du prompt ─────────────────────────────────────
        system_parts: list[str] = []
        if agent.description:
            system_parts.append(f"Tu es l'agent « {agent.name} ».\n{agent.description}")

        # Skills assignés (tous, ou uniquement celui demandé via skill_id).
        skill_ids = [skill_id] if skill_id else list(agent.skill_ids or [])
        for sid in skill_ids:
            try:
                skill = await skills.get_skill(sid)
                if skill and skill.get("is_active", True):
                    content = skill.get("content", "").strip()
                    if content:
                        system_parts.append(f"[Skill: {skill.get('name', sid)}]\n{content}")
            except Exception as exc:
                logger.warning("Failed to load skill %s: %s", sid, exc)

        if agent.capabilities:
            system_parts.append("Capabilities: " + ", ".join(agent.capabilities))

        system_prompt = "\n\n".join(system_parts) or f"Tu es l'agent « {agent.name} »."

        messages = [ChatMessage(role="system", content=system_prompt)]
        if context:
            context_lines = "\n".join(f"- {k}: {v}" for k, v in context.items())
            messages.append(
                ChatMessage(
                    role="user",
                    content=f"[Contexte]\n{context_lines}\n\nTâche : {task}",
                )
            )
        else:
            messages.append(ChatMessage(role="user", content=task))

        response = await provider.chat(messages, model=model, temperature=0.7)
        return response.content

    return execute