#!/usr/bin/env python3
"""ETHAN CLI — REPL loop."""

import sys
import os
import json
import readline
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from interfaces.cli.client import RuntimeClient
from interfaces.cli.session import SessionManager, Session
from interfaces.cli.ui.prompt import get_prompt
from interfaces.cli.ui.renderer import render_user_message, render_assistant_message, render_error
from interfaces.cli.commands.parser import parse_command, COMMANDS


def repl_loop():
    """Main REPL loop."""
    # Initialize components
    client = RuntimeClient()
    session_manager = SessionManager()
    session = session_manager.create()
    
    # Welcome banner
    print_welcome(session)
    
    # Main loop
    while True:
        try:
            # Read input
            user_input = input(get_prompt(session)).strip()
            
            # Empty input
            if not user_input:
                continue
            
            # Command
            if user_input.startswith("/"):
                handle_command(user_input, session, client, session_manager)
                continue
            
            # Message
            handle_message(user_input, session, client, session_manager)
            
        except KeyboardInterrupt:
            print("\n✗ Interrupted")
            break
        except EOFError:
            print("\n◆ Goodbye")
            break


def print_welcome(session: Session):
    """Print welcome banner."""
    print()
    print("◆ ETHAN Chat")
    print(f"  Session: {session.id[:8]}")
    print()
    print("  /help for commands")
    print()


def handle_command(input_str: str, session: Session, client: RuntimeClient, session_manager: SessionManager):
    """Handle slash commands."""
    cmd, args = parse_command(input_str)
    
    handler = COMMANDS.get(cmd)
    if handler:
        handler(args, session, client, session_manager)
    else:
        render_error(f"Unknown command: {cmd}", "Try: /help")


def handle_message(content: str, session: Session, client: RuntimeClient, session_manager: SessionManager):
    """Handle user message."""
    # Save user message
    session.add_message("user", content)
    
    # Display user message
    render_user_message(content)
    
    # Send to Runtime
    request = {
        "type": "message.send",
        "session_id": session.id,
        "content": content,
        "stream": True
    }
    
    try:
        # Stream response
        full_response = ""
        print("Assistant:")
        
        for chunk in client.stream(request):
            if chunk.get("done"):
                # Final chunk with metadata
                metadata = chunk.get("metadata", {})
                print()  # Newline
                print_status(metadata)
                full_response = chunk.get("content", full_response)
                break
            
            # Print chunk
            text = chunk.get("content", "")
            print(text, end="", flush=True)
            full_response += text
        
        print()  # Newline
        
        # Save assistant message
        session.add_message("assistant", full_response, metadata=metadata if chunk.get("done") else {})
        session_manager.save(session)
        
    except Exception as e:
        render_error("Failed to send message", str(e))


def print_status(metadata: dict):
    """Print status line after response."""
    parts = []
    
    if "duration_ms" in metadata:
        duration = metadata["duration_ms"] / 1000
        parts.append(f"⏱ {duration:.1f}s")
    
    if "tokens" in metadata:
        parts.append(f"Tokens: {metadata['tokens']}")
    
    if "model" in metadata:
        parts.append(f"Model: {metadata['model']}")
    
    if parts:
        print(f"  {' │ '.join(parts)}")


if __name__ == "__main__":
    repl_loop()