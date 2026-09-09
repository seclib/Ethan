"""Diagnostic éphémère — état de sys.modules pour interfaces.cli.*."""
import sys


def test_diag_state():
    print("FINDER0", type(sys.meta_path[0]).__name__, file=sys.stderr)
    for k in sorted(k for k in sys.modules if k.startswith("interfaces.cli")):
        m = sys.modules[k]
        alias = "cli" + k[len("interfaces"):]
        target = sys.modules.get(alias)
        print("KEY", k, "IS_ALIAS", target is m if target else "no-alias", file=sys.stderr)
    print("---", file=sys.stderr)
    print("CHAT_IN_SYS", "cli.commands.chat" in sys.modules, file=sys.stderr)
    print("CLIENT_IN_SYS", "cli.core.client" in sys.modules, file=sys.stderr)