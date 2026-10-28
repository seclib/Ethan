"""Normalisation des sessions archivées en Markdown."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from core.knowledge.agent_traces.types import (
    ArchivedMessage,
    ArchivedSession,
    MessageType,
    filter_secrets,
)


def _format_timestamp(ts: datetime | None) -> str:
    if ts is None:
        return "N/A"
    return ts.strftime("%Y-%m-%d %H:%M:%S UTC")


def _escape_yaml(value: str) -> str:
    if any(c in value for c in ":{}\n\"'"):
        return f'"{value}"'
    return value


def session_to_markdown(session: ArchivedSession) -> str:
    """Convertit une session archivée en Markdown avec frontmatter YAML."""
    lines = []

    # Frontmatter YAML
    lines.append("---")
    lines.append(f'id: "{session.session_id}"')
    lines.append(f'agent: "{session.agent.value}"')
    lines.append(f'agent_version: "{session.agent_version}"')
    lines.append(f'session_type: "{session.session_type}"')
    lines.append(f'created_at: "{session.created_at.isoformat() if session.created_at else ""}"')
    lines.append(f'updated_at: "{session.updated_at.isoformat() if session.updated_at else ""}"')
    lines.append(f'model: "{session.model}"')
    lines.append(f'model_provider: "{session.model_provider}"')
    lines.append(f'mode: "{session.mode}"')
    lines.append(f'cwd: "{session.cwd}"')
    lines.append(f'tokens_in: {session.tokens_in}')
    lines.append(f'tokens_out: {session.tokens_out}')
    lines.append(f'total_cost: {session.total_cost}')
    lines.append(f'files_in_context: {session.files_in_context}')
    lines.append(f'status: "{session.status.value}"')
    lines.append(f'checksum: "{session.checksum}"')
    lines.append(f'raw_source: "{session.raw_source}"')
    lines.append("---")
    lines.append("")

    # Titre
    title = session.metadata.get("thread_name", "")
    if not title and session.messages:
        first_user = next((m for m in session.messages if m.role == "user"), None)
        if first_user:
            title, _ = filter_secrets(first_user.content[:80].replace("\n", " "))
    if not title:
        title = f"Session {session.session_id}"
    lines.append(f"# {title}")
    lines.append("")

    # Résumé
    lines.append("## Résumé")
    lines.append("")
    lines.append(f"- **Agent** : {session.agent.value} (v{session.agent_version})")
    lines.append(f"- **Modèle** : {session.model} ({session.model_provider})")
    lines.append(f"- **Mode** : {session.mode or 'N/A'}")
    lines.append(f"- **Statut** : {session.status.value}")
    lines.append(f"- **Messages** : {len(session.messages)}")
    lines.append(f"- **Fichiers en contexte** : {session.files_in_context}")
    lines.append(f"- **Répertoire de travail** : {session.cwd or 'N/A'}")
    lines.append("")

    # Conversation
    lines.append("## Conversation")
    lines.append("")

    for i, msg in enumerate(session.messages, 1):
        ts_str = _format_timestamp(msg.timestamp)
        lines.append(f"### Tour {i} — {msg.role.capitalize()}")
        lines.append("")
        lines.append(f"*{ts_str}*")
        lines.append("")

        content, detected = filter_secrets(msg.content)
        lines.append(content)
        lines.append("")

        if detected:
            lines.append(f"> ⚠️ Secrets filtrés : {', '.join(detected)}")
            lines.append("")

        if msg.message_type == MessageType.TOOL_CALL:
            lines.append("**Outil appelé** :")
            lines.append(f"- Nom : `{msg.tool_name}`")
            if msg.tool_args:
                args_str = str(msg.tool_args)[:500]
                args_str, _ = filter_secrets(args_str)
                lines.append(f"- Arguments : `{args_str}`")
            lines.append("")

        if msg.message_type == MessageType.TOOL_RESULT:
            lines.append("**Résultat de l'outil** :")
            result = msg.tool_result or msg.content
            result, _ = filter_secrets(result)
            lines.append(f"```\n{result[:2000]}\n```")
            lines.append("")

        if msg.message_type == MessageType.CHECKPOINT:
            lines.append("> 📌 Checkpoint créé")
            lines.append("")

        if msg.message_type == MessageType.COMPACTION:
            lines.append("> 📦 Conversation compactée (résumé)")
            lines.append("")

    # Fichiers modifiés
    if session.files_modified:
        lines.append("## Fichiers en contexte")
        lines.append("")
        lines.append("| Fichier | État | Source |")
        lines.append("|---------|------|--------|")
        for f in session.files_modified:
            lines.append(f"| {f.get('path', '')} | {f.get('state', '')} | {f.get('source', '')} |")
        lines.append("")

    # Métadonnées techniques
    lines.append("## Métadonnées techniques")
    lines.append("")
    lines.append(f"- **Tokens entrée** : {session.tokens_in}")
    lines.append(f"- **Tokens sortie** : {session.tokens_out}")
    lines.append(f"- **Coût total** : ${session.total_cost:.4f}")
    lines.append(f"- **Checksum** : `{session.checksum}`")
    lines.append(f"- **Source brute** : `{session.raw_source}`")
    lines.append("")

    return "\n".join(lines)
