"""
Tests for the SIMBAD adapter.
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


from core.adapters.simbad import (
    SIMBADConfig,
    SIMBADAdapter,
    SIMBADRequestError,
    SIMBADConnectionError,
    SIMBADQuotaError,
    get_simbad_adapter,
)


@pytest.fixture
def simbad_config():
    return SIMBADConfig()


@pytest.fixture
def simbad_adapter(simbad_config):
    return SIMBADAdapter(config=simbad_config)


def test_get_simbad_adapter(simbad_config):
    adapter = get_simbad_adapter(config=simbad_config)
    assert adapter.config == simbad_config
    asyncio.run(adapter.close())


def test_simbad_adapter_creation(simbad_config):
    adapter = SIMBADAdapter(config=simbad_config)
    assert adapter.config == simbad_config
    assert adapter.http_timeout == 15.0
    asyncio.run(adapter.close())


def test_get_object():
    adapter = SIMBADAdapter(config=SIMBADConfig())
    result = asyncio.run(adapter.get_object("HD 209458"))
    assert result is None  # SIMBAD API not actually called, returns None
    asyncio.run(adapter.close())


def test_get_objects_by_coord():
    adapter = SIMBADAdapter(config=SIMBADConfig())
    result = asyncio.run(adapter.get_objects_by_coord(
        ra_deg=180.0,
        dec_deg=0.0,
        radius_arcmin=1.0,
    ))
    assert isinstance(result, list)
    asyncio.run(adapter.close())


def test_custom_config():
    config = SIMBADConfig(
        base_url="https://example.com/simbad",
        format="json",
        max_objects_per_query=100,
        timeout_seconds=30.0,
    )
    adapter = SIMBADAdapter(config=config)
    assert adapter.config.base_url == "https://example.com/simbad"
    assert adapter.config.format == "json"
    assert adapter.config.timeout_seconds == 30.0
    asyncio.run(adapter.close())


def test_error_hierarchy():
    from core.adapters.simbad import SIMBADError
    assert issubclass(SIMBADRequestError, SIMBADError)
    assert issubclass(SIMBADConnectionError, SIMBADError)
    assert issubclass(SIMBADQuotaError, SIMBADError)

