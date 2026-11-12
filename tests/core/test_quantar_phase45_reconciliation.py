import json
import subprocess
from pathlib import Path

import core.applications.quantar_service as qs
from core.applications.quantar_service import QuantarTaskService


def test_running_with_live_container_stays_running(monkeypatch, tmp_path) -> None:
    service = QuantarTaskService(workspace_root=tmp_path)
    task = service.create_task({"ticker": "NVDA", "analysis_date": "2026-09-01", "task_id": "t1"})
    with service._lock:
        service._tasks[task["task_id"]].status = "RUNNING"
        service._tasks[task["task_id"]].container_id = "cid-live"
        service._persist_task(service._tasks[task["task_id"]])
    monkeypatch.setattr(service, "_container_running", lambda cid: True)

    reconciled = service.reconcile_task(task["task_id"])
    assert reconciled["status"] == "RUNNING"


def test_running_with_missing_container_becomes_interrupted(monkeypatch, tmp_path) -> None:
    service = QuantarTaskService(workspace_root=tmp_path)
    task = service.create_task({"ticker": "NVDA", "analysis_date": "2026-09-01", "task_id": "t2"})
    with service._lock:
        service._tasks[task["task_id"]].status = "RUNNING"
        service._tasks[task["task_id"]].container_id = "cid-missing"
        service._persist_task(service._tasks[task["task_id"]])
    monkeypatch.setattr(service, "_container_running", lambda cid: False)
    monkeypatch.setattr(service, "_container_exit_code", lambda cid: None)

    reconciled = service.reconcile_task(task["task_id"])
    assert reconciled["status"] == "INTERRUPTED"
    assert reconciled["error_code"] == "execution_unconfirmed"


def test_completed_result_valid_stays_completed(tmp_path) -> None:
    service = QuantarTaskService(workspace_root=tmp_path)
    task = service.create_task({"ticker": "NVDA", "analysis_date": "2026-09-01", "task_id": "t3"})
    with service._lock:
        service._tasks[task["task_id"]].status = "COMPLETED"
        service._tasks[task["task_id"]].result = {"task_id": "t3", "decision": "HOLD"}
        service._persist_task(service._tasks[task["task_id"]])
    assert service.reconcile_task(task["task_id"])["status"] == "COMPLETED"


def test_completed_without_result_becomes_interrupted(monkeypatch, tmp_path) -> None:
    service = QuantarTaskService(workspace_root=tmp_path)
    task = service.create_task({"ticker": "NVDA", "analysis_date": "2026-09-01", "task_id": "t4"})
    with service._lock:
        service._tasks[task["task_id"]].status = "COMPLETED"
        service._tasks[task["task_id"]].result = None
        service._persist_task(service._tasks[task["task_id"]])
    monkeypatch.setattr(service, "_container_running", lambda cid: False)
    assert service.reconcile_task(task["task_id"])["status"] == "INTERRUPTED"


def test_mismatched_result_becomes_interrupted(monkeypatch, tmp_path) -> None:
    service = QuantarTaskService(workspace_root=tmp_path)
    task = service.create_task({"ticker": "NVDA", "analysis_date": "2026-09-01", "task_id": "t5"})
    with service._lock:
        service._tasks[task["task_id"]].status = "RUNNING"
        service._tasks[task["task_id"]].container_id = "cid"
        service._tasks[task["task_id"]].result = {"task_id": "other", "decision": "HOLD"}
        service._persist_task(service._tasks[task["task_id"]])
    monkeypatch.setattr(service, "_container_running", lambda cid: False)
    monkeypatch.setattr(service, "_container_exit_code", lambda cid: 0)
    assert service.reconcile_task(task["task_id"])["status"] == "INTERRUPTED"


def test_cancel_requested_confirmed_becomes_cancelled(monkeypatch, tmp_path) -> None:
    service = QuantarTaskService(workspace_root=tmp_path)
    task = service.create_task({"ticker": "NVDA", "analysis_date": "2026-09-01", "task_id": "t6"})
    with service._lock:
        service._tasks[task["task_id"]].status = "CANCEL_REQUESTED"
        service._tasks[task["task_id"]].cancelled = True
        service._tasks[task["task_id"]].cancellation_requested = True
        service._tasks[task["task_id"]].container_id = "cid"
        service._persist_task(service._tasks[task["task_id"]])
    monkeypatch.setattr(service, "_container_running", lambda cid: False)
    assert service.reconcile_task(task["task_id"])["status"] == "CANCELLED"
    assert service.get_task(task["task_id"])["cancellation_confirmed"] is True


