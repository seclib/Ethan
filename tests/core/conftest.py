"""Minimal conftest for core tests to avoid heavy imports."""

import pytest


@pytest.fixture
def fixed_time():
    from datetime import datetime
    return datetime(2024, 1, 1, 12, 0, 0)