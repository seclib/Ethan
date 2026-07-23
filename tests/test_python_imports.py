import sys
import os

# Ensure project root on path for test execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_core_kernel_import():
    import core.kernel  # noqa: F401


def test_core_main_import():
    import core.main  # noqa: F401


def test_interfaces_api_import():
    import interfaces.api.main  # noqa: F401


def test_interfaces_cli_import():
    import interfaces.cli.main  # noqa: F401
    import interfaces.cli.commands.router  # noqa: F401


def test_bootstrap_import():
    import core.bootstrap  # noqa: F401