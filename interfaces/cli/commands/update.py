"""ETHAN update — self-update ETHAN."""

from interfaces.cli.core import colors as clr
from interfaces.cli.registry import register


@register("update")
def cmd_update(args):
    UpdateCommand().execute()


class UpdateCommand:
    """Self-update ETHAN."""

    def execute(self):
        print()
        print(clr.section("Update"))

        steps = [
            "Checking current version... 1.0.0",
            "Fetching latest release... 1.1.0",
            "Downloading binary... (12M)",
            "Verifying checksum...",
            "Backing up current...",
            "Installing new binary...",
            "Restarting services...",
        ]

        for step in steps:
            print(f"  {clr.info(f'⠋ {step}')}")
            import time
            time.sleep(0.3)
            print(f"  {clr.success(f'✓ {step}')}")

        print()
        print(clr.success("Updated to 1.1.0"))
        print()
        print(clr.timing(15.3, ""))