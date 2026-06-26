#!/usr/bin/env python3
"""ETHAN CLI — Session management."""

import json
import os
import uuid
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any

SESSIONS_DIR = os.path.expanduser("~/.local/share/ethan/sessions")


@dataclass
class Session:
    """Session data model."""
    id: str
    created_at: str
    last_active: str
    history: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None):
        """Add message to history."""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        if metadata:
            message["metadata"] = metadata
        
        self.history.append(message)
        self.last_active = message["timestamp"]


class SessionManager:
    """Manage CLI sessions."""
    
    def __init__(self):
        self.sessions_dir = SESSIONS_DIR
        os.makedirs(self.sessions_dir, exist_ok=True)
    
    def create(self) -> Session:
        """Create new session."""
        session_id = str(uuid.uuid4())[:8]
        now = datetime.utcnow().isoformat() + "Z"
        
        session = Session(
            id=session_id,
            created_at=now,
            last_active=now,
            history=[],
            metadata={}
        )
        
        self.save(session)
        return session
    
    def load(self, session_id: str) -> Session:
        """Load existing session."""
        path = self._get_path(session_id)
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
                return Session(**data)
        return self.create()
    
    def save(self, session: Session):
        """Save session to disk."""
        path = self._get_path(session.id)
        with open(path, "w") as f:
            json.dump(asdict(session), f, indent=2)
    
    def list_recent(self, limit: int = 10) -> List[Session]:
        """List recent sessions."""
        sessions = []
        if not os.path.exists(self.sessions_dir):
            return sessions
        
        files = sorted(os.listdir(self.sessions_dir), reverse=True)[:limit]
        for file in files:
            path = os.path.join(self.sessions_dir, file)
            with open(path) as f:
                sessions.append(Session(**json.load(f)))
        
        return sessions
    
    def _get_path(self, session_id: str) -> str:
        """Get file path for session."""
        return os.path.join(self.sessions_dir, f"{session_id}.json")