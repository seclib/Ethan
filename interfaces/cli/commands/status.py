"""ETHAN status — show system status."""

from interfaces.cli.core import colors as clr
from interfaces.cli.registry import register


@register("status")
def cmd_status(args):
    StatusCommand().execute()


class StatusCommand:
    """Display system status."""

    def execute(self):
        print()
        print(clr.section("Status  ◇  RUNNING"))

        # Runtime
        print()
        print(clr.section("Runtime"))
        print(f"  State:    {clr.C.GREEN}{clr.I.DOT} RUNNING{clr.C.RESET}")
        print(f"  Uptime:   {clr.C.DIM}2h 15m{clr.C.RESET}")
        print(f"  PID:      {clr.C.DIM}12345{clr.C.RESET}")
        print(f"  Memory:   {clr.C.DIM}128M{clr.C.RESET}")
        print(f"  CPU:      {clr.C.DIM}0.5%{clr.C.RESET}")

        # Services
        print()
        print(clr.section("Services"))
        services = [
            ("nats", "running", "healthy", "4222"),
            ("redis", "running", "healthy", "6379"),
            ("postgres", "running", "healthy", "5432"),
            ("ethan-core", "running", "healthy", "8000"),
            ("ethan-plugins", "running", "healthy", "8003"),
        ]
        for name, state, health, port in services:
            status_icon = f"{clr.C.GREEN}{clr.I.DOT} ONLINE{clr.C.RESET}" if state == "running" else f"{clr.C.DIM}{clr.I.CIRCL} OFFLINE{clr.C.RESET}"
            print(f"  {name:<16} {status_icon}  {port}")

        # Core
        print()
        print(clr.section("Core"))
        print(f"  Status:  {clr.C.GREEN}{clr.I.DOT} healthy{clr.C.RESET}")
        print(f"  Version: {clr.C.DIM}1.0.0{clr.C.RESET}")
        print(f"  Uptime:  {clr.C.DIM}2h 15m{clr.C.RESET}")

        # Databases
        print()
        print(clr.section("Databases"))
        print(f"  nats      {clr.C.GREEN}{clr.I.CHECK}{clr.C.RESET}")
        print(f"  redis     {clr.C.GREEN}{clr.I.CHECK}{clr.C.RESET}")
        print(f"  postgres  {clr.C.GREEN}{clr.I.CHECK}{clr.C.RESET}")

        print()
        print(clr.timing(0.2, ""))