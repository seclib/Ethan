"""Agent executor — Adapter d'exécution Core pour les agents.

Cette logique appartient au Core : elle résout le provider LLM et le modèle
de l'agent, construit le prompt (description + skills + contexte) et appelle
le ProviderManager réel. Aucun mock : sans provider capable, l'exécution
échoue proprement.

Sécurité (Constitution CT-4 — séparation données/instructions) : les skills
et le contexte RAG injectés dans le prompt sont des **données récupérées**,
jamais des instructions. Leur contenu est sanitisé (blocs `<system>` /
`<instruction>` / `system:` retirés) puis enclos dans des balises `<data>`
avec provenance et instructions sticky via ``core.security.prompt_guard``.

L'injection se fait dans la composition root (interfaces/api/main.py) après
initialisation du ProviderManager.
"""

from __future__ import annotations

import logging
from typing import Any

from core.agents.resources import resolve_agent_resources
from core.agents.types import Agent
from core.llm.types import ChatMessage
from core.security.prompt_guard import (
    sanitize_external_content,
    wrap_data_block,
)

logger = logging.getLogger(__name__)


class _NoOpSkillStore:
    """Placeholder sans effet si aucun skill store n'est fourni."""

    async def get_skill(self, skill_id: str) -> dict[str, Any] | None:
        return None


async def _resolve_provider(
    provider_manager: Any, provider_id: str | None
) -> Any | None:
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


class _NoOpKnowledgeCollections:
    """Placeholder sans effet si aucun collection manager n'est fourni."""

    async def build_context_multi(
        self, query: str, collection_ids: list[str], *, top_k: int | None = None
    ) -> str:
        return ""


