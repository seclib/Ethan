"""ETHAN help — structured, grouped command help."""

import sys
from interfaces.cli.core import colors as clr
from interfaces.cli.core.discovery import registry


def cmd_help(args):
    """Show ETHAN help."""
    topic = args[0] if args else None
    show_help(topic)
    return 0


def show_help(topic=None):
    if topic:
        show_topic(topic)
    else:
        show_top_level()


def show_top_level():
    print()
    print(f"  {clr.C.BOLD}{clr.C.BLUE}ETHAN — Cognitive Runtime CLI{clr.C.RESET}")
    print()

    # Core
    print(f"  {clr.C.BOLD}Core{clr.C.RESET}")
    for cmd in registry.list_commands("core"):
        print(f"    {clr.C.CYAN}{cmd.name:<10}{clr.C.RESET} {cmd.description}")
    print()

    # Advanced
    print(f"  {clr.C.BOLD}Advanced{clr.C.RESET}")
    for cmd in registry.list_commands("advanced"):
        print(f"    {clr.C.CYAN}{cmd.name:<10}{clr.C.RESET} {cmd.description}")
    print()

    # Flags
    print(f"  {clr.C.BOLD}Flags{clr.C.RESET}")
    flags = [
        ("-v, --version", "Show version"),
        ("-h, --help", "Show this help"),
        ("--debug", "Show debug output"),
    ]
    for flag, desc in flags:
        print(f"    {clr.C.DIM}{flag:<20}{clr.C.RESET}{desc}")
    print()

    # Quick start
    print(f"  {clr.C.BOLD}Quick start:{clr.C.RESET}")
    print(f"    {clr.C.DIM}ethan chat{clr.C.RESET}                 Start AI chat")
    print(f"    {clr.C.DIM}ethan run docker build{clr.C.RESET}     Execute command")
    print(f"    {clr.C.DIM}ethan status{clr.C.RESET}               Show system state")
    print()


def show_topic(topic):
    cmd = registry.get(topic)
    if not cmd:
        suggestions = registry.suggest(topic)
        if suggestions:
            print()
            print(f"  {clr.C.RED}{clr.I.CROSS} Unknown topic: '{topic}'{clr.C.RESET}")
            print(f"  {clr.C.CYAN}{clr.I.ARROW} Did you mean?{clr.C.RESET}")
            for s in suggestions:
                print(f"    {clr.C.CYAN}{s.name}{clr.C.RESET}")
        else:
            print()
            print(f"  {clr.C.RED}{clr.I.CROSS} Unknown topic: '{topic}'{clr.C.RESET}")
            print(f"  {clr.C.CYAN}{clr.I.ARROW} Try: ethan --help{clr.C.RESET}")
        print()
        return

    print()
    print(f"  {clr.C.BOLD}{clr.C.BLUE}ethan {cmd.name} — {cmd.description}{clr.C.RESET}")
    print()
    if cmd.usage:
        print(f"  {clr.C.CYAN}Usage:{clr.C.RESET}")
        print(f"    {clr.C.DIM}{cmd.usage}{clr.C.RESET}")
    if cmd.examples:
        print()
        print(f"  {clr.C.CYAN}Examples:{clr.C.RESET}")
        for ex in cmd.examples:
            print(f"    {clr.C.DIM}{ex}{clr.C.RESET}")
    print()