"""Tests for cli/core/colors.py — color system, icons, and formatters."""
from __future__ import annotations

import pytest


class TestConstants:
    """Color and icon constants tests."""

    def test_c_has_reset(self) -> None:
        from cli.core.colors import C
        assert C.RESET == "\033[0m"

    def test_c_has_bold(self) -> None:
        from cli.core.colors import C
        assert C.BOLD == "\033[1m"

    def test_c_has_all_colors(self) -> None:
        from cli.core.colors import C
        for attr in ("BLUE", "CYAN", "GREEN", "YELLOW", "RED", "PURPLE", "WHITE"):
            assert hasattr(C, attr)

    def test_i_has_all_icons(self) -> None:
        from cli.core.colors import I
        for attr in ("CHECK", "CROSS", "WARN", "INFO", "ARROW", "SECTION", "TIMER", "DOT", "CIRCL"):
            assert hasattr(I, attr)


class TestFormatters:
    """Formatter function tests."""

    def test_section(self) -> None:
        from cli.core.colors import section
        result = section("Title")
        assert "Title" in result

    def test_section_with_subtitle(self) -> None:
        from cli.core.colors import section
        result = section("Title", "Subtitle")
        assert "Title" in result
        assert "Subtitle" in result

    def test_success(self) -> None:
        from cli.core.colors import success
        result = success("Done")
        assert "Done" in result

    def test_error_title_only(self) -> None:
        from cli.core.colors import error
        result = error("Failed")
        assert "Failed" in result

    def test_error_with_context(self) -> None:
        from cli.core.colors import error
        result = error("Failed", "context info")
        assert "Failed" in result
        assert "context info" in result

    def test_error_with_suggestion(self) -> None:
        from cli.core.colors import error
        result = error("Failed", "context", "try again")
        assert "Failed" in result
        assert "try again" in result

    def test_warn(self) -> None:
        from cli.core.colors import warn
        result = warn("Warning message")
        assert "Warning message" in result

    def test_warning_alias(self) -> None:
        from cli.core.colors import warning
        result = warning("Warning message")
        assert "Warning message" in result

    def test_info(self) -> None:
        from cli.core.colors import info
        result = info("Info message")
        assert "Info message" in result

    def test_item(self) -> None:
        from cli.core.colors import item
        result = item("List item")
        assert "List item" in result

    def test_metadata(self) -> None:
        from cli.core.colors import metadata
        result = metadata("1.2s")
        assert "1.2s" in result

    def test_online(self) -> None:
        from cli.core.colors import online
        result = online()
        assert "ONLINE" in result

    def test_online_custom(self) -> None:
        from cli.core.colors import online
        result = online("ACTIVE")
        assert "ACTIVE" in result

    def test_offline(self) -> None:
        from cli.core.colors import offline
        result = offline()
        assert "OFFLINE" in result

    def test_offline_custom(self) -> None:
        from cli.core.colors import offline
        result = offline("DOWN")
        assert "DOWN" in result

    def test_prompt_default(self) -> None:
        from cli.core.colors import prompt
        result = prompt()
        assert "ethan" in result

    def test_prompt_states(self) -> None:
        from cli.core.colors import prompt
        for state in ("idle", "working", "error", "thinking", "auto", "chat"):
            result = prompt(state)
            assert state in result
            assert "ethan" in result

    def test_spinner(self) -> None:
        from cli.core.colors import spinner
        result = spinner(0)
        assert result is not None

    def test_progress_bar_zero(self) -> None:
        from cli.core.colors import progress_bar
        result = progress_bar(0, 10)
        assert "0%" in result

    def test_progress_bar_half(self) -> None:
        from cli.core.colors import progress_bar
        result = progress_bar(5, 10)
        assert "50%" in result

    def test_progress_bar_full(self) -> None:
        from cli.core.colors import progress_bar
        result = progress_bar(10, 10)
        assert "100%" in result

    def test_progress_bar_zero_total(self) -> None:
        from cli.core.colors import progress_bar
        result = progress_bar(0, 0)
        assert "0%" in result

    def test_table(self) -> None:
        from cli.core.colors import table
        result = table(["Name", "Value"], [["a", "1"], ["b", "2"]])
        assert "Name" in result
        assert "a" in result

    def test_definition_list(self) -> None:
        from cli.core.colors import definition_list
        result = definition_list({"Key": "Value", "Foo": "Bar"})
        assert "Key" in result
        assert "Value" in result

    def test_timing(self) -> None:
        from cli.core.colors import timing
        result = timing(1.5)
        assert "1.5s" in result

    def test_timing_with_timestamp(self) -> None:
        from cli.core.colors import timing
        result = timing(1.5, "2024-01-01")
        assert "1.5s" in result
        assert "2024-01-01" in result

    def test_counters(self) -> None:
        from cli.core.colors import counters
        result = counters(errors=3, warnings=5)
        assert "3" in result
        assert "errors" in result

    def test_divider(self) -> None:
        from cli.core.colors import divider
        result = divider()
        assert "─" in result

    def test_inline_code(self) -> None:
        from cli.core.colors import inline_code
        result = inline_code("ethan status")
        assert "ethan status" in result

    def test_code_block(self) -> None:
        from cli.core.colors import code_block
        result = code_block("python", "print('hello')")
        assert "python" in result
        assert "print('hello')" in result

    def test_output_lines(self) -> None:
        from cli.core.colors import output_lines
        result = output_lines(["line1", "line2"])
        assert "line1" in result
        assert "line2" in result