"""Command matrix tests — smoke test all commands."""

import pytest

from cli.registry import COMMAND_HANDLERS, discover_commands


class TestCommandMatrix:
    """Smoke test all registered commands."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure commands are discovered."""
        discover_commands()

    def test_all_commands_registered(self):
        """All expected commands should be registered.

        La liste reflète le **contrat public actuel** du CLI ETHAN
        (`interfaces/cli/commands/`). Les commandes historiques
        `service`, `plugins`, `think` et `run` ont été retirées lors du
        rebuild (le Runtime legacy qu'elles adressaient n'existe plus) :
        leur présence ici masquerait une régression de suppression.

        Le TUI officiel est `cli` — `tui` n'est PAS une commande publique.
        """
        expected_commands = [
            # Infrastructure
            "doctor",
            "up",
            "down",
            "restart",
            "status",
            "logs",
            # Cognitive
            "agent",
            "agents",
            "approval",
            "bench",
            "chat",
            "cli",
            "document",
            "documents",
            "extension",
            "knowledge",
            "mcp",
            "memory",
            "mission",
            "missions",
            "model",
            "plugin",
            "provider",
            "router",
            "skill",
            "suggest",
            # System
            "auth",
            "config",
            "daemon",
            "exec",
            "help",
            "version",
        ]

        for cmd in expected_commands:
            assert cmd in COMMAND_HANDLERS, f"Command '{cmd}' not registered"

    def test_removed_legacy_commands_absent(self):
        """Les commandes du Runtime legacy ne doivent pas réapparaître.

        `repl` et `tui` ont été retirés de l'interface publique : `ethan cli`
        est le seul TUI interactif officiel (ADR-4010).
        """
        for cmd in ("repl", "tui", "service", "plugins", "think", "run"):
            assert cmd not in COMMAND_HANDLERS, f"Command '{cmd}' should not be registered"

    def test_all_commands_callable(self):
        """All registered commands must be callable."""
        non_callable = []
        for name, fn in COMMAND_HANDLERS.items():
            if not callable(fn):
                non_callable.append(name)

        assert len(non_callable) == 0, f"Non-callable commands: {non_callable}"

    def test_no_circular_imports(self):
        """Commands should not have circular imports."""
        import importlib
        import sys

        # Re-import the CLI modules in ISOLATION to detect circular imports,
        # WITHOUT dropping them from sys.modules.
        #
        # Supprimer `sys.modules['cli.*']` rechargeait les modules avec les
        # chemins RÉELS (`~/.ethan`, `~/.config/ethan`) : les fixtures
        # d'isolation du conftest (monkeypatch) ne s'appliquent plus au
        # module rechargé, et les commandes écrit alors dans le répertoire
        # utilisateur réel — pollution croisée observée sur les snapshots
        # (historique local) et sur les tests TUI (frontière HTTP).
        #
        # On restaure donc le registre original après l'essai.
        saved_modules = {k: v for k, v in sys.modules.items() if k.startswith("cli.")}
        try:
            for mod in list(saved_modules):
                del sys.modules[mod]
            importlib.import_module("cli.registry")
        except ImportError as e:
            pytest.fail(f"Circular import detected: {e}")
        finally:
            for mod in [k for k in sys.modules if k.startswith("cli.")]:
                del sys.modules[mod]
            sys.modules.update(saved_modules)

    def test_command_handlers_return_int(self):
        """Command handlers should return int exit codes."""
        bad_returns = []
        for name, fn in COMMAND_HANDLERS.items():
            try:
                result = fn([])
                if result is not None and not isinstance(result, int):
                    bad_returns.append(f"{name}: returned {type(result).__name__}")
            except SystemExit:
                pass  # OK
            except Exception:
                pass  # OK for smoke test

        assert len(bad_returns) == 0, "Commands with bad return types:\n" + "\n".join(bad_returns)
