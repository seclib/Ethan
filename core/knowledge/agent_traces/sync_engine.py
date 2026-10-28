"""Moteur de synchronisation pour l'archivage des traces d'agents."""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.knowledge.agent_traces.cline_connector import ClineConnector
from core.knowledge.agent_traces.codex_connector import CodexConnector
from core.knowledge.agent_traces.copilot_connector import CopilotConnector
from core.knowledge.agent_traces.normalizer import session_to_markdown
from core.knowledge.agent_traces.types import SessionStatus


class SyncEngine:
    def __init__(self, knowledge_root: Path | None = None):
        self.knowledge_root = knowledge_root or (Path.home() / "AI" / "Ethan" / "Odsidian")
        self.raw_dir = self.knowledge_root / "01-Archives"
        self.sessions_dir = self.knowledge_root / "01-Archives"
        self.index_dir = self.knowledge_root
        self.summaries_dir = self.knowledge_root / "06-Syntheses"
        self.metadata_dir = self.knowledge_root / "_meta"
        self.sync_state_path = self.metadata_dir / "sync-state.json"

        for d in [self.raw_dir, self.sessions_dir, self.index_dir, self.summaries_dir, self.metadata_dir]:
            d.mkdir(parents=True, exist_ok=True)

        self.connectors = {
            "cline": ClineConnector(),
            "codex": CodexConnector(),
            "copilot": CopilotConnector(),
        }

    def _load_sync_state(self) -> dict[str, Any]:
        if self.sync_state_path.exists():
            try:
                with open(self.sync_state_path) as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return {"version": 1, "sessions": {}, "last_sync": None}

    def _save_sync_state(self, state: dict[str, Any]) -> None:
        state["last_sync"] = datetime.now(timezone.utc).isoformat()
        tmp_path = self.sync_state_path.with_suffix(".tmp")
        with open(tmp_path, "w") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, self.sync_state_path)

    def _session_path(self, session) -> Path:
        agent = session.agent.value
        date_str = (session.created_at or datetime.now(timezone.utc)).strftime("%Y-%m-%d")
        return self.sessions_dir / agent / date_str / f"{session.session_id}.md"

    def _is_duplicate(self, session, sync_state: dict[str, Any]) -> bool:
        session_key = f"{session.agent.value}:{session.session_id}"
        if session_key in sync_state.get("sessions", {}):
            stored_checksum = sync_state["sessions"][session_key].get("checksum", "")
            if stored_checksum == session.checksum:
                return True
        return False


    def sync(self, agents=None):
        sync_state = self._load_sync_state()
        results = {
            "collected": 0, "skipped": 0, "errors": 0,
            "duplicates": 0, "ignored": 0, "sessions": [],
        }
        agents_to_sync = agents or list(self.connectors.keys())

        for agent_name in agents_to_sync:
            connector = self.connectors.get(agent_name)
            if not connector or not connector.is_available():
                results["ignored"] += 1
                continue
            try:
                sessions_list = connector.list_sessions()
            except Exception:
                results["errors"] += 1
                continue

            for session_ref in sessions_list:
                try:
                    session = connector.collect_session(session_ref)
                    if session is None:
                        results["errors"] += 1
                        continue
                    if session.status == SessionStatus.SKIPPED:
                        results["ignored"] += 1
                        continue
                    if self._is_duplicate(session, sync_state):
                        results["duplicates"] += 1
                        continue

                    md_content = session_to_markdown(session)
                    md_path = self._session_path(session)
                    md_path.parent.mkdir(parents=True, exist_ok=True)

                    tmp_path = md_path.with_suffix(".tmp")
                    with open(tmp_path, "w", encoding="utf-8") as f:
                        f.write(md_content)
                    if md_path.exists():
                        import shutil
                        shutil.copy2(md_path, md_path.with_suffix(".bak"))
                    import os
                    os.replace(tmp_path, md_path)

                    session_key = f"{session.agent.value}:{session.session_id}"
                    sync_state.setdefault("sessions", {})[session_key] = {
                        "checksum": session.checksum,
                        "path": str(md_path.relative_to(self.knowledge_root)),
                        "synced_at": datetime.now(timezone.utc).isoformat(),
                        "status": session.status.value,
                    }
                    results["collected"] += 1
                    results["sessions"].append({
                        "id": session.session_id,
                        "agent": session.agent.value,
                        "path": str(md_path),
                        "status": session.status.value,
                    })
                except Exception as e:
                    results["errors"] += 1
                    results["sessions"].append({
                        "id": str(session_ref),
                        "agent": agent_name,
                        "error": str(e),
                    })

        self._save_sync_state(sync_state)
        self._generate_index(sync_state, results)
        self.generate_all_summaries()
        return results

    def _generate_index(self, sync_state, results):
        index_path = self.knowledge_root / "INDEX.md"
        lines = []
        lines.append("# ETHAN Knowledge Base — Index")
        lines.append("")
        lines.append(f"*Dernière synchronisation : {sync_state.get('last_sync', 'N/A')}*")
        lines.append("")
        lines.append("## Résumé")
        lines.append("")
        lines.append(f"- **Sessions collectées** : {results['collected']}")
        lines.append(f"- **Doublons ignorés** : {results['duplicates']}")
        lines.append(f"- **Sessions ignorées** : {results['ignored']}")
        lines.append(f"- **Erreurs** : {results['errors']}")
        lines.append("")

        lines.append("## Sessions par agent")
        lines.append("")

        by_agent = {}
        for session_key, info in sync_state.get("sessions", {}).items():
            agent = session_key.split(":")[0]
            by_agent.setdefault(agent, []).append((session_key, info))

        for agent, sessions in sorted(by_agent.items()):
            lines.append(f"### {agent.capitalize()}")
            lines.append("")
            lines.append("| Session ID | Statut | Date sync |")
            lines.append("|------------|--------|-----------|")
            for session_key, info in sessions:
                sid = session_key.split(":", 1)[1]
                lines.append(f"| [{sid}]({info['path']}) | {info['status']} | {info['synced_at'][:10]} |")
            lines.append("")

        lines.append("## Synthèses")
        lines.append("")
        lines.append("- [Synthèse Cline](06-Syntheses/by-agent/cline-summary.md)")
        lines.append("- [Synthèse Codex](06-Syntheses/by-agent/codex-summary.md)")
        lines.append("- [Synthèse Copilot](06-Syntheses/by-agent/copilot-summary.md)")
        lines.append("")

        tmp_path = index_path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        import os
        os.replace(tmp_path, index_path)

    def generate_agent_summary(self, agent_name: str) -> str:
        sync_state = self._load_sync_state()
        sessions = [
            (k, v) for k, v in sync_state.get("sessions", {}).items()
            if k.startswith(f"{agent_name}:")
        ]

        lines = []
        lines.append(f"# Synthèse — {agent_name.capitalize()}")
        lines.append("")
        lines.append(f"*Généré le {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*")
        lines.append("")
        lines.append(f"## Sessions : {len(sessions)}")
        lines.append("")

        for session_key, info in sessions:
            sid = session_key.split(":", 1)[1]
            lines.append(f"- [{sid}]({info['path']}) — {info['status']}")
        lines.append("")

        lines.append("## Sources")
        lines.append("")
        lines.append(f"Toutes les sessions sont archivées dans `01-Archives/{agent_name}/`")
        lines.append(f"Source brute : `01-Archives/{agent_name}/`")
        lines.append("")

        return "\n".join(lines)

    def generate_all_summaries(self) -> None:
        for agent in ["cline", "codex", "copilot"]:
            summary = self.generate_agent_summary(agent)
            summary_path = self.summaries_dir / "by-agent" / f"{agent}-summary.md"
            summary_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = summary_path.with_suffix(".tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(summary)
            import os
            os.replace(tmp_path, summary_path)
