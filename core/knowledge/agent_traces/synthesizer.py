"""Moteur de synthèse pour la transformation des logs en connaissances techniques."""

from __future__ import annotations
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

from core.knowledge.agent_traces.sync_engine import SyncEngine
from core.knowledge.agent_traces.types import ArchivedSession

class TechnicalSynthesizer:
    def __init__(self, knowledge_root: Path):
        self.knowledge_root = knowledge_root
        self.decisions_dir = knowledge_root / "05-Decisions"
        self.knowledge_dir = knowledge_root / "03-Connaissances-Verifiees"

        self.decisions_dir.mkdir(parents=True, exist_ok=True)
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)

    def extract_decisions(self, session: ArchivedSession) -> list[dict[str, str]]:
        """
        Analyse une session pour identifier des décisions d'architecture ou techniques.
        Recherche des patterns de conclusion et de validation.
        """
        decisions = []
        content = ""

        # On simule la reconstruction du contenu pour l'analyse
        for msg in session.messages:
            content += f"\n{msg.role}: {msg.content}"

        # Patterns simples de détection de décision
        patterns = [
            r"(?i)j'ai décidé de\s+([^.\n]+)",
            r"(?i)la solution retenue est\s+([^.\n]+)",
            r"(?i)nous allons utiliser\s+([^.\n]+)",
            r"(?i)validation de l'architecture\s+([^.\n]+)",
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                decisions.append({
                    "decision": match.group(0),
                    "context": match.group(1) if len(match.groups()) > 0 else "",
                    "session_id": session.session_id
                })

        return decisions

    def promote_to_knowledge(self, session: ArchivedSession, topic: str, content: str):
        """
        Transforme un résultat vérifié en document de connaissance.
        """
        safe_topic = re.sub(r'[^\w\s-]', '', topic).strip().replace(' ', '_')
        file_path = self.knowledge_dir / f"{safe_topic}.md"

        markdown = f"""---
topic: {topic}
source_session: {session.session_id}
verified_at: {datetime.now(timezone.utc).isoformat()}
status: verified
---

# {topic}

{content}

---
**Source** : [Session {session.session_id}](01-Archives/{session.agent.value}/{session.created_at.strftime('%Y-%m-%d') if session.created_at else 'unknown'}/{session.session_id}.md)
"""
        file_path.write_text(markdown, encoding="utf-8")
        return file_path

    def process_archives(self, sync_engine: SyncEngine):
        """
        Parcourt toutes les sessions synchronisées pour extraire des synthèses.
        """
        sync_state = sync_engine._load_sync_state()
        sessions_data = sync_state.get("sessions", {})

        # Note: In a real scenario, we would reload the ArchivedSession object
        # from the markdown or raw source. Here we focus on the logic.
        print(f"Analyse de {len(sessions_data)} sessions pour synthèse...")
        # Implementation would iterate sessions and call extract_decisions
