#!/usr/bin/env python3
"""ETHAN CLI — Command parser."""

from typing import Tuple


def parse_command(input_str: str) -> Tuple[str, str]:
    """Parse command string.
    
    Returns:
        (command, args)
    """
    parts = input_str.split(maxsplit=1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    return cmd, args


# Command registry
COMMANDS = {}


def register_command(name: str):
    """Decorator to register command handler."""
    def decorator(func):
        COMMANDS[name] = func
        return func
    return decorator