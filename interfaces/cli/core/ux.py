"""ETHAN Command UX Layer — autocomplete, inline help, typo suggestions, smart errors.

Usage:
    from core.ux import UX

    UX.show_help("chat")
    suggestion = UX.suggest_command("chatt", ["chat", "run", "status"])
    print(UX.smart_error("unknown_command", input="chatt", suggestion="chat"))
"""

import difflib


class UX:
    """Command-line UX helpers."""

    @staticmethod
    def levenshtein(a: str, b: str) -> int:
        """Calculate Levenshtein distance."""
        if len(a) < len(b):
            return UX.levenshtein(b, a)
        if len(b) == 0:
            return len(a)
        prev = range(len(b) + 1)
        for i, ca in enumerate(a):
            curr = [i + 1]
            for j, cb in enumerate(b):
                ins = prev[j + 1] + 1
                dele = curr[j] + 1
                subs = prev[j] + (0 if ca == cb else 1)
                curr.append(min(ins, dele, subs))
            prev = curr
        return prev[-1]

    @staticmethod
    def suggest_command(input_str: str, commands: list[str], cutoff: int = 2) -> str | None:
        """Return the closest matching command, or None."""
        if not input_str or not commands:
            return None
        matches = difflib.get_close_matches(input_str, commands, n=1, cutoff=0.3)
        if matches:
            return matches[0]
        # Fallback: manual distance check for very short typos
        best = None
        best_dist = cutoff + 1
        for cmd in commands:
            dist = UX.levenshtein(input_str, cmd)
            if dist <= cutoff and dist < best_dist:
                best = cmd
                best_dist = dist
        return best

    @staticmethod
    def show_help(topic: str | None = None) -> None:
        """Display minimal help."""
        from interfaces.cli.core import colors as clr
        import sys

        help_map = {
            None: (
                "ETHAN — Cognitive Runtime CLI",
                [
                    ("chat", "Interactive AI chat"),
                    ("run", "Execute via capabilities"),
                    ("status", "Show system state"),
                    ("logs", "Tail system logs"),
                    ("plugin", "Manage plugins"),
                    ("shell", "Open ethan-shell"),
                    ("help", "Show help"),
                ],
                [
                    ("-v, --version", "Show version"),
                    ("-h, --help", "Show this help"),
                ],
            ),
            "chat": (
                "ethan chat — interactive AI chat",
                [],
                [
                    ("ethan chat", "Start new session"),
                    ("ethan chat --resume", "Resume last session"),
                ],
            ),
            "run": (
                "ethan run — execute a command via capabilities",
                [],
                [
                    ("ethan run <cmd>", "Execute shell command"),
                    ("ethan run docker build", "Build docker image"),
                ],
            ),
            "status": (
                "ethan status — show kernel/system state",
                [],
                [
                    ("ethan status", "Show state summary"),
                    ("ethan status --verbose", "Show full state"),
                ],
            ),
            "logs": (
                "ethan logs — tail system logs",
                [],
                [
                    ("ethan logs --follow", "Follow logs live"),
                    ("ethan logs --lines 50", "Show last 50 lines"),
                ],
            ),
            "plugin": (
                "ethan plugin — manage plugins",
                [],
                [
                    ("ethan plugin list", "List installed plugins"),
                    ("ethan plugin install <path>", "Install a plugin"),
                    ("ethan plugin remove <name>", "Remove a plugin"),
                ],
            ),
        }

        title, _, examples = help_map.get(topic, help_map[None])
        print()
        print(f"  {clr.C.BOLD}{title}{clr.C.RESET}")
        print()
        if topic and topic in help_map:
            _, _, items = help_map[topic]
            print(f"  {clr.C.CYAN}Usage:{clr.C.RESET}")
            for usage, desc in items:
                print(f"    {clr.C.DIM}{usage}{clr.C.RESET}  {desc}")
        else:
            print(f"  {clr.C.CYAN}Commands:{clr.C.RESET}")
            _, commands, _ = help_map[None]
            for cmd, desc in commands:
                print(f"    {clr.C.BOLD}{cmd:<10}{clr.C.RESET} {desc}")
            print()
            print(f"  {clr.C.CYAN}Flags:{clr.C.RESET}")
            for flag, desc in help_map[None][2]:
                print(f"    {flag:<20}{desc}")
        print()

    @staticmethod
    def smart_error(kind: str, **context) -> str:
        """Generate actionable error block."""
        from interfaces.cli.core import colors as clr

        errors = {
            "unknown_command": lambda ctx: (
                f"{clr.C.RED}{clr.I.CROSS} Unknown command: '{ctx['input']}'{clr.C.RESET}\n"
                + (f"  {clr.C.DIM}{clr.I.ARROW} Did you mean? {ctx['suggestion']}{clr.C.RESET}\n" if ctx.get('suggestion') else "")
                + f"  {clr.C.CYAN}{clr.I.ARROW} Try: ethan --help{clr.C.RESET}"
            ),
            "missing_argument": lambda ctx: (
                f"{clr.C.RED}{clr.I.CROSS} Missing argument: <{ctx['arg']}>{clr.C.RESET}\n"
                + f"  {clr.C.CYAN}{clr.I.ARROW} Usage: {ctx['usage']}{clr.C.RESET}\n"
                + f"  {clr.C.CYAN}{clr.I.ARROW} Example: {ctx['example']}{clr.C.RESET}"
            ),
            "command_failed": lambda ctx: (
                f"{clr.C.RED}{clr.I.CROSS} Command failed: {ctx['command']}{clr.C.RESET}\n"
                + f"  {clr.C.DIM}{clr.I.ARROW} Exit code {ctx.get('code', '?')}{clr.C.RESET}\n"
                + f"  {clr.C.CYAN}{clr.I.ARROW} Try: ethan logs --follow{clr.C.RESET}"
            ),
            "api_unreachable": lambda ctx: (
                f"{clr.C.RED}{clr.I.CROSS} API unreachable{clr.C.RESET}\n"
                + f"  {clr.C.DIM}{clr.I.ARROW} ethan daemon may be stopped{clr.C.RESET}\n"
                + f"  {clr.C.CYAN}{clr.I.ARROW} try: ethan daemon start{clr.C.RESET}"
            ),
            "permission_denied": lambda ctx: (
                f"{clr.C.RED}{clr.I.CROSS} Permission denied{clr.C.RESET}\n"
                + f"  {clr.C.DIM}{clr.I.ARROW} {ctx.get('reason', '')}{clr.C.RESET}\n"
                + f"  {clr.C.CYAN}{clr.I.ARROW} Run as: {ctx.get('run_as', '')}{clr.C.RESET}"
            ),
        }
        fn = errors.get(kind, lambda ctx: f"{clr.C.RED}{clr.I.CROSS} Error{clr.C.RESET}")
        return fn(context)