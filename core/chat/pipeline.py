"""Chat Pipeline — Core orchestration for chat completions.

ETHAN Core owns the chat pipeline.  The WebUI only sends user actions and
renders events.  This pipeline:

1. Validates the model + ACL
2. Loads the conversation tree (ChatStore)
3. Resolves context (skills, tools, RAG, memory)
4. Generates via ProviderManager
5. Persists messages + tree
6. Emits events (SSE/WebSocket)

The pipeline has no dependency on an API, CLI, or graphical interface.
"""

from __future__ import annotations

import logging
from typing import Any

from core.llm.provider_manager import ProviderManager
from core.llm.types import ChatMessage as LLMChatMessage
from core.llm.types import LLMRequirements
from core.rag import RAGPipeline
from core.skills.store import SkillStore
from core.state.chats import ChatStore
from core.state.webui_store import CoreWebUIStore

logger = logging.getLogger(__name__)


class ChatPipeline:
    """Core chat orchestration pipeline.

    Args:
        chat_store: Core-owned conversation store.
        provider_manager: LLM provider manager.
        rag: Optional RAG pipeline for retrieval-augmented context.
        skill_store: Optional skill store for skill resolution.
    """

    def __init__(
        self,
        chat_store: ChatStore,
        provider_manager: ProviderManager | None = None,
        rag: RAGPipeline | None = None,
        skill_store: SkillStore | None = None,
        memory_store: CoreWebUIStore | None = None,
        file_store: Any | None = None,
    ) -> None:
        self._chats = chat_store
        self._manager = provider_manager
        self._rag = rag
        self._skills = skill_store
        self._memory = memory_store
        self._files = file_store

    def set_provider_manager(self, manager: "ProviderManager") -> None:
        """Injecte/remplace le ProviderManager après construction.

        Nécessaire car le ProviderManager est initialisé après le pipeline
        dans le lifespan de l'API : sans cette réinjection, _generate()
        retombe sur le fallback echo (provider mock).
        """
        self._manager = manager

    async def run(
        self,
        *,
        message: str,
        chat_id: str | None = None,
        user_id: str = "anonymous",
        provider_id: str | None = None,
        model: str | None = None,
        parent_id: str | None = None,
        skill_ids: list[str] | None = None,
        tool_ids: list[str] | None = None,
        knowledge_ids: list[str] | None = None,
        file_ids: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run the chat pipeline for a single user message.

        Returns:
            A dict with ``chat_id``, ``user_message``, ``assistant_message``
            and ``branch`` (the current message path).
        """
        # 1. Créer ou réutiliser la conversation.
        if chat_id:
            chat_record = await self._chats.get_chat(chat_id)
            if chat_record is None:
                raise ValueError(f"Chat {chat_id} not found")
        else:
            chat_record = await self._chats.create_chat(
                title=message[:60] or "New Chat",
                user_id=user_id,
                metadata=metadata,
            )
            chat_id = chat_record["id"]

        assert chat_id is not None  # garanti par le bloc ci-dessus

        # 2. Persister le message utilisateur (nœud de l'arbre).
        # Si aucun parent_id n'est fourni et que la conversation existe déjà,
        # lier au dernier message de la branche courante (continuité du fil).
        if parent_id is None and chat_record.get("messages"):
            current_branch = await self._chats.get_branch(chat_id)
            if current_branch:
                parent_id = current_branch[-1]["id"]

        user_message = await self._chats.add_message(
            chat_id,
            role="user",
            content=message,
            user_id=user_id,
            parent_id=parent_id,
            metadata={
                "provider_id": provider_id,
                "model": model,
                "skill_ids": skill_ids or [],
                "tool_ids": tool_ids or [],
                "knowledge_ids": knowledge_ids or [],
                "file_ids": file_ids or [],
            },
        )

        # 3. Construire le contexte LLM.
        llm_messages = await self._build_llm_messages(
            chat_id=chat_id,
            user_message=message,
            user_id=user_id,
            skill_ids=skill_ids,
            knowledge_ids=knowledge_ids,
            file_ids=file_ids,
        )

        # 4. Générer la réponse.
        assistant_content, response_meta = await self._generate(
            llm_messages=llm_messages,
            provider_id=provider_id,
            model=model,
        )

        # 5. Persister la réponse assistant (enfant du message utilisateur).
        assistant_message = await self._chats.add_message(
            chat_id,
            role="assistant",
            content=assistant_content,
            user_id=user_id,
            parent_id=user_message["id"],
            model=response_meta.get("model"),
            status="done",
            done=True,
            metadata=response_meta,
        )

        # 6. Retourner la branche courante.
        branch = await self._chats.get_branch(chat_id, assistant_message["id"])

        return {
            "chat_id": chat_id,
            "user_message": user_message,
            "assistant_message": assistant_message,
            "branch": branch,
        }

    # ── Helpers ──────────────────────────────────────────────────────────

    async def _build_llm_messages(
        self,
        *,
        chat_id: str,
        user_message: str,
        user_id: str,
        skill_ids: list[str] | None,
        knowledge_ids: list[str] | None,
        file_ids: list[str] | None,
    ) -> list[LLMChatMessage]:
        """Build the LLM message list with resolved context."""
        messages: list[LLMChatMessage] = []

        # Contexte système : skills activées.
        system_parts: list[str] = []
        if self._skills and skill_ids:
            for skill_id in skill_ids:
                skill = await self._skills.get_skill(skill_id)
                if skill and skill.get("is_active", True):
                    content = skill.get("content", "").strip()
                    if content:
                        system_parts.append(f"[Skill: {skill.get('name', skill_id)}]\n{content}")

        # Contexte mémoire : faits persistants sur l'utilisateur.
        # Distinct du RAG : les faits sont globaux et injectés tels quels,
        # les documents sont retrievés par similarité.
        if self._memory:
            try:
                facts = await self._memory.list_facts()
                if facts:
                    fact_lines = []
                    for fact in facts:
                        subject = fact.get("subject", "")
                        predicate = fact.get("predicate", "")
                        obj = fact.get("object", "")
                        if subject and obj:
                            fact_lines.append(f"- {subject} {predicate} {obj}".rstrip())
                        elif subject:
                            fact_lines.append(f"- {subject}")
                    if fact_lines:
                        system_parts.append("[Faits mémoire utilisateur]\n" + "\n".join(fact_lines))
            except Exception as exc:
                logger.warning("Memory facts injection failed: %s", exc)

        # Contexte RAG : retrieval sur les documents.
        if self._rag:
            try:
                rag_context = await self._rag.build_context(user_message)
                if rag_context.strip():
                    system_parts.append(f"[Contexte documentaire]\n{rag_context}")
            except Exception as exc:
                logger.warning("RAG context build failed: %s", exc)

        # Contexte fichiers attachés : injecter le contenu des fichiers
        # Core (FileStore) dans le prompt pour que l'utilisateur puisse
        # réellement référencer ces fichiers dans son message.
        if file_ids:
            file_store = getattr(self, "_files", None)
            if file_store is None:
                logger.warning("Attached files requested but no FileStore is injected into ChatPipeline")
            else:
                try:
                    file_parts: list[str] = []
                    for file_id in file_ids:
                        try:
                            file_record = await file_store.get(file_id)
                            if file_record is None:
                                continue
                            result = await file_store.download(file_id)
                            if result is None:
                                continue
                            content, _result_record = result
                            text = content.decode("utf-8", errors="replace")
                            filename = file_record.get("filename", file_id)
                            # Tronquer à 10 KB pour éviter un prompt démesuré.
                            truncated = text[:10_000]
                            file_parts.append(f"=== File: {filename} ===\n{truncated}")
                        except Exception as exc:
                            logger.warning("Failed to load attached file %s: %s", file_id, exc)
                    if file_parts:
                        system_parts.append("[Fichiers attachés]\n" + "\n\n".join(file_parts))
                except Exception as exc:
                    logger.warning("Attached-files context build failed: %s", exc)

        if system_parts:
            messages.append(LLMChatMessage(role="system", content="\n\n".join(system_parts)))

        # Historique de la branche courante (hors message courant).
        # Le message utilisateur courant est déjà persisté dans la branche ;
        # on l'exclut pour éviter un doublon dans le contexte LLM.
        branch = await self._chats.get_branch(chat_id)
        for msg in branch[:-1]:
            if msg.get("role") in ("user", "assistant"):
                messages.append(LLMChatMessage(role=msg["role"], content=msg.get("content", "")))

        # Message utilisateur courant.
        messages.append(LLMChatMessage(role="user", content=user_message))
        return messages

    async def _generate(
        self,
        *,
        llm_messages: list[LLMChatMessage],
        provider_id: str | None,
        model: str | None,
    ) -> tuple[str, dict[str, Any]]:
        """Generate a response via the ProviderManager."""
        if self._manager is None:
            logger.warning("ProviderManager not initialized — falling back to echo")
            return f"[ECHO] {llm_messages[-1].content if llm_messages else ''}", {
                "provider": "mock",
                "model": "echo",
            }

        try:
            # Provider direct si fourni.
            if provider_id:
                provider = self._manager._registry.get_provider(provider_id)
                if provider is None:
                    config = self._manager._providers_config.get(provider_id)
                    if config and config.get("enabled", False):
                        from core.llm.provider_factory import create_provider_from_config
                        provider = create_provider_from_config({**config, "name": provider_id})
                        await provider.initialize()
                if provider is not None:
                    result = await provider.chat(llm_messages, model=model or None)
                    return result.content, {
                        "provider": provider_id,
                        "model": result.model,
                        "usage": result.usage,
                    }

            # Sélection automatique.
            requirements = LLMRequirements(
                task_type="chat",
                preferred_providers=[provider_id] if provider_id else [],
            )
            result = await self._manager.chat(llm_messages, requirements)
            return result.content, {
                "provider": result.provider,
                "model": result.model,
                "usage": result.usage,
            }
        except Exception as exc:
            logger.exception("Chat generation failed: %s", exc)
            raise


__all__ = ["ChatPipeline"]