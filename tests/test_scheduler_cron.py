"""tests/test_scheduler_cron.py — Cron scheduling and timezone support."""

import pytest
from datetime import datetime, timezone, timedelta
from core.scheduler.scheduler import (
    next_cron_occurrence,
    _parse_cron_field,
)


class TestParseCronField:
    def test_star_returns_all(self):
        result = _parse_cron_field("*", 0, 59)
        assert result == list(range(0, 60))

    def test_single_value(self):
        result = _parse_cron_field("5", 0, 59)
        assert result == [5]

    def test_comma_separated(self):
        result = _parse_cron_field("1,5,10", 0, 59)
        assert result == [1, 5, 10]

    def test_range(self):
        result = _parse_cron_field("1-5", 0, 59)
        assert result == [1, 2, 3, 4, 5]

    def test_step(self):
        result = _parse_cron_field("*/15", 0, 59)
        assert result == [0, 15, 30, 45]

    def test_range_with_step(self):
        result = _parse_cron_field("1-10/2", 0, 59)
        assert result == [1, 3, 5, 7, 9]

    def test_invalid_returns_empty(self):
        result = _parse_cron_field("abc", 0, 59)
        assert result == []


class TestNextCronOccurrence:
    def test_valid_cron_returns_future(self):
        result = next_cron_occurrence("0 9 * * 1-5", "UTC")
        assert result is not None
        assert result > datetime.now(timezone.utc)

    def test_invalid_cron_returns_none(self):
        assert next_cron_occurrence("invalid", "UTC") is None

    def test_wrong_field_count_returns_none(self):
        assert next_cron_occurrence("0 9 * *", "UTC") is None

    def test_timezone_aware(self):
        result = next_cron_occurrence("0 9 * * *", "America/New_York")
        assert result is not None

    def test_invalid_timezone_falls_back_to_utc(self):
        result = next_cron_occurrence("0 9 * * *", "Invalid/Zone")
        assert result is not None

    def test_specific_minute(self):
        result = next_cron_occurrence("30 14 * * *", "UTC")
        assert result is not None
        assert result.minute == 30
        assert result.hour == 14


class TestSchedulerCron:
    @pytest.mark.asyncio
    async def test_schedule_cron_valid(self):
        from core.scheduler.scheduler import Scheduler
        from unittest.mock import AsyncMock

        bus = AsyncMock()
        scheduler = Scheduler(bus=bus)
        scheduler._running = True

        result = await scheduler.schedule_cron(
            name="test-cron",
            cron_expr="*/5 * * * *",
            topic="test.topic",
            tz="UTC",
        )
        assert result is True
        assert "test-cron" in scheduler._cron_expressions

    @pytest.mark.asyncio
    async def test_schedule_cron_invalid(self):
        from core.scheduler.scheduler import Scheduler
        from unittest.mock import AsyncMock

        bus = AsyncMock()
        scheduler = Scheduler(bus=bus)
        scheduler._running = True

        result = await scheduler.schedule_cron(
            name="test-cron",
            cron_expr="invalid",
            topic="test.topic",
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_cancel_schedule(self):
        from core.scheduler.scheduler import Scheduler
        from unittest.mock import AsyncMock

        bus = AsyncMock()
        scheduler = Scheduler(bus=bus)
        scheduler._running = True

        await scheduler.schedule_cron(
            name="test-cron",
            cron_expr="*/5 * * * *",
            topic="test.topic",
        )
        result = await scheduler.cancel("test-cron")
        assert result is True

    @pytest.mark.asyncio
    async def test_cancel_missing_returns_false(self):
        from core.scheduler.scheduler import Scheduler
        from unittest.mock import AsyncMock

        bus = AsyncMock()
        scheduler = Scheduler(bus=bus)
        result = await scheduler.cancel("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_schedule(self):
        from core.scheduler.scheduler import Scheduler
        from unittest.mock import AsyncMock

        bus = AsyncMock()
        scheduler = Scheduler(bus=bus)
        scheduler._running = True

        await scheduler.schedule_cron(
            name="test-cron",
            cron_expr="0 9 * * *",
            topic="test.topic",
            tz="America/New_York",
        )
        info = scheduler.get_schedule("test-cron")
        assert info is not None
        assert info["cron"] == "0 9 * * *"
        assert info["timezone"] == "America/New_York"
        assert info["next_occurrence"] is not None

    @pytest.mark.asyncio
    async def test_list_schedules(self):
        from core.scheduler.scheduler import Scheduler
        from unittest.mock import AsyncMock

        bus = AsyncMock()
        scheduler = Scheduler(bus=bus)
        scheduler._running = True

        await scheduler.schedule_cron(
            name="cron1",
            cron_expr="0 9 * * *",
            topic="test.topic",
        )
        await scheduler.schedule_cron(
            name="cron2",
            cron_expr="0 10 * * *",
            topic="test.topic",
        )
        schedules = scheduler.list_schedules()
        assert len(schedules) == 2
