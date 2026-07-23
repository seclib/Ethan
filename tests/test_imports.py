import pytest


def test_core_import():
    import core  # noqa: F401


def test_core_kernel_import():
    from core.kernel import CognitiveKernel  # noqa: F401


def test_sdk_event_import():
    from sdk.event import EventType  # noqa: F401


def test_nats_py_import():
    import nats  # noqa: F401


def test_psutil_import():
    import psutil  # noqa: F401


def test_asyncpg_import():
    import asyncpg  # noqa: F401


def test_redis_import():
    import redis  # noqa: F401