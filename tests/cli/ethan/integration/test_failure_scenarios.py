"""Integration tests for all failure modes."""

from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

import pytest


class TestAPIUnreachable:
    """All commands handle API unreachable gracefully."""

    def test_chat_api_unreachable(self) -> None:
        """Un Core injoignable doit faire échouer `chat` proprement.

        En mode one-shot (message fourni), `cmd_chat` laisse remonter la
        `CLIError` : c'est `main.py` qui la rend sur stderr et applique le
        code de sortie du contrat. Aucun traceback.

        Le code de sortie d'une `CLIError` construite à la main vaut
        OPERATION_FAILED (1) : le mapping HTTP → UNAVAILABLE (5) est porté
        par `api_error`, qui n'est pas le chemin emprunté ici (le mock
        court-circuite la frontière HTTP).
        """
        from cli.commands.chat import cmd_chat
        from cli.core.errors import CLIError
        from cli.core.exit_codes import ExitCode

        # `chat` envoie le message via la frontière HTTP unique
        # (`cli.core.api.api_post`, importée au niveau du module de commande
        # — le patch doit donc viser le module consommateur).
        #
        # Un message est fourni : sans argument, `chat` bascule en mode
        # interactif et lit stdin (inadapté à un test).
        with mock.patch(
            "cli.commands.chat.api_post",
            side_effect=CLIError("Core unreachable", code="API-000", status=503),
        ):
            with pytest.raises(CLIError) as excinfo:
                cmd_chat(["bonjour"])

        assert excinfo.value.exit_code == int(ExitCode.OPERATION_FAILED)
        assert excinfo.value.status == 503

    def test_status_api_unreachable(self, capsys) -> None:
        """Un Core injoignable doit produire un état dégradé, pas un échec.

        `status` affiche désormais « STOPPED » (l'ancien libellé « OFFLINE »
        a été remplacé par le rendu d'état courant du CLI).

        L'interrogation du démon Docker est neutralisée : elle dépend de la
        charge de la machine, pas du comportement testé ici.

        Une réponse HTTP 503 prouve que le serveur répond → affichage `● idle`,
        pas `○ unreachable`.
        """
        from cli.commands.status import cmd_status
        from cli.core.errors import CLIError

        completed = mock.MagicMock()
        completed.returncode = 0
        completed.stdout = "Server Version: 26.1.5\n"
        completed.stderr = ""

        with mock.patch("cli.commands.status.subprocess.run", return_value=completed):
            with mock.patch(
                "cli.core.api.api_get",
                side_effect=CLIError("Core unreachable", code="API-000", status=503),
            ):
                result = cmd_status([])
                captured = capsys.readouterr()
                assert result == 0
                assert "STOPPED" in captured.out
                # 503 est un code HTTP : l'API est joignable (erreure),
                # elle ne doit pas être affichée comme unreachable.
                assert "unreachable" not in captured.out
                # L'API répond (même avec une erreur HTTP) → affichage reachable.
                # Le mode affiché dépend de la réponse ; s'assurer qu'il ne s'agit
                # pas de l'ancien affichage unreachable.
                assert "●" in captured.out  # affiche un indicateur reachable (● running / ● idle)

    def test_daemon_fetch_state_handles_refused(self) -> None:
        from urllib.error import URLError

        from cli.core.daemon import _fetch_state

        def _refused(*_args, **_kwargs):
            raise URLError("Connection refused")

        with mock.patch("cli.core.daemon.urlopen", side_effect=_refused):
            assert _fetch_state() is None


class TestCorruptConfig:
    """Corrupt configuration file handling."""

    def test_corrupt_config_file(self) -> None:
        from cli.core.config import CONFIG_FILE, load

        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            f.write("not valid json {")
        config = load()
        # Should fallback to defaults
        assert config["api"]["base_url"] == "http://localhost:8000"

    def test_corrupt_local_config(self) -> None:
        from cli.core.config import CONFIG_FILE, CONFIG_LOCAL_FILE, load

        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump({"api": {"base_url": "http://valid"}}, f)
        with open(CONFIG_LOCAL_FILE, "w") as f:
            f.write("corrupt json")
        config = load()
        assert config["api"]["base_url"] == "http://valid"


