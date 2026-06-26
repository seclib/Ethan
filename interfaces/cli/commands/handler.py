#!/usr/bin/env python3
"""ETHAN CLI — Built-in command handlers."""

import sys
import os
from interfaces.cli.commands.parser import register_command
from interfaces.cli.ui.renderer import render_success, render_error, render_info
from interfaces.cli.session import Session
from interfaces.cli.client import RuntimeClient
from interfaces.cli.session import SessionManager


@register_command("/exit")
@register_command("/quit")
def cmd_exit(args, session: Session, client: RuntimeClient, session_manager: SessionManager):
    """Exit CLI."""
    print("◆ Goodbye")
    sys.exit(0)


@register_command("/clear")
def cmd_clear(args, session: Session, client: RuntimeClient, session_manager: SessionManager):
    """Clear screen."""
    os.system("clear" if os.name == "posix" else "cls")


@register_command("/status")
def cmd_status(args, session: Session, client: RuntimeClient, session_manager: SessionManager):
    """Show Runtime status."""
    try:
        resp = client.send({"type": "status.get"})
        
        if resp.get("status") == "ok":
            data = resp.get("data", {})
            runtime = data.get("runtime", {})
            services = data.get("services", [])
            
            print()
            print("◆ Status")
            print()
            print(f"  Runtime: {runtime.get('state', 'UNKNOWN')}")
            print()
            print("  Services:")
            for svc in services:
                name = svc.get("name", "unknown")
                state = svc.get("state", "unknown")
                health = svc.get("health", "unknown")
                print(f"    {name}: {state} ({health})")
            print()
        else:
            render_error("Failed to get status", resp.get("error", ""))
    
    except Exception as e:
        render_error("Failed to connect to Runtime", str(e))


@register_command("/session")
def cmd_session(args, session: Session, client: RuntimeClient, session_manager: SessionManager):
    """Show session info."""
    print()
    print("◆ Session")
    print()
    print(f"  ID: {session.id}")
    print(f"  Created: {session.created_at}")
    print(f"  Last active: {session.last_active}")
    print(f"  Messages: {len(session.history)}")
    print()


@register_command("/history")
def cmd_history(args, session: Session, client: RuntimeClient, session_manager: SessionManager):
    """Show message history."""
    if not session.history:
        render_info("No messages in history")
        return
    
    print()
    print("◆ History")
    print()
    
    # Show last 10 messages
    for i, msg in enumerate(session.history[-10:], 1):
        role = msg["role"]
        content = msg["content"][:80]
        if len(msg["content"]) > 80:
            content += "..."
        print(f"  {i}. {role}: {content}")
    
    if len(session.history) > 10:
        print(f"  ... and {len(session.history) - 10} more")
    
    print()


@register_command("/help")
def cmd_help(args, session: Session, client: RuntimeClient, session_manager: SessionManager):
    """Show help."""
    print()
    print("◆ Help")
    print()
    print("  Commands:")
    print("    /exit, /quit    Exit CLI")
    print("    /clear          Clear screen")
    print("    /status         Show Runtime status")
    print("    /session        Show session info")
    print("    /history        Show recent messages")
    print("    /help           Show this help")
    print()
    print("  Usage:")
    print("    Just type your message to chat")
    print("    Messages are sent to ETHAN Runtime")
    print()