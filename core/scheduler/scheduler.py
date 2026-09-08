"""Scheduler — Background tasks, cron-like event triggers, and reminders.

Supports:
- Interval-based scheduling (seconds)
- Cron expressions (5-field: min hour day month weekday)
- Timezone-aware scheduling
- One-shot reminders at a specific datetime
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from zoneinfo import ZoneInfo

from core.bus.interface import EventBus
from core.ethan_types.event import Event, EventType

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_cron_field(field: str, min_val: int, max_val: int) -> list[int]:
    """Parse a single cron field into a sorted list of valid values."""
    values: set[int] = set()
    for part in field.split(","):
        try:
            if "/" in part:
                range_part, step_part = part.split("/", 1)
                step = int(step_part)
                if range_part == "*":
                    start, end = min_val, max_val
                elif "-" in range_part:
                    start, end = map(int, range_part.split("-", 1))
                else:
                    start = int(range_part)
                    end = max_val
                for v in range(start, end + 1, step):
                    values.add(v)
            elif "-" in part:
                start, end = map(int, part.split("-", 1))
                for v in range(start, end + 1):
                    values.add(v)
            elif part == "*":
                for v in range(min_val, max_val + 1):
                    values.add(v)
            else:
                values.add(int(part))
        except (ValueError, IndexError):
            continue
    return sorted(v for v in values if min_val <= v <= max_val)


def next_cron_occurrence(cron_expr: str, tz: str = "UTC") -> Optional[datetime]:
    """Calculate the next occurrence of a cron expression in the given timezone."""
    parts = cron_expr.strip().split()
    if len(parts) != 5:
        return None
    try:
        minutes = _parse_cron_field(parts[0], 0, 59)
        hours = _parse_cron_field(parts[1], 0, 23)
        days = _parse_cron_field(parts[2], 1, 31)
        months = _parse_cron_field(parts[3], 1, 12)
        weekdays = _parse_cron_field(parts[4], 0, 6)
    except (ValueError, IndexError):
        return None

    if not (minutes and hours and days and months and weekdays):
        return None

    try:
        zone = ZoneInfo(tz)
    except (KeyError, Exception):
        zone = ZoneInfo("UTC")

    now = _utc_now().astimezone(zone)
    candidate = now.replace(second=0, microsecond=0)

    for _ in range(366 * 24 * 60):  # Max ~1 year lookahead
        candidate = candidate.replace(minute=candidate.minute)  # Keep current minute
        if candidate.month not in months:
            # Move to next valid month
            next_months = [m for m in months if m > candidate.month]
            if next_months:
                candidate = candidate.replace(month=next_months[0], day=1, hour=0, minute=0)
            else:
                candidate = candidate.replace(year=candidate.year + 1, month=months[0], day=1, hour=0, minute=0)
            continue
        if candidate.day not in days or candidate.weekday() not in weekdays:
            candidate = candidate.replace(hour=0, minute=0)
            candidate = _next_candidate_day(candidate, days, weekdays)
            if candidate is None:
                return None
            continue
        if candidate.hour not in hours:
            next_hours = [h for h in hours if h > candidate.hour]
            if next_hours:
                candidate = candidate.replace(hour=next_hours[0], minute=0)
            else:
                candidate = _next_candidate_day(candidate, days, weekdays)
                if candidate is None:
                    return None
                candidate = candidate.replace(hour=hours[0], minute=0)
            continue
        if candidate.minute not in minutes:
            next_mins = [m for m in minutes if m > candidate.minute]
            if next_mins:
                candidate = candidate.replace(minute=next_mins[0])
            else:
                candidate = candidate.replace(hour=candidate.hour + 1, minute=0)
                if candidate.hour > 23:
                    candidate = _next_candidate_day(candidate, days, weekdays)
                    if candidate is None:
                        return None
                    candidate = candidate.replace(hour=0, minute=0)
            continue
        return candidate.astimezone(timezone.utc)
    return None


def _next_candidate_day(candidate: datetime, days: list[int], weekdays: list[int]) -> Optional[datetime]:
    """Find the next valid day from the candidate."""
    for offset in range(1, 366):
        next_day = candidate + __import__("datetime").timedelta(days=offset)
        if next_day.day in days and next_day.weekday() in weekdays:
            return next_day
    return None


class Scheduler:
    """Manages background tasks, cron triggers, and reminders."""

    def __init__(self, bus: EventBus):
        self.bus = bus
        self._running = False
        self._tasks: Dict[str, asyncio.Task] = {}
        self._cron_expressions: Dict[str, str] = {}
        self._timezones: Dict[str, str] = {}

    async def start(self) -> None:
        """Start the scheduler."""
        self._running = True
        logger.info("Scheduler started")

    async def stop(self) -> None:
        """Stop the scheduler and cancel all tasks."""
        self._running = False
        for name, task in list(self._tasks.items()):
            if not task.done():
                task.cancel()
        await asyncio.gather(*self._tasks.values(), return_exceptions=True)
        self._tasks.clear()
        self._cron_expressions.clear()
        self._timezones.clear()
        logger.info("Scheduler stopped")

    async def start(self) -> None:
        """Start scheduler loop."""
        self._running = True
        logger.info("Scheduler started")

    async def stop(self) -> None:
        """Stop all scheduled tasks."""
        self._running = False
        tasks = list(self._tasks.items())
        for name, task in tasks:
            task.cancel()
            logger.info(f"Cancelled scheduled task: {name}")
        self._tasks.clear()
        if tasks:
            results = await asyncio.gather(
                *(task for _, task in tasks), return_exceptions=True
            )
            for (name, _), result in zip(tasks, results):
                if isinstance(result, BaseException) and not isinstance(result, asyncio.CancelledError):
                    logger.error(
                        "Scheduled task failed during shutdown: %s",
                        name,
                        exc_info=(type(result), result, result.__traceback__),
                    )

    async def schedule_cron(
        self, name: str, interval_seconds: int, topic: str, payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Schedule a recurring event at a fixed interval."""
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be greater than zero")

        previous = self._tasks.get(name)
        if previous is not None and not previous.done():
            previous.cancel()
            await asyncio.gather(previous, return_exceptions=True)

        async def _loop():
            while self._running:
                await asyncio.sleep(interval_seconds)
                event = Event(
                    type=EventType.SCHEDULE_TRIGGER,
                    source=f"scheduler:{name}",
                    payload={"topic": topic, "payload": payload or {}},
                )
                await self.bus.publish(topic, event)
                logger.debug(f"Scheduled trigger: {name} → {topic}")

        task = asyncio.create_task(_loop(), name=name)
        self._tasks[name] = task
        task.add_done_callback(self._task_done)
        logger.info(f"Scheduled cron: {name} every {interval_seconds}s → {topic}")

    async def schedule_cron(
        self,
        name: str,
        cron_expr: str,
        topic: str,
        payload: Optional[Dict[str, Any]] = None,
        tz: str = "UTC",
    ) -> bool:
        """Schedule a recurring event using a cron expression.

        Args:
            name: Unique schedule identifier.
            cron_expr: 5-field cron expression (min hour day month weekday).
            topic: Event bus topic to publish to.
            payload: Optional event payload.
            tz: IANA timezone (e.g. 'America/New_York', 'Europe/Paris').
        """
        next_occurrence = next_cron_occurrence(cron_expr, tz)
        if next_occurrence is None:
            logger.error(f"Invalid cron expression: {cron_expr!r}")
            return False

        self._cron_expressions[name] = cron_expr
        self._timezones[name] = tz

        previous = self._tasks.get(name)
        if previous is not None and not previous.done():
            previous.cancel()
            await asyncio.gather(previous, return_exceptions=True)

        async def _loop():
            while self._running:
                next_fire = next_cron_occurrence(cron_expr, tz)
                if next_fire is None:
                    break
                now = _utc_now()
                wait_seconds = (next_fire - now).total_seconds()
                if wait_seconds > 0:
                    await asyncio.sleep(min(wait_seconds, 3600))
                    continue
                event = Event(
                    type=EventType.SCHEDULE_TRIGGER,
                    source=f"scheduler:cron:{name}",
                    payload={"topic": topic, "payload": payload or {}, "cron": cron_expr, "tz": tz},
                )
                await self.bus.publish(topic, event)
                logger.debug(f"Cron trigger: {name} ({cron_expr} {tz}) → {topic}")
                await asyncio.sleep(60)  # Avoid double-firing within the same minute

        task = asyncio.create_task(_loop(), name=name)
        self._tasks[name] = task
        task.add_done_callback(self._task_done)
        logger.info(f"Scheduled cron: {name} ({cron_expr} {tz}) → {topic}")
        return True

    async def schedule_once(
        self,
        name: str,
        fire_at: datetime,
        topic: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Schedule a one-shot reminder at a specific datetime."""
        now = _utc_now()
        if fire_at.tzinfo is None:
            fire_at = fire_at.replace(tzinfo=timezone.utc)
        wait_seconds = (fire_at.astimezone(timezone.utc) - now).total_seconds()

        if wait_seconds <= 0:
            logger.warning(f"Reminder {name} is in the past, firing immediately")

        previous = self._tasks.get(name)
        if previous is not None and not previous.done():
            previous.cancel()
            await asyncio.gather(previous, return_exceptions=True)

        async def _fire():
            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)
            event = Event(
                type=EventType.SCHEDULE_TRIGGER,
                source=f"scheduler:once:{name}",
                payload={"topic": topic, "payload": payload or {}, "fire_at": fire_at.isoformat()},
            )
            await self.bus.publish(topic, event)
            logger.info(f"One-shot reminder fired: {name} → {topic}")

        task = asyncio.create_task(_fire(), name=name)
        self._tasks[name] = task
        task.add_done_callback(self._task_done)
        logger.info(f"Scheduled one-shot: {name} at {fire_at.isoformat()} → {topic}")
        return True

    async def cancel(self, name: str) -> bool:
        """Cancel a scheduled task by name."""
        task = self._tasks.get(name)
        if task is None:
            return False
        if not task.done():
            task.cancel()
        self._cron_expressions.pop(name, None)
        self._timezones.pop(name, None)
        logger.info(f"Cancelled schedule: {name}")
        return True

    def get_schedule(self, name: str) -> Optional[Dict[str, Any]]:
        """Get schedule info (cron expression, timezone, next occurrence)."""
        task = self._tasks.get(name)
        if task is None:
            return None
        cron_expr = self._cron_expressions.get(name)
        tz = self._timezones.get(name, "UTC")
        next_occurrence = next_cron_occurrence(cron_expr, tz) if cron_expr else None
        return {
            "name": name,
            "cron": cron_expr,
            "timezone": tz,
            "next_occurrence": next_occurrence.isoformat() if next_occurrence else None,
            "running": not task.done(),
        }

    def list_schedules(self) -> list[Dict[str, Any]]:
        """List all active schedules."""
        return [
            self.get_schedule(name)
            for name in self._tasks
            if not self._tasks[name].done()
        ]

    def _task_done(self, task: asyncio.Task) -> None:
        """Consume task exceptions so failed schedules are observable."""
        if task.cancelled():
            return
        try:
            error = task.exception()
        except asyncio.CancelledError:
            return
        if error is not None:
            logger.error(
                "Scheduled task failed",
                exc_info=(type(error), error, error.__traceback__),
            )