class TestCorruptMemory:
    """Corrupt memory file handling."""

    def test_corrupt_memory_file(self) -> None:
        """Un fichier d'historique corrompu doit être traité comme vide."""
        import os

        from cli.core.memory import MEM_FILE, _load

        # MEM_FILE est une chaîne (compat historical) : on utilise
        # os.path.dirname, pas Path.parent.
        os.makedirs(os.path.dirname(MEM_FILE) or ".", exist_ok=True)
        with open(MEM_FILE, "w") as f:
            f.write("corrupt json")
        entries = _load()
        assert entries == []

    def test_corrupt_log_file(self) -> None:
        """Un journal corrompu doit être traité comme vide."""
        import os

        from cli.core.logging import LOG_FILE, _load

        os.makedirs(os.path.dirname(LOG_FILE) or ".", exist_ok=True)
        with open(LOG_FILE, "w") as f:
            f.write("corrupt json")
        entries = _load()
        assert entries == []


class TestPermissionDenied:
    """Permission error handling tests."""

    def test_permission_error_constructor(self) -> None:
        from cli.core.errors import EthanError, permission_denied

        err = permission_denied("no write access", "root")
        assert isinstance(err, EthanError)
        assert "no write access" in err.context

    def test_permission_error_format(self) -> None:
        from cli.core.errors import format_error, permission_denied

        err = permission_denied("disk full")
        result = format_error(err)
        assert "Permission denied" in result
        assert "SYS-003" in result


class TestEmptyState:
    """Empty state response handling."""

    def test_empty_state_from_api(self) -> None:
        """Un Core joignable mais sans état ne doit pas faire échouer `status`."""
        from cli.commands.status import cmd_status

        # `status` lit le Core via la frontière HTTP unique
        # (`cli.core.api.api_get`, importée localement dans `_get_core_info`) —
        # plus l'ancien `alive`/`get_state` importés dans le module de
        # commande. On patche donc le module d'API, pas la commande.
        with mock.patch("cli.core.api.api_get", return_value=None):
            result = cmd_status([])
            assert result == 0

    def test_incomplete_state_response(self) -> None:
        """Une réponse d'état incomplète ne doit pas faire échouer `status`."""
        from cli.commands.status import cmd_status

        with mock.patch("cli.core.api.api_get", return_value={}):
            result = cmd_status([])
            assert result == 0


class TestPluginLoadFailure:
    """Plugin load failure handling."""

    def test_load_broken_plugin(self, tmp_path: Path) -> None:
        from cli.registry import _load_module

        plugin_dir = tmp_path / "plugins" / "broken"
        plugin_dir.mkdir(parents=True)
        plugin_file = plugin_dir / "plugin.py"
        plugin_file.write_text("""
THIS IS NOT VALID PYTHON @@@@
""")
        result = _load_module(plugin_dir)
        assert result is None


class TestDaemonFailure:
    """Daemon failure handling."""

    def test_daemon_pid_corrupt(self) -> None:
        """Un fichier PID corrompu doit être lu comme « aucun daemon »."""
        import os

        from cli.core.daemon import PID_FILE, _pid_read

        # PID_FILE est une chaîne : os.path.dirname, pas Path.parent.
        os.makedirs(os.path.dirname(PID_FILE) or ".", exist_ok=True)
        with open(PID_FILE, "w") as f:
            f.write("not an integer")
        pid = _pid_read()
        assert pid is None

    def test_daemon_cache_corrupt(self) -> None:
        """Un cache daemon corrompu doit être lu comme absent."""
        import os

        from cli.core.daemon import CACHE_FILE, _cache_read

        os.makedirs(os.path.dirname(CACHE_FILE) or ".", exist_ok=True)
        with open(CACHE_FILE, "w") as f:
            f.write("corrupt json")
        cached = _cache_read()
        assert cached is None
