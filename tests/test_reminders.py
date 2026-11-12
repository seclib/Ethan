"""tests/test_reminders.py — Core-owned reminder system."""

import pytest
from core.reminders import ReminderManager


@pytest.fixture
def reminder_manager():
    return ReminderManager()


@pytest.fixture
def reminder_manager_with_scheduler():
    """ReminderManager with a mocked scheduler."""
    scheduler = MockScheduler()
    return ReminderManager(scheduler=scheduler), scheduler


class MockScheduler:
    def __init__(self):
        self.scheduled = []
        self.cancelled = []

    async def schedule_cron(self, name, cron_expr, topic, payload=None, tz="UTC"):
        self.scheduled.append({"name": name, "cron": cron_expr, "topic": topic, "tz": tz})
        return True

    async def schedule_once(self, name, fire_at, topic, payload=None):
        self.scheduled.append({"name": name, "fire_at": fire_at, "topic": topic})
        return True

    async def cancel(self, name):
        self.cancelled.append(name)
        return True


@pytest.mark.asyncio
async def test_create_reminder_with_schedule(reminder_manager):
    reminder = await reminder_manager.create(
        title="Test Reminder",
        schedule="0 9 * * 1-5",
        timezone="America/New_York",
    )
    assert reminder["title"] == "Test Reminder"
    assert reminder["schedule"] == "0 9 * * 1-5"
    assert reminder["timezone"] == "America/New_York"
    assert reminder["enabled"] is True


@pytest.mark.asyncio
async def test_create_reminder_with_fire_at(reminder_manager):
    reminder = await reminder_manager.create(
        title="One Shot",
        fire_at="2025-12-25T09:00:00",
    )
    assert reminder["title"] == "One Shot"
    assert reminder["fire_at"] == "2025-12-25T09:00:00"


@pytest.mark.asyncio
async def test_create_reminder_requires_schedule_or_fire_at(reminder_manager):
    with pytest.raises(ValueError, match="Must specify either schedule or fire_at"):
        await reminder_manager.create(title="Invalid")


@pytest.mark.asyncio
async def test_create_reminder_rejects_both_schedule_and_fire_at(reminder_manager):
    with pytest.raises(ValueError, match="Cannot specify both"):
        await reminder_manager.create(
            title="Invalid",
            schedule="0 9 * * *",
            fire_at="2025-01-01T00:00:00",
        )


@pytest.mark.asyncio
async def test_get_reminder(reminder_manager):
    reminder = await reminder_manager.create(title="Test", schedule="0 9 * * *")
    fetched = await reminder_manager.get(reminder["id"])
    assert fetched is not None
    assert fetched["title"] == "Test"


@pytest.mark.asyncio
async def test_get_missing_reminder_returns_none(reminder_manager):
    assert await reminder_manager.get("nonexistent") is None


@pytest.mark.asyncio
async def test_list_reminders(reminder_manager):
    await reminder_manager.create(title="R1", schedule="0 9 * * *")
    await reminder_manager.create(title="R2", schedule="0 10 * * *")
    reminders = await reminder_manager.list()
    assert len(reminders) == 2


@pytest.mark.asyncio
async def test_list_reminders_filter_enabled(reminder_manager):
    r1 = await reminder_manager.create(title="R1", schedule="0 9 * * *", enabled=True)
    await reminder_manager.create(title="R2", schedule="0 10 * * *", enabled=False)
    enabled = await reminder_manager.list(enabled=True)
    assert len(enabled) == 1
    assert enabled[0]["id"] == r1["id"]


@pytest.mark.asyncio
async def test_update_reminder(reminder_manager):
    reminder = await reminder_manager.create(title="Old", schedule="0 9 * * *")
    updated = await reminder_manager.update(reminder["id"], {"title": "New"})
    assert updated["title"] == "New"


@pytest.mark.asyncio
async def test_delete_reminder(reminder_manager):
    reminder = await reminder_manager.create(title="To Delete", schedule="0 9 * * *")
    existed = await reminder_manager.delete(reminder["id"])
    assert existed is True
    assert await reminder_manager.get(reminder["id"]) is None


@pytest.mark.asyncio
async def test_delete_missing_returns_false(reminder_manager):
    assert await reminder_manager.delete("nonexistent") is False


@pytest.mark.asyncio
async def test_enable_reminder(reminder_manager):
    reminder = await reminder_manager.create(title="Test", schedule="0 9 * * *", enabled=False)
    enabled = await reminder_manager.enable(reminder["id"])
    assert enabled["enabled"] is True


@pytest.mark.asyncio
async def test_disable_reminder(reminder_manager):
    reminder = await reminder_manager.create(title="Test", schedule="0 9 * * *", enabled=True)
    disabled = await reminder_manager.disable(reminder["id"])
    assert disabled["enabled"] is False


@pytest.mark.asyncio
async def test_fire_reminder(reminder_manager):
    reminder = await reminder_manager.create(title="Test", schedule="0 9 * * *")
    fired = await reminder_manager.fire(reminder["id"])
    assert fired["fire_count"] == 1
    assert fired["last_fired_at"] is not None


@pytest.mark.asyncio
async def test_scheduler_called_on_create(reminder_manager_with_scheduler):
    manager, scheduler = reminder_manager_with_scheduler
    reminder = await manager.create(title="Test", schedule="0 9 * * *")
    assert len(scheduler.scheduled) == 1
    assert scheduler.scheduled[0]["name"] == f"reminder-{reminder['id']}"


@pytest.mark.asyncio
async def test_scheduler_cancelled_on_delete(reminder_manager_with_scheduler):
    manager, scheduler = reminder_manager_with_scheduler
    reminder = await manager.create(title="Test", schedule="0 9 * * *")
    await manager.delete(reminder["id"])
    assert f"reminder-{reminder['id']}" in scheduler.cancelled
