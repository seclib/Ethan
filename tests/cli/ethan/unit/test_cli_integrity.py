"""Tests d'intégrité du CLI — garde-fous issus de l'audit Phase 1.

Couvre :
- handlers tous callables (crash historique 'str' object is not callable) ;
- purge des handlers slash REPL du dispatch CLI ;
- métadonnées d'aide (__meta__) présentes et renseignées ;
- commands lifecycle (up/down/restart) réelles — plus de simulation ;
- résolution du token (env > config) et header Bearer sur l'API.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest import mock


class TestRegistryIntegrity:
    def test_all_handlers_callable(self) -> None:
        from cli.registry import COMMAND_HANDLERS, discover_commands

        discover_commands()
        non_callable = [n for n, fn in COMMAND_HANDLERS.items() if not callable(fn)]
        assert non_callable == []

    def test_repl_is_not_a_public_command(self) -> None:
        """Le REPL legacy ne doit plus être une commande publique.

        `ethan cli` est le seul TUI interactif officiel (ADR-4010). Le REPL
        legacy interrogeait un Runtime inexistant (`:8002` / socket Unix) et
        portait un second registre de sessions local : il a été retiré.
        """
        from cli.registry import COMMAND_HANDLERS, discover_commands

        discover_commands()
        assert "repl" not in COMMAND_HANDLERS
        assert "tui" not in COMMAND_HANDLERS
        # Le TUI officiel reste bien accessible.
        assert "cli" in COMMAND_HANDLERS

    def test_no_legacy_runtime_client_in_cli(self) -> None:
        """Aucun module du CLI ne doit parler au Runtime legacy `:8002`.

        Le Runtime legacy (socket Unix `/run/ethan/runtime.sock` ou HTTP
        `:8002`) n'est plus le contrat Core : la frontière HTTP unique est
        `interfaces/cli/core/client.py` vers l'API Core.
        """
        import pathlib

        cli_root = pathlib.Path(__file__).resolve().parents[3] / "interfaces" / "cli"
        offenders: list[str] = []
        for path in cli_root.rglob("*.py"):
            source = path.read_text(encoding="utf-8", errors="replace")
            if ":8002" in source or "runtime.sock" in source:
                offenders.append(str(path.relative_to(cli_root)))
        assert offenders == [], f"Runtime legacy encore référencé : {offenders}"

    def test_help_metadata_present(self) -> None:
        from cli.registry import COMMAND_HANDLERS, discover_commands

        discover_commands()
        for name in ("status", "up", "down", "restart", "doctor", "auth", "version"):
            assert name in COMMAND_HANDLERS, f"missing command: {name}"
            meta = getattr(COMMAND_HANDLERS[name], "__meta__", None)
            assert meta, f"{name} has no __meta__ (aide vide)"
            assert meta.get("group"), f"{name} has no group"
            assert meta.get("description"), f"{name} has no description"

    def test_lifecycle_commands_bind_to_real_modules(self) -> None:
        """up/down/restart doivent venir des vrais fichiers docker, pas d'une simulation."""
        from cli.registry import COMMAND_HANDLERS, discover_commands

        discover_commands()
        for name in ("up", "down", "restart"):
            handler = COMMAND_HANDLERS[name]
            # Les modules sont chargés dynamiquement sans passer par
            # sys.modules : co_filename donne l'origine réelle du handler.
            origin = handler.__code__.co_filename
            assert origin.endswith(f"commands/{name}.py"), (
                f"{name} bound to {origin} — simulation suspecte"
            )

    def test_simulated_commands_are_gone(self) -> None:
        """Les commandes simulation (service/think/run/update) ont été retirées."""
        from cli.registry import COMMAND_HANDLERS, discover_commands

        discover_commands()
        for ghost in ("service", "think", "run", "update"):
            assert ghost not in COMMAND_HANDLERS, f"stale simulated command: {ghost}"


