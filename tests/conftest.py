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
    try:
        import httpx as _real_httpx_source
    except Exception:  # pragma: no cover
        _real_httpx_source = None
    dummy = types.ModuleType("httpx")
    if _real_httpx_source is not None:
        dummy.__dict__.update(getattr(_real_httpx_source, "__dict__", {}))

    class _DummyAsyncClient:
        """A minimal async client mock that returns empty responses
        so adapter code can parse them without network calls.

        When constructed with an ``httpx`` ASGI transport (as the config
        persistence tests do), delegate to the real ``httpx.AsyncClient``
        so in-process ASGI requests keep working.
        """

        def __init__(self, *args, **kwargs):
            self._transport = kwargs.get("transport")
            self._real = None
            if _real_httpx_source is not None and self._transport is not None:
                try:
                    self._real = _real_httpx_source.AsyncClient(*args, **kwargs)
                except Exception:  # pragma: no cover - fall back to empty mock
                    self._real = None

        async def _request(self, method, *args, **kwargs):
            if self._real is not None:
                return await getattr(self._real, method)(*args, **kwargs)
            return _DummyResponse("")

        async def get(self, *args, **kwargs):
            return await self._request("get", *args, **kwargs)

        async def post(self, *args, **kwargs):
            return await self._request("post", *args, **kwargs)

        async def put(self, *args, **kwargs):
            return await self._request("put", *args, **kwargs)

        async def patch(self, *args, **kwargs):
            return await self._request("patch", *args, **kwargs)

        async def delete(self, *args, **kwargs):
            return await self._request("delete", *args, **kwargs)

        async def __aenter__(self):
            if self._real is not None:
                return await self._real.__aenter__()
            return self

        async def __aexit__(self, *args):
            if self._real is not None:
                return await self._real.__aexit__(*args)
            await self.aclose()
            return False

        def is_closed(self):
            if self._real is not None:
                return self._real.is_closed
            return False

        async def aclose(self):
            if self._real is not None:
                await self._real.aclose()

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
from fastapi.testclient import TestClient
from interfaces.api.main import app


@pytest.fixture(autouse=True)
def _patch_httpx_for_async_tests():
    """Ensure httpx is mocked in async tests that need it."""
    _install_dummy_httpx()
    yield


@pytest.fixture
def contract_client():
    """Client de contrat API (ADR-3006), cadence minimale."""
    with TestClient(app) as client:
        yield client


import asyncio as _asyncio
import os as _os

try:
    import tests.test_config_persistence as _cfg_persistence
except Exception:  # pragma: no cover
    _cfg_persistence = None

try:
    import asyncpg as _asyncpg
except Exception:  # pragma: no cover
    _asyncpg = None


@pytest.fixture(autouse=True)
def _clear_hrot_durable_state():
    """Isolate durable HROT approvals between tests without weakening them."""
    from pathlib import Path as _Path

    approval_file = _Path.home() / ".ethan" / "hrot" / "approvals.jsonl"
    try:
        approval_file.unlink(missing_ok=True)
    except OSError:
        pass

    dsn = _os.getenv("DATABASE_URL")
    if dsn is None and _cfg_persistence is not None:
        dsn = _cfg_persistence._dsn()

    if dsn and _asyncpg is not None and _cfg_persistence is not None and _cfg_persistence._pg_available():
        async def _clear() -> None:
            pool = await _asyncpg.create_pool(dsn, min_size=1, max_size=1)
            try:
                async with pool.acquire() as conn:
                    await conn.execute("DELETE FROM hrot_approvals")
            finally:
                await pool.close()

        try:
            _asyncio.run(_clear())
        except Exception:
            pass

    yield

    try:
        approval_file.unlink(missing_ok=True)
    except OSError:
        pass
