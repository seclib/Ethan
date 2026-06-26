#!/usr/bin/env python3
"""ETHAN CLI — Output rendering."""


def render_user_message(content: str):
    """Render user message."""
    print(f"User: {content}")


def render_assistant_message(content: str):
    """Render assistant message header."""
    print("Assistant:")


def render_error(title: str, detail: str = ""):
    """Render error message."""
    print(f"✗ {title}")
    if detail:
        print(f"  → {detail}")


def render_success(message: str):
    """Render success message."""
    print(f"✓ {message}")


def render_info(message: str):
    """Render info message."""
    print(f"ℹ {message}")