"""ETHAN help — command catalogue."""

from interfaces.cli.registry import register


@register(
    "help",
    group="system",
    description="Show the command catalogue",
    usage="ethan help",
)
def cmd_help(args):
    """Show the command catalogue."""
    from interfaces.cli.main import _show_help
    from interfaces.cli.registry import Registry

    _show_help(Registry())
    return 0
