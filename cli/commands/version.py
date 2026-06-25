"""ETHAN version command."""
from cli.registry import register


@register("version", group="core", description="Show version")
def cmd_version(args):
    """Show ETHAN version."""
    print("ethan 2.0")
    return 0