class TestTokenResolution:
    def test_env_token_has_priority(self, monkeypatch, tmp_path: Path) -> None:
        from cli.core.client import get_token

        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"token": "from-config"}))
        monkeypatch.setattr("cli.config.CONFIG_FILE", str(config_file))
        monkeypatch.setenv("ETHAN_TOKEN", "from-env")
        assert get_token() == "from-env"

    def test_falls_back_to_config_file(self, monkeypatch, tmp_path: Path) -> None:
        from cli.core.client import get_token

        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"token": "from-config"}))
        # `get_token()` lit le config legacy via `interfaces.cli.config`
        # (le module de compatibilité `cli.config` est le même objet).
        monkeypatch.setattr("interfaces.cli.config.CONFIG_FILE", str(config_file))
        monkeypatch.setattr("cli.config.CONFIG_FILE", str(config_file))
        monkeypatch.delenv("ETHAN_TOKEN", raising=False)
        # Isolate the bootstrap token source by mocking get_base_url to a non-local host
        # and clearing the local secret so the fallback goes to the config file
        import interfaces.cli.core.client as client_mod
        with mock.patch.object(client_mod, "get_base_url", lambda: "http://remote.api.invalid"):
            with mock.patch.object(client_mod, "_local_bootstrap_token", None):
                assert get_token() == "from-config"

    def test_returns_none_without_token(self, monkeypatch, tmp_path: Path) -> None:
        from cli.core import client

        # Toutes les sources de get_token sont isolées : contexte CLI,
        # env, credentials.json, config legacy ET token bootstrap local
        # (auto-généré quand base_url est localhost — sinon le test verrait
        # un vrai JWT admin sur une machine de dev authentifiée).
        monkeypatch.setattr("interfaces.cli.core.context.get_context", lambda: None)
        monkeypatch.delenv("ETHAN_TOKEN", raising=False)
        monkeypatch.setattr(
            "interfaces.cli.core.config.get_token_from_credentials",
            lambda *args, **kwargs: None,
        )
        monkeypatch.setattr(
            "interfaces.cli.config.CONFIG_FILE", str(tmp_path / "missing.json")
        )
        monkeypatch.setattr(
            "cli.config.CONFIG_FILE", str(tmp_path / "missing.json")
        )
        monkeypatch.setattr(client, "get_base_url", lambda: "http://ethan.invalid")
        monkeypatch.setattr(client, "_local_bootstrap_token", None)

        assert client.get_token() is None


class TestRequestJson:
    def test_sends_bearer_and_json_body(self) -> None:
        from cli.core import client

        captured = {}

        class _Resp:
            def read(self):
                return json.dumps({"ok": True}).encode()

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        def _fake_urlopen(req, timeout=None):
            captured["url"] = req.full_url
            captured["method"] = req.get_method()
            captured["auth"] = req.get_header("Authorization")
            captured["body"] = req.data
            return _Resp()

        with mock.patch.object(client, "get_token", return_value="jwt-abc"):
            with mock.patch.object(client, "urlopen", side_effect=_fake_urlopen):
                result = client.request_json("POST", "/v1/test", {"a": 1})

        assert result == {"ok": True}
        assert captured["url"].endswith("/v1/test")
        assert captured["method"] == "POST"
        assert captured["auth"] == "Bearer jwt-abc"
        assert json.loads(captured["body"]) == {"a": 1}

    def test_api_error_carries_status_and_detail(self) -> None:
        import io

        from cli.core import client

        def _fake_urlopen(req, timeout=None):
            raise client.HTTPError(
                req.full_url, 401, "Unauthorized", {}, io.BytesIO(b'{"detail":"nope"}')
            )

        with mock.patch.object(client, "urlopen", side_effect=_fake_urlopen):
            try:
                client.request_json("GET", "/v1/test")
                raise AssertionError("APIError not raised")
            except client.APIError as exc:
                assert exc.status == 401
                assert "nope" in str(exc)