def test_cancel_requested_unconfirmed_becomes_interrupted(monkeypatch, tmp_path) -> None:
    service = QuantarTaskService(workspace_root=tmp_path)
    task = service.create_task({"ticker": "NVDA", "analysis_date": "2026-09-01", "task_id": "t7"})
    with service._lock:
        service._tasks[task["task_id"]].status = "CANCEL_REQUESTED"
        service._tasks[task["task_id"]].cancelled = True
        service._tasks[task["task_id"]].cancellation_requested = True
        service._tasks[task["task_id"]].container_id = "cid-live"
        service._persist_task(service._tasks[task["task_id"]])
    monkeypatch.setattr(service, "_container_running", lambda cid: True)
    reconciled = service.reconcile_task(task["task_id"])
    assert reconciled["status"] == "INTERRUPTED"


def test_request_recovery_success(monkeypatch, tmp_path) -> None:
    service = QuantarTaskService(workspace_root=tmp_path)
    task = service.create_task({"ticker": "NVDA", "analysis_date": "2026-09-01", "task_id": "t8"})
    with service._lock:
        service._tasks[task["task_id"]].status = "INTERRUPTED"
        service._persist_task(service._tasks[task["task_id"]])
    monkeypatch.setattr(service, "_container_running", lambda cid: False)

    recovered = service.request_recovery(task["task_id"])
    assert recovered["status"] == "QUEUED"
    assert recovered["execution_id"] is not None


def test_request_recovery_refused_while_active(monkeypatch, tmp_path) -> None:
    service = QuantarTaskService(workspace_root=tmp_path)
    task = service.create_task({"ticker": "NVDA", "analysis_date": "2026-09-01", "task_id": "t9"})
    with service._lock:
        service._tasks[task["task_id"]].status = "INTERRUPTED"
        service._tasks[task["task_id"]].container_id = "cid-live"
        service._persist_task(service._tasks[task["task_id"]])
    monkeypatch.setattr(service, "_container_running", lambda cid: True)
    try:
        service.request_recovery(task["task_id"])
    except ValueError as exc:
        assert "active" in str(exc)
    else:
        raise AssertionError("expected refusal")


def test_request_recovery_idempotent(monkeypatch, tmp_path) -> None:
    service = QuantarTaskService(workspace_root=tmp_path)
    task = service.create_task({"ticker": "NVDA", "analysis_date": "2026-09-01", "task_id": "t10"})
    with service._lock:
        service._tasks[task["task_id"]].status = "INTERRUPTED"
        service._persist_task(service._tasks[task["task_id"]])
    monkeypatch.setattr(service, "_container_running", lambda cid: False)

    first = service.request_recovery(task["task_id"])
    second = service.request_recovery(task["task_id"])
    assert first["execution_id"] == second["execution_id"]
    assert second["status"] == "QUEUED"


def test_request_recovery_rejected_with_valid_result(monkeypatch, tmp_path) -> None:
    service = QuantarTaskService(workspace_root=tmp_path)
    task = service.create_task({"ticker": "NVDA", "analysis_date": "2026-09-01", "task_id": "t11"})
    with service._lock:
        service._tasks[task["task_id"]].status = "INTERRUPTED"
        service._tasks[task["task_id"]].result = {"task_id": "t11", "decision": "HOLD"}
        service._persist_task(service._tasks[task["task_id"]])
    monkeypatch.setattr(service, "_container_running", lambda cid: False)
    try:
        service.request_recovery(task["task_id"])
    except ValueError as exc:
        assert "valid result" in str(exc)
    else:
        raise AssertionError("expected refusal")


def test_repeated_reconciliation_is_stable(monkeypatch, tmp_path) -> None:
    service = QuantarTaskService(workspace_root=tmp_path)
    task = service.create_task({"ticker": "NVDA", "analysis_date": "2026-09-01", "task_id": "t12"})
    with service._lock:
        service._tasks[task["task_id"]].status = "RUNNING"
        service._tasks[task["task_id"]].container_id = "cid"
        service._persist_task(service._tasks[task["task_id"]])
    monkeypatch.setattr(service, "_container_running", lambda cid: False)
    monkeypatch.setattr(service, "_container_exit_code", lambda cid: 1)

    first = service.reconcile_task(task["task_id"])
    second = service.reconcile_task(task["task_id"])
    assert first["status"] == second["status"] == "FAILED"
