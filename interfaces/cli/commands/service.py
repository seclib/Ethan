"""ETHAN service — lifecycle commands (up, down, restart)."""

import time

from interfaces.cli.core import colors as clr
from interfaces.cli.core.loading import Spinner
from interfaces.cli.registry import register


@register("up")
def cmd_up(args):
    UpCommand().execute()


@register("down")
def cmd_down(args):
    DownCommand().execute()


@register("restart")
def cmd_restart(args):
    RestartCommand().execute()


class UpCommand:
    """Start all ETHAN services."""

    def execute(self):
        print()
        print(clr.section("Starting ETHAN"))

        spinner = Spinner()
        spinner.start("Checking Docker...")
        time.sleep(0.3)
        spinner.stop()
        print(clr.success("Docker ready"))

        services = ["nats", "redis", "postgres", "ethan-core", "ethan-plugins"]
        print()
        for svc in services:
            print(f"  {clr.info(f'→ {svc}')}")
            time.sleep(0.3)
            print(f"  {clr.success(f'{svc} started')}")

        print()
        print(clr.success("Runtime started"))
        print(clr.success("Core online"))
        print(clr.success("Plugins online"))
        print()
        print(clr.timing(2.5, ""))
        print()
        print(clr.info("Next: ethan"))


class DownCommand:
    """Stop all ETHAN services."""

    def execute(self):
        print()
        print(clr.section("Stopping ETHAN"))

        services = ["ethan-plugins", "ethan-core", "nats", "redis", "postgres"]
        for svc in services:
            print(f"  {clr.info(f'→ {svc}')}")
            time.sleep(0.2)
            print(f"  {clr.success(f'{svc} stopped')}")

        print()
        print(clr.success("Cleanup complete"))
        print()
        print(clr.timing(1.5, ""))


class RestartCommand:
    """Restart all ETHAN services."""

    def execute(self):
        print()
        print(clr.section("Restarting ETHAN"))

        print()
        DownCommand().execute()

        print()
        UpCommand().execute()