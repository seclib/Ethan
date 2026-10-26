"""
Tests for the JPL Horizons adapter.
"""

import sys
import types

# Install dummy httpx BEFORE importing adapters so the mock is used
_httpx_dummy = types.ModuleType("httpx")


class _DummyTimeout:
    def __init__(self, *args, **kwargs):
        pass


class _DummyAsyncClient:
    def __init__(self, *args, **kwargs):
        pass

    async def get(self, *args, **kwargs):
        class _Resp:
            text = ""
            status_code = 200

            def raise_for_status(self):
                pass

            def json(self):
                return {}

        return _Resp()

    def is_closed(self):
        return False

    async def aclose(self):
        pass


class _DummyHTTPStatusError(Exception):
    def __init__(self, *args, **kwargs):
        self.response = types.SimpleNamespace(status_code=500, text="")
        super().__init__(*args)


class _DummyRequestError(Exception):
    pass


_httpx_dummy.AsyncClient = _DummyAsyncClient
_httpx_dummy.Timeout = _DummyTimeout
_httpx_dummy.HTTPStatusError = _DummyHTTPStatusError
_httpx_dummy.RequestError = _DummyRequestError
sys.modules["httpx"] = _httpx_dummy

import asyncio
import pytest


from core.adapters.jpl_horizons import (
    JPLConfig,
    JPLAdapter,
    JPLQuotaError,
    JPLRequestError,
    JPLConnectionError,
    JPLError,
    get_jpl_adapter,
)


@pytest.fixture
def jpl_config():
    return JPLConfig()


@pytest.fixture
def jpl_adapter(jpl_config):
    return JPLAdapter(config=jpl_config)


def test_get_jpl_adapter(jpl_config):
    adapter = get_jpl_adapter(config=jpl_config)
    assert adapter.config == jpl_config
    asyncio.run(adapter.close())


def test_jpl_adapter_creation(jpl_config):
    adapter = JPLAdapter(config=jpl_config)
    assert adapter.config == jpl_config
    assert adapter.http_timeout == 10.0
    assert adapter.max_retries == 3
    asyncio.run(adapter.close())


def test_search_body_known_object():
    adapter = JPLAdapter(config=JPLConfig())
    result = asyncio.run(adapter.search_body("sun"))
    assert result is not None
    assert result.identifier == "10"
    assert result.name == "Sun"
    assert result.ephemeris_source == "jpl_horizons"
    asyncio.run(adapter.close())


def test_search_body_unknown_object():
    adapter = JPLAdapter(config=JPLConfig())
    result = asyncio.run(adapter.search_body("unknown_celestial_object_xyz"))
    assert result is None
    asyncio.run(adapter.close())


def test_search_body_common_names():
    adapter = JPLAdapter(config=JPLConfig())
    result = asyncio.run(adapter.search_body("moon"))
    assert result is not None
    assert result.identifier == "301"
    result = asyncio.run(adapter.search_body("luna"))
    assert result is not None
    assert result.identifier == "301"
    result = asyncio.run(adapter.search_body("jupiter"))
    assert result is not None
    assert result.identifier == "501"
    asyncio.run(adapter.close())


def test_get_ephemeris_placeholder():
    adapter = JPLAdapter(config=JPLConfig())
    # This would require a real API call to JPL Horizons
    # We just test that the method exists and doesn't crash
    result = asyncio.run(adapter.get_ephemeris(object_id="10", start_time=None, end_time=None))
    # Mock returns empty response, so result should be an empty list
    assert isinstance(result, list)
    asyncio.run(adapter.close())


def test_custom_config():
    config = JPLConfig(
        base_url="https://example.com/horizons",
        query_time=None,
        time_span_hours=12.0,
        step_size_hours=2.0,
        max_objects=10,
    )
    adapter = JPLAdapter(config=config)
    assert adapter.config.base_url == "https://example.com/horizons"
    assert adapter.config.time_span_hours == 12.0
    assert adapter.config.step_size_hours == 2.0
    asyncio.run(adapter.close())


def test_quota_error():
    # Test that quota errors are properly typed
    assert issubclass(JPLQuotaError, JPLError)


def test_request_error():
    # Test that request errors are properly typed
    assert issubclass(JPLRequestError, JPLError)


def test_connection_error():
    # Test that connection errors are properly typed
    assert issubclass(JPLConnectionError, JPLError)

