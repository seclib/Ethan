"""Tests for cli/core/config.py — configuration loading & merging."""
from __future__ import annotations

import json
from pathlib import Path

import pytest


class TestDefaults:
    """Default configuration tests."""

    def test_defaults_exist(self) -> None:
        from cli.core.config import DEFAULTS
        assert "api" in DEFAULTS
        assert "daemon" in DEFAULTS
        assert "memory" in DEFAULTS
        assert "logging" in DEFAULTS
        assert "plugins" in DEFAULTS

    def test_default_api_base_url(self) -> None:
        from cli.core.config import DEFAULTS
        assert DEFAULTS["api"]["base_url"] == "http://localhost:8000"

    def test_default_api_timeout(self) -> None:
        from cli.core.config import DEFAULTS
        assert DEFAULTS["api"]["timeout"] == 10


class TestLoad:
    """load() tests."""

    def test_load_returns_defaults_when_no_files(self) -> None:
        from cli.core.config import load
        config = load()
        assert config["api"]["base_url"] == "http://localhost:8000"

    def test_load_merges_user_config(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from cli.core.config import CONFIG_FILE, load
        # Write user config
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump({"api": {"base_url": "http://custom:9000"}}, f)
        config = load()
        assert config["api"]["base_url"] == "http://custom:9000"

    def test_load_merges_local_config(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from cli.core.config import CONFIG_FILE, CONFIG_LOCAL_FILE, load
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump({"api": {"base_url": "http://user:9000"}}, f)
        with open(CONFIG_LOCAL_FILE, "w") as f:
            json.dump({"api": {"base_url": "http://local:9000"}}, f)
        config = load()
        assert config["api"]["base_url"] == "http://local:9000"


class TestDeepMerge:
    """_deep_merge() tests."""

    def test_deep_merge_simple(self) -> None:
        from cli.core.config import _deep_merge
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = _deep_merge(base, override)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_deep_merge_nested(self) -> None:
        from cli.core.config import _deep_merge
        base = {"api": {"url": "http://a", "timeout": 10}}
        override = {"api": {"url": "http://b"}}
        result = _deep_merge(base, override)
        assert result["api"]["url"] == "http://b"
        assert result["api"]["timeout"] == 10

    def test_deep_merge_deeply_nested(self) -> None:
        from cli.core.config import _deep_merge
        base = {"level1": {"level2": {"key": "a", "keep": "me"}}}
        override = {"level1": {"level2": {"key": "b"}}}
        result = _deep_merge(base, override)
        assert result["level1"]["level2"]["key"] == "b"
        assert result["level1"]["level2"]["keep"] == "me"

    def test_deep_merge_non_dict_override(self) -> None:
        from cli.core.config import _deep_merge
        base = {"key": {"nested": "value"}}
        override = {"key": "scalar"}
        result = _deep_merge(base, override)
        assert result == {"key": "scalar"}


class TestGetAndSet:
    """get() and set_value() tests."""

    def test_get_dot_notation(self) -> None:
        from cli.core.config import get
        val = get("api.base_url")
        assert val == "http://localhost:8000"

    def test_get_nonexistent_returns_default(self) -> None:
        from cli.core.config import get
        val = get("nonexistent.key", "fallback")
        assert val == "fallback"

    def test_get_nonexistent_without_default(self) -> None:
        from cli.core.config import get
        val = get("nonexistent.key")
        assert val is None

    def test_set_value_updates_config(self) -> None:
        from cli.core.config import set_value, get
        set_value("api.base_url", "http://updated:8000")
        assert get("api.base_url") == "http://updated:8000"

    def test_set_value_creates_nested_keys(self) -> None:
        from cli.core.config import set_value, get
        set_value("custom.nested.key", "value")
        assert get("custom.nested.key") == "value"

    def test_reset_restores_defaults(self) -> None:
        from cli.core.config import set_value, get, reset, DEFAULTS
        set_value("api.base_url", "http://custom:8000")
        reset()
        assert get("api.base_url") == DEFAULTS["api"]["base_url"]


class TestEnvVars:
    """Environment variable override tests."""

    def test_env_var_overrides(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from cli.core.config import load
        monkeypatch.setenv("ETHAN_API_BASE_URL", "http://env:7000")
        config = load()
        assert config["api"]["base_url"] == "http://env:7000"

    def test_env_var_missing_prefix_ignored(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from cli.core.config import load
        monkeypatch.setenv("OTHER_VAR", "value")
        config = load()
        assert "OTHER_VAR" not in str(config)

    def test_env_var_with_simple_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from cli.core.config import load
        monkeypatch.setenv("ETHAN_DEBUG", "true")
        config = load()
        assert config.get("debug") == "true"


class TestShow:
    """show() tests."""

    def test_show_output(self, capsys: pytest.CaptureFixture) -> None:
        from cli.core.config import show
        show()
        captured = capsys.readouterr()
        assert "api" in captured.out
        assert "base_url" in captured.out