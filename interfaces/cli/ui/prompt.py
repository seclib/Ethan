#!/usr/bin/env python3
"""ETHAN CLI — Prompt formatting."""

from interfaces.cli.session import Session


def get_prompt(session: Session) -> str:
    """Get formatted prompt string."""
    # Brand marker
    prompt = "◆ ethan"
    
    # Session ID (truncated)
    session_short = session.id[:8]
    prompt += f" ◇ {session_short}"
    
    # Input cursor
    prompt += " ▸ "
    
    return prompt