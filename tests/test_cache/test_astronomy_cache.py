"""
Tests for the astronomy cache (memory + disk + TTL).
"""

import asyncio
import os
import pytest


from core.cache.astronomy_cache import (
    CacheConfig,
    AstronomyCache,
    get_astronomy_cache,
)


@pytest.fixture
def cache_config(tmp_path):
    return CacheConfig(
        disk_dir=tmp_path / "astronomy_cache",
        memory_max_items=100,
        memory_ttl_seconds=300,
        disk_ttl_seconds=60,
        enable_disk=True,
        enable_memory=True,
    )


@pytest.fixture
def cache(cache_config):
    return AstronomyCache(config=cache_config)


@pytest.mark.asyncio
async def test_cache_set_and_get(cache):
    await cache.set("test_key", {"data": "test_value"}, ttl_seconds=60)
    result = await cache.get("test_key")
    assert result == {"data": "test_value"}


@pytest.mark.asyncio
async def test_cache_miss(cache):
    result = await cache.get("nonexistent_key")
    assert result is None


@pytest.mark.asyncio
async def test_cache_delete(cache):
    await cache.set("test_key", {"data": "test_value"}, ttl_seconds=60)
    await cache.delete("test_key")
    result = await cache.get("test_key")
    assert result is None


@pytest.mark.asyncio
async def test_cache_clear(cache):
    await cache.set("key1", {"data": "value1"}, ttl_seconds=60)
    await cache.set("key2", {"data": "value2"}, ttl_seconds=60)
    await cache.clear()
    assert await cache.get("key1") is None
    assert await cache.get("key2") is None


@pytest.mark.asyncio
async def test_cache_expiry(cache):
    """Test that expired entries are not returned."""
    await cache.set("expired_key", {"data": "value"}, ttl_seconds=0.01)
    # Small delay to let the TTL expire
    await asyncio.sleep(0.05)
    result = await cache.get("expired_key")
    assert result is None


@pytest.mark.asyncio
async def test_cache_memory_only_mode(cache_config, tmp_path):
    """Test that memory-only mode works without disk."""
    disk_free_config = CacheConfig(
        disk_dir=tmp_path / "astronomy_cache_no_disk",
        memory_max_items=100,
        memory_ttl_seconds=300,
        disk_ttl_seconds=60,
        enable_disk=False,  # create new instance instead of mutating frozen dataclass
        enable_memory=True,
    )
    cache = AstronomyCache(config=disk_free_config)
    await cache.set("test_key", {"data": "value"}, ttl_seconds=60)
    result = await cache.get("test_key")
    assert result == {"data": "value"}
    await cache.clear()


@pytest.mark.asyncio
async def test_cache_disk_files_creation(cache, tmp_path):
    """Test that disk files are created after setting values."""
    await cache.set("disk_test", {"data": "test_value"}, ttl_seconds=60)
    cache_dir = cache._disk_dir
    assert cache_dir.exists()
    assert any(cache_dir.glob("*.cache"))
    await cache.clear()
    assert not any(cache_dir.glob("*.cache"))


@pytest.mark.asyncio
async def test_get_astronomy_cache_factory(cache_config):
    """Test the factory function."""
    cache = get_astronomy_cache(config=cache_config)
    assert isinstance(cache, AstronomyCache)

