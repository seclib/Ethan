"""
Shared test fixtures for ETHAN.

This conftest centralizes the dummy httpx injection pattern used across
adapter tests so that imports of core.adapters.* work without a real HTTP
dependency.
"""

import sys
import types


def _install_dummy_httpx() -> types.ModuleType:
    """Install a minimal dummy httpx module into sys.modules.

    Always replaces sys.modules["httpx"] with the dummy so that adapter
    imports see the mock, not the real network library.
    """
    dummy = types.ModuleType("httpx")

    class _DummyAsyncClient:
        """A minimal async client mock that returns empty responses
        so adapter code can parse them without network calls."""

        def __init__(self, *args, **kwargs):
            pass

        async def get(self, *args, **kwargs):
            return _DummyResponse("")

        async def post(self, *args, **kwargs):
            return _DummyResponse("")

        def is_closed(self):
            return False

        async def aclose(self):
            pass

    class _DummyResponse:
        """Mock HTTP response with empty text."""

        def __init__(self, text: str = ""):
            self.text = text
            self.status_code = 200
            self.content = text.encode()

        def raise_for_status(self):
            pass

        def json(self):
            return {}

        async def aread(self):
            return self.content


    class _DummyTimeout:
        def __init__(self, *args, **kwargs):
            pass

    class _DummyHTTPStatusError(Exception):
        def __init__(self, *args, **kwargs):
            self.response = types.SimpleNamespace(status_code=500, text="")
            super().__init__(*args)

    class _DummyRequestError(Exception):
        pass

    dummy.AsyncClient = _DummyAsyncClient
    dummy.Timeout = _DummyTimeout
    dummy.HTTPStatusError = _DummyHTTPStatusError
    dummy.RequestError = _DummyRequestError
    # Also expose commonly-used names so adapter code can reference them
    dummy.HTTPStatusError = _DummyHTTPStatusError
    dummy.RequestError = _DummyRequestError
    dummy.AsyncClient = _DummyAsyncClient
    dummy._dummy = True
    sys.modules["httpx"] = dummy
    return dummy


# Install at import time so that all test modules can import adapters
_install_dummy_httpx()

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _patch_httpx_for_async_tests():
    """Ensure httpx is mocked in async tests that need it."""
    _install_dummy_httpx()
    yield