def create_agent_executor(
    provider_manager: Any,
    skill_store: Any | None = None,
    knowledge_collections: Any | None = None,
    domain_manager: Any | None = None,
    folders: Any | None = None,
    knowledge_manager: Any | None = None,
    tools: Any | None = None,
) -> Any:
    """Fabrique l'exécuteur d'agents lié au runtime.

    Retourne un callable asynchrone compatible avec AgentManager.executor :
    ``(agent, task, context, skill_id) -> str``.

    Args:
        provider_manager: Instance du ProviderManager Core (LLM).
        skill_store: Store Core des skills (optionnel) — permet d'injecter
            le contenu des skills assignés dans le prompt de l'agent.
        knowledge_collections: KnowledgeCollectionManager Core (optionnel) —
            permet de scopier le RAG sur les collections de connaissances
            assignées à l'agent (``agent.knowledge_collection_ids``).
        domain_manager: DomainManager Core (optionnel) — résout les
            ressources (skills, collections RAG) rattachées aux domains
            sélectionnés explicitement par l'agent (``agent.domain_ids``).
        folders: FolderManager Core (optionnel) — résout les contenus des
            dossiers sélectionnés par l'agent (``agent.folder_ids``) :
            sélectionner un dossier inclut les ressources qu'il contient.
        knowledge_manager: KnowledgeManager Core (optionnel) — injecte le
            contenu des nœuds de Knowledge spécifiquement autorisés
            (``agent.knowledge_ids``) comme données sanitizées.
        tools: ToolManager Core (optionnel) — n'expose au runtime QUE les
            tools/MCP autorisés (``agent.tool_ids`` + ceux des dossiers).

    La résolution effective (déduplication, sources, fantômes) est déléguée à
    ``core.agents.resources.resolve_agent_resources`` : aucune ressource
    globale n'est injectée sans décision explicite de l'utilisateur.
    """
    skills = skill_store or _NoOpSkillStore()
    knowledge = knowledge_collections or _NoOpKnowledgeCollections()

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

        # ── Résolution des ressources effectives ───────────────────────
        # Le résolveur Core fusionne la sélection explicite et les contenus
        # des dossiers sélectionnés, déduplique par identité, trace la
        # source et ignore les ressources disparues : le runtime ne reçoit
        # QUE les ressources autorisées — jamais le catalogue global.
        resolved = await resolve_agent_resources(
            agent,
            folders=folders,
            knowledge=knowledge_manager,
            collections=knowledge_collections,
            skills=skills,
            tools=tools,
        )
        folder_skill_ids = [
            s["id"] for s in resolved["skills"] if s["source"] != "explicit"
        ]
        folder_collection_ids = [
            c["id"] for c in resolved["collections"] if c["source"] != "explicit"
        ]
        allowed_knowledge = resolved["knowledge"]
        allowed_tools = resolved["tools"]

        # Skills assignés (tous, ou uniquement celui demandé via skill_id).
        # Les skills rattachés aux domains sélectionnés par l'agent sont
        # résolus par le Core via le DomainManager : l'agent ne peut
        # s'auto-attribuer des ressources, seules les memberships Core
        # (domain_ids validés à la création) font foi.
        # Sécurité (CT-4 — séparation données/instructions) : le contenu du
        # skill est sanitisé puis enclos dans un bloc <data> avec provenance.
        # Il reste des DONNÉES, jamais des instructions.
        domain_skill_ids: list[str] = []
        domain_collection_ids: list[str] = []
        for domain_id in list(getattr(agent, "domain_ids", None) or []):
            if domain_manager is None:
                logger.warning(
                    "Agent %s declares domain %s but no DomainManager is wired "
                    "— domain resources are ignored",
                    agent.name,
                    domain_id,
                )
                continue
            try:
                memberships = await domain_manager.list_resource_ids(domain_id)
            except Exception as exc:
                logger.warning(
                    "Failed to resolve domain %s for agent %s: %s",
                    domain_id,
                    agent.name,
                    exc,
                )
                continue
            for membership in memberships:
                rtype = membership.get("resource_type")
                rid = membership.get("resource_id")
                if rtype == "collection":
                    domain_collection_ids.append(rid)
                elif rtype == "skill":
                    domain_skill_ids.append(rid)

        skill_ids = [skill_id] if skill_id else list(
            dict.fromkeys(
                [*(agent.skill_ids or []), *folder_skill_ids, *domain_skill_ids]
            )
        )
        for sid in skill_ids:
            try:
                skill = await skills.get_skill(sid)
                if skill and skill.get("is_active", True):
                    content = skill.get("content", "").strip()
                    if content:
                        safe = sanitize_external_content(content)
                        system_parts.append(
                            wrap_data_block(
                                safe,
                                source=f"skill:{sid}",
                                kind="skill",
                                header=f"[Skill: {skill.get('name', sid)}]",
                            )
                        )
            except Exception as exc:
                logger.warning("Failed to load skill %s: %s", sid, exc)

        # Knowledge spécifique : le contenu des nœuds autorisés est injecté
        # comme DONNÉES récupérées (CT-4 : sanitization + balise <data>) —
        # jamais des instructions. Aucun nœud non autorisé n'est consulté.
        for item in allowed_knowledge:
            if knowledge_manager is None:
                logger.warning(
                    "Agent %s declares knowledge %s but no KnowledgeManager is "
                    "wired — knowledge content is ignored",
                    agent.name,
                    item["id"],
                )
                continue
            try:
                node = await knowledge_manager.get(item["id"])
            except Exception as exc:
                logger.warning(
                    "Failed to load knowledge %s for agent %s: %s",
                    item["id"], agent.name, exc,
                )
                continue
            record = node.to_dict() if node is not None and hasattr(node, "to_dict") else node
            content = ""
            if isinstance(record, dict):
                content = str(record.get("content", "") or "")
            if content.strip():
                safe = sanitize_external_content(content)
                system_parts.append(
                    wrap_data_block(
                        safe,
                        source=f"knowledge:{item['id']}",
                        kind="knowledge",
                        header=f"[Knowledge: {item.get('name', item['id'])}]",
                    )
                )

        # Connaissances : le RAG est scopé sur les collections assignées à
        # l'agent (knowledge_collection_ids) augmentées des collections
        # issues de ses dossiers et de ses domains.  Une collection
        # indisponible ne bloque pas l'exécution — elle est simplement
        # ignorée (warning).
        knowledge_ids = list(
            dict.fromkeys(
                [
                    *(getattr(agent, "knowledge_collection_ids", None) or []),
                    *folder_collection_ids,
                    *domain_collection_ids,
                ]
            )
        )
        if knowledge_ids:
            try:
                rag_context = await knowledge.build_context_multi(
                    task, knowledge_ids
                )
            except Exception as exc:
                logger.warning(
                    "Failed to build RAG context for agent %s: %s",
                    agent.name,
                    exc,
                )
                rag_context = ""
            if rag_context:
                # CT-4 : le contexte RAG est des données récupérées — jamais
                # des instructions. Sanitization + balise <data> + provenance.
                safe_context = sanitize_external_content(rag_context)
                system_parts.append(
                    wrap_data_block(
                        safe_context,
                        source="rag:" + ",".join(knowledge_ids),
                        kind="rag",
                        header="[Connaissances]",
                    )
                )

        # Tools / MCP : le runtime ne reçoit que la liste des outils
        # explicitement autorisés (sélection directe ou via dossiers).
        # Aucun tool global n'est exposé par défaut.
        if allowed_tools:
            tool_lines = "\n".join(
                f"- {t['name']} ({t.get('provider') or 'tool'})"
                for t in allowed_tools
            )
            system_parts.append(
                "Outils autorisés — le runtime n'expose QUE ces tools/MCP :\n"
                + tool_lines
            )

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
