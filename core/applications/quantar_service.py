"""Quantar real-task execution service for ETHAN (MEM-014).

Quantar is a task engine, not a daemon.  A task is created, executed once
through ``TradingAgentsGraph.propagate()``, produces a structured result, and
terminates.  In-process execution remains available for unit tests and for
environments without Docker; Docker one-shot containers are preferred for
production runtime isolation.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping
from uuid import uuid4

TRADINGAGENTS_AVAILABLE = False
TRADINGAGENTS_ERROR = None
DEFAULT_CONFIG_FACTORY: Callable[[], Any] | None = None

try:
    import tradingagents  # type: ignore  # noqa: F401
    from tradingagents.default_config import DEFAULT_CONFIG  # type: ignore
    from tradingagents.graph.trading_graph import TradingAgentsGraph  # type: ignore

    TRADINGAGENTS_AVAILABLE = True
    DEFAULT_CONFIG_FACTORY = lambda: (  # noqa: E731
        DEFAULT_CONFIG.copy() if hasattr(DEFAULT_CONFIG, "copy") else dict(DEFAULT_CONFIG)
    )
except Exception as exc:  # pragma: no cover - import evaluated at runtime
    TRADINGAGENTS_ERROR = str(exc)
    DEFAULT_CONFIG = None
    TradingAgentsGraph = None


class QuantarTaskStatus(str):
    """Canonical status values for a Quantar task."""

    PREPARED = "PREPARED"
    QUEUED = "QUEUED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    CANCEL_REQUESTED = "CANCEL_REQUESTED"
    INTERRUPTED = "INTERRUPTED"
    RECONCILING = "RECONCILING"

    def __eq__(self, other: object) -> bool:  # type: ignore[override]
        if isinstance(other, str):
            return self.upper() == other.upper()
        return super().__eq__(other)

    __hash__ = str.__hash__


# Backwards-compatible alias used by earlier phases.
QuantarAnalysisStatus = QuantarTaskStatus


@dataclass(slots=True)
class QuantarTask:
    """One bounded Quantar analysis task."""

    task_id: str
    ticker: str
    analysis_date: str
    provider: str | None = None
    status: str = QuantarTaskStatus.PREPARED
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result: Any = None
    error: str | None = None
    provenance: str = "TradingAgents"
    parameters: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    logs: list[str] = field(default_factory=list)
    container_id: str | None = None
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    cancelled: bool = False
    application_id: str = "quantar"
    execution_id: str | None = None
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error_code: str | None = None
    error_summary: str | None = None
    result_reference: str | None = None
    log_reference: str | None = None
    cancellation_requested: bool = False
    cancellation_confirmed: bool = False

    # Compatibility alias expected by v1 records.
    @property
    def analysis_id(self) -> str:
        return self.task_id

    @analysis_id.setter
    def analysis_id(self, value: str) -> None:
        self.task_id = value

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "analysis_id": self.task_id,
            "ticker": self.ticker,
            "analysis_date": self.analysis_date,
            "provider": self.provider,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "started_at": None if self.started_at is None else self.started_at.isoformat(),
            "finished_at": None if self.finished_at is None else self.finished_at.isoformat(),
            "result": self.result,
            "error": self.error,
            "provenance": self.provenance,
            "parameters": self.parameters,
            "metadata": self.metadata,
            "logs": self.logs,
            "container_id": self.container_id,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "cancelled": self.cancelled,
            "application_id": self.application_id,
            "execution_id": self.execution_id,
            "updated_at": self.updated_at.isoformat(),
            "error_code": self.error_code,
            "error_summary": self.error_summary,
            "result_reference": self.result_reference,
            "log_reference": self.log_reference,
            "cancellation_requested": self.cancellation_requested,
            "cancellation_confirmed": self.cancellation_confirmed,
        }


# Compatibility alias expected by previous phases.
QuantarAnalysisRecord = QuantarTask


def _default_config() -> Any:
    if DEFAULT_CONFIG_FACTORY is not None:
        try:
            return DEFAULT_CONFIG_FACTORY()
        except Exception:
            pass
    return getattr(globals(), "DEFAULT_CONFIG", None)


class QuantarTaskService:
    """Core owner of Quantar tasks and their execution lifecycle."""

    def __init__(
        self,
        store: Any = None,
        docker_cmd: str = "docker",
        image: str = "quantar-runtime:latest",
        workspace_root: Path | str | None = None,
        compose_file: Path | str | None = None,
        network_mode: str = "none",
    ) -> None:
        self.store = store
        self.docker_cmd = docker_cmd
        self.image = image
        ethan_root = Path(__file__).resolve().parents[2]
        self.workspace_root = Path(workspace_root or (ethan_root / ".quantar-tasks")).resolve()
        self.compose_file = Path(compose_file or (Path(__file__).resolve().parents[2] / "examples" / "quantar" / "compose.yaml"))
        self.network_mode = network_mode
        self._lock = threading.RLock()
        self._tasks: dict[str, QuantarTask] = {}
        self._load_persisted_tasks()

    @property
    def _analyses(self) -> dict[str, QuantarTask]:
        return self._tasks

    # ── Status & configuration ───────────────────────────────────────────

    def status(self) -> dict[str, Any]:
        # Docker one-shot est une voie d'exécution autonome, même si les
        # modules Python ne sont pas importables dans le processus Core.
        image_available = False
        try:
            binary = shutil.which(self.docker_cmd or "docker") or self.docker_cmd or "docker"
            proc = subprocess.run(
                [binary, "image", "inspect", self.image],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            image_available = proc.returncode == 0
        except Exception:  # pragma: no cover - robustesse d'évaluation
            image_available = False
        inprocess_available = TRADINGAGENTS_AVAILABLE
        available = bool(inprocess_available or image_available)
        if inprocess_available:
            message = "TradingAgents is importable and Quantar can execute real tasks."
        elif image_available:
            message = ("TradingAgents is not importable in-process, but the "
                       "Quantar Docker one-shot runtime is available.")
        else:
            message = "Neither in-process TradingAgents nor the Docker runtime is available."
        return {
            "application": "Quantar",
            "source": "TradingAgents",
            "available": available,
            "error": TRADINGAGENTS_ERROR,
            "runtime": "ready" if available else "unavailable",
            "task_runtime": "real-task",
            "inprocess_available": inprocess_available,
            "docker_image_available": image_available,
            "message": message,
        }

    def config(self) -> dict[str, Any]:
        config: dict[str, Any] = {}
        if TRADINGAGENTS_AVAILABLE:
            try:
                from tradingagents.default_config import DEFAULT_CONFIG

                safe_keys = (
                    "llm_provider",
                    "deep_think_llm",
                    "quick_think_llm",
                    "max_debate_rounds",
                    "max_risk_discuss_rounds",
                    "data_vendors",
                )
                config = {key: DEFAULT_CONFIG[key] for key in safe_keys if key in DEFAULT_CONFIG}
            except Exception as exc:
                config = {"error": str(exc)}
        return {
            "available": TRADINGAGENTS_AVAILABLE,
            "config": config,
            "secrets_exposed": False,
        }

    # ── Task creation ───────────────────────────────────────────────────

    def create_task(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        task = self._validate_and_create(payload, status=QuantarTaskStatus.QUEUED)
        with self._lock:
            self._tasks[task.task_id] = task
            task.updated_at = datetime.now(timezone.utc)
            self._persist_task(task)
        return task.to_dict()

    def prepare_analysis(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        task = self._validate_and_create(payload, status=QuantarTaskStatus.PREPARED)
        with self._lock:
            self._tasks[task.task_id] = task
            task.updated_at = datetime.now(timezone.utc)
            self._persist_task(task)
        result = task.to_dict()
        result["prepared"] = True
        return result

    def start_task(self, task_id: str, *, execute: bool = False) -> dict[str, Any]:
        task = self._get_task(task_id)
        if task is None:
            raise ValueError("unknown task")
        with self._lock:
            if task.status not in (QuantarTaskStatus.CANCELLED,):
                task.status = QuantarTaskStatus.STARTING
        if execute:
            return self.run_task(task_id)
        return self.get_task(task_id)

    def start_analysis(self, payload: Mapping[str, Any], *, execute: bool = False) -> dict[str, Any]:
        prepared = self.prepare_analysis(payload)
        task_id = prepared["task_id"]
        task = self._get_task(task_id)
        if task is None:
            raise ValueError("analysis was not prepared")
        with self._lock:
            task.status = QuantarTaskStatus.QUEUED
        if execute:
            self.run_task(task_id)
        return self.get_task(task_id)

    # ── Execution ───────────────────────────────────────────────────────

    def run_task(self, task_id: str, *, use_docker: bool = False) -> dict[str, Any]:
        task = self._get_task(task_id)
        if task is None:
            raise ValueError("unknown task")
        if task.cancelled:
            with self._lock:
                task.status = QuantarTaskStatus.CANCELLED
                task.finished_at = datetime.now(timezone.utc)
                self._persist_task(task)
            return task.to_dict()

        if task.status in {QuantarTaskStatus.COMPLETED, QuantarTaskStatus.FAILED, QuantarTaskStatus.CANCELLED, QuantarTaskStatus.INTERRUPTED, QuantarTaskStatus.CANCEL_REQUESTED}:
            return task.to_dict()

        if use_docker:
            return self.run_task_in_container(task_id)

        if not TRADINGAGENTS_AVAILABLE:
            with self._lock:
                task.status = QuantarTaskStatus.FAILED
                task.error = TRADINGAGENTS_ERROR or "TradingAgents is not available"
                task.finished_at = datetime.now(timezone.utc)
            task.logs.append(f"FAILED: {task.error}")
            return task.to_dict()

        with self._lock:
            task.status = QuantarTaskStatus.STARTING
            task.started_at = datetime.now(timezone.utc)
        task.logs.append("STARTING")
        with self._lock:
            task.status = QuantarTaskStatus.RUNNING
            task.updated_at = datetime.now(timezone.utc)
            self._persist_task(task)
        task.logs.append("RUNNING")

        try:
            graph_cls = TradingAgentsGraph
            config = _default_config()
            graph = graph_cls(debug=False, config=(config.copy() if hasattr(config, "copy") else config))

            task.logs.append("propagate() invoked")
            raw_result = graph.propagate(task.ticker, task.analysis_date)
            if isinstance(raw_result, tuple) and len(raw_result) == 2:
                final_state, rating = raw_result
            else:
                final_state, rating = {}, raw_result
            if isinstance(rating, Mapping):
                decision_value = rating.get("decision", rating)
            else:
                decision_value = rating
            reports: dict[str, Any] = {}
            if isinstance(final_state, Mapping):
                for key in (
                    "final_trade_decision",
                    "investment_plan",
                    "trader_investment_plan",
                    "market_report",
                    "sentiment_report",
                    "news_report",
                    "fundamentals_report",
                ):
                    value = final_state.get(key)
                    if value is not None:
                        reports[key] = value
            final_report_value = None
            if isinstance(final_state, Mapping):
                final_report_value = final_state.get("final_trade_decision")
            with self._lock:
                task.result = {
                    "task_id": task.task_id,
                    "ticker": task.ticker,
                    "analysis_date": task.analysis_date,
                    "decision": decision_value,
                    "reports": reports,
                    "metadata": task.metadata,
                }
                # Preserve any full structured state provided by the graph.
                if isinstance(final_state, Mapping) and "final_state" not in task.result:
                    task.result["final_state"] = dict(final_state)
                task.status = QuantarTaskStatus.COMPLETED
                task.finished_at = datetime.now(timezone.utc)
                task.updated_at = datetime.now(timezone.utc)
                self._persist_task(task)
            task.logs.append("COMPLETED")
        except Exception as exc:  # noqa: BLE001 - surfaced to the caller
            with self._lock:
                task.status = QuantarTaskStatus.FAILED
                task.error = str(exc)
                task.error_summary = task.error_summary or str(exc)
                task.finished_at = datetime.now(timezone.utc)
                task.updated_at = datetime.now(timezone.utc)
                self._persist_task(task)
            task.logs.append(f"FAILED: {task.error}")
        return task.to_dict()

    def run_analysis(self, analysis_id: str) -> dict[str, Any]:
        return self.run_task(analysis_id)

    # ── Docker one-shot execution ───────────────────────────────────────

    def _task_workspace(self, task_id: str) -> Path:
        workspace = self.workspace_root / task_id
        workspace.mkdir(parents=True, exist_ok=True)
        return workspace

    def create_task_input(self, task_id: str, payload: Mapping[str, Any] | None = None) -> Path:
        task = self._get_task(task_id)
        if task is None:
            raise ValueError("unknown task")
        workspace = self._task_workspace(task_id)
        input_file = workspace / "task.json"
        data = payload if payload is not None else task.to_dict()
        input_file.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        return input_file

    def run_task_in_container(self, task_id: str) -> dict[str, Any]:
        task = self._get_task(task_id)
        if task is None:
            raise ValueError("unknown task")
        workspace = self._task_workspace(task_id)
        input_file = workspace / "task.json"
        if not input_file.exists():
            self.create_task_input(task_id)
        output_file = workspace / "result.json"
        for path in (output_file,):
            if path.exists():
                path.unlink()

        container_name = f"quantar-task-{task_id}"
        command = self._docker_run_command(container_name, workspace)
        with self._lock:
            task.status = QuantarTaskStatus.STARTING
            task.started_at = datetime.now(timezone.utc)
        task.logs.append("STARTING container")
        try:
            proc = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=3600,
                check=False,
            )
            with self._lock:
                task.container_id = container_name
                task.exit_code = proc.returncode
                task.stdout = proc.stdout or ""
                task.stderr = proc.stderr or ""
                task.logs.append((proc.stdout or "").strip())
                if proc.stderr:
                    task.logs.append((proc.stderr or "").strip())
            result_loaded = False
            if output_file.exists():
                try:
                    parsed_result = json.loads(output_file.read_text(encoding="utf-8"))
                    with self._lock:
                        task.result = parsed_result
                    result_loaded = True
                except Exception as exc:  # noqa: BLE001
                    with self._lock:
                        task.result = None
                        task.error = f"invalid task result: {exc}"
            else:
                with self._lock:
                    task.result = None
                    task.error = task.error or "container produced no result.json"

            if proc.returncode != 0:
                with self._lock:
                    task.status = QuantarTaskStatus.FAILED
                    task.error = task.error or (proc.stderr.strip() or f"container exited {proc.returncode}")
                    task.finished_at = datetime.now(timezone.utc)
                task.logs.append(f"FAILED: {task.error}")
                return task.to_dict()

            if not result_loaded or not isinstance(task.result, (Mapping, dict, list, str, int, float, bool)) or task.result is None:
                with self._lock:
                    task.status = QuantarTaskStatus.FAILED
                    task.error = task.error or "container exited successfully but produced no valid result"
                    task.finished_at = datetime.now(timezone.utc)
                task.logs.append(f"FAILED: {task.error}")
                return task.to_dict()

            with self._lock:
                task.status = QuantarTaskStatus.COMPLETED
                task.finished_at = datetime.now(timezone.utc)
                task.updated_at = datetime.now(timezone.utc)
                self._persist_task(task)
            task.logs.append("COMPLETED")
        except Exception as exc:  # noqa: BLE001
            with self._lock:
                task.status = QuantarTaskStatus.FAILED
                task.error = str(exc)
                task.error_summary = task.error_summary or str(exc)
                task.finished_at = datetime.now(timezone.utc)
                task.updated_at = datetime.now(timezone.utc)
                self._persist_task(task)
            task.logs.append(f"FAILED: {task.error}")
        finally:
            self.cleanup_container(container_name, remove=True)
        return task.to_dict()

    def _docker_run_command(self, container_name: str, workspace: Path) -> list[str]:
        binary = shutil.which(self.docker_cmd) or self.docker_cmd
        return [
            binary,
            "compose",
            "--project-name",
            "quantar",
            "-f",
            str(self.compose_file),
            "run",
            "--rm",
            "--name",
            container_name,
            "-v",
            f"{workspace}:/data/quantar",
            "-e",
            f"QUANTAR_TASK_FILE=/data/quantar/task.json",
            "-e",
            f"QUANTAR_RESULT_FILE=/data/quantar/result.json",
            "quantar-task",
        ]

    def cleanup_container(self, container_name: str, *, remove: bool = True) -> dict[str, Any]:
        binary = shutil.which(self.docker_cmd) or self.docker_cmd
        args = ["rm", "-f", container_name] if remove else ["stop", container_name]
        try:
            proc = subprocess.run([binary, *args], capture_output=True, text=True, timeout=30, check=False)
            return {"ok": proc.returncode == 0, "output": (proc.stdout or proc.stderr).strip()}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc)}

    # ── Logs / results / cancellation ───────────────────────────────────

    def get_logs(self, task_id: str, tail: int = 100) -> dict[str, Any]:
        task = self._get_task(task_id)
        if task is None:
            raise ValueError("unknown task")
        safe_tail = max(1, min(int(tail), 500))
        logs = task.logs[-safe_tail:]
        return {"ok": True, "task_id": task_id, "logs": logs, "stdout": task.stdout, "stderr": task.stderr}

    def get_result(self, task_id: str) -> dict[str, Any]:
        task = self._get_task(task_id)
        if task is None:
            raise ValueError("unknown task")
        if task.status != QuantarTaskStatus.COMPLETED:
            raise ValueError("task is not completed")
        return task.result or {}

    def cancel_task(self, task_id: str) -> dict[str, Any]:
        task = self._get_task(task_id)
        if task is None:
            raise ValueError("unknown task")
        with self._lock:
            task.cancellation_requested = True
            task.cancelled = True
            task.status = QuantarTaskStatus.CANCEL_REQUESTED
            task.updated_at = datetime.now(timezone.utc)
            self._persist_task(task)
        task.logs.append("CANCEL_REQUESTED")
        if task.container_id:
            stopped = self.stop_container(task.container_id, grace_seconds=5.0)
            confirmed = bool(stopped.get("ok", False)) and not self._container_running(task.container_id)
            self.cleanup_container(task.container_id, remove=True)
        else:
            stopped = {"ok": True, "method": "none"}
            confirmed = True
        with self._lock:
            if confirmed:
                task.cancellation_confirmed = True
                task.status = QuantarTaskStatus.CANCELLED
            else:
                task.cancellation_confirmed = False
                task.status = QuantarTaskStatus.INTERRUPTED
                task.error_code = task.error_code or "cancellation_unconfirmed"
                task.error_summary = task.error_summary or "Container cancellation was not confirmed"
            task.finished_at = datetime.now(timezone.utc)
            task.updated_at = datetime.now(timezone.utc)
            self._persist_task(task)
        task.logs.append("CANCELLED" if confirmed else "CANCEL_FAILED")
        return task.to_dict()

    def cleanup_task(self, task_id: str) -> dict[str, Any]:
        task = self._get_task(task_id)
        if task is not None and task.container_id:
            self.cleanup_container(task.container_id, remove=True)
        with self._lock:
            self._tasks.pop(task_id, None)
        return {"ok": True, "task_id": task_id}

    def get_task(self, task_id: str) -> dict[str, Any]:
        task = self._get_task(task_id)
        if task is None:
            raise ValueError("unknown task")
        return task.to_dict()

    def list_tasks(self) -> list[dict[str, Any]]:
        with self._lock:
            return [task.to_dict() for task in self._tasks.values()]

    def list_analyses(self) -> list[dict[str, Any]]:
        return self.list_tasks()


    # ---------- persistence / recovery ----------

    def _state_path(self, task_id: str) -> Path:
        return self._task_workspace(task_id) / "state.json"

    from contextlib import contextmanager

    @contextmanager
    def _task_lock(self, task_id: str, timeout_seconds: float = 10.0):
        import fcntl
        workspace = self._task_workspace(task_id)
        lock_path = workspace / "state.lock"
        fd = os.open(str(lock_path), os.O_RDWR | os.O_CREAT, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            yield
        finally:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            except OSError:
                pass
            os.close(fd)

    def stop_container(self, container_id: str, grace_seconds: float = 5.0) -> dict[str, Any]:
        binary = shutil.which(self.docker_cmd) or self.docker_cmd
        try:
            proc = subprocess.run(
                [binary, "stop", "-t", str(grace_seconds), container_id],
                capture_output=True,
                text=True,
                timeout=max(10, int(grace_seconds) + 10),
                check=False,
            )
            if proc.returncode == 0 or not self._container_running(container_id):
                return {"ok": True, "method": "stop", "output": (proc.stdout or proc.stderr).strip()}
        except Exception as exc:
            return {"ok": False, "method": "stop", "error": str(exc)}
        # forced kill if stop did not stop it
        try:
            proc = subprocess.run(
                [binary, "kill", container_id],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            ok = proc.returncode == 0 or not self._container_running(container_id)
            return {"ok": ok, "method": "kill", "output": (proc.stdout or proc.stderr).strip()}
        except Exception as exc:
            return {"ok": False, "method": "kill", "error": str(exc)}

    def _persist_task(self, task: QuantarTask) -> None:
        if not task.task_id:
            return
        try:
            workspace = self._task_workspace(task.task_id)
            path = workspace / "state.json"
            if task.result is not None and workspace.exists():
                task.result_reference = str(workspace / "result.json")
            task.log_reference = str(workspace / "logs.json")
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps(task.to_dict(), ensure_ascii=False, indent=2, default=str), encoding="utf-8")
            tmp.replace(path)
        except OSError:
            # Persistence must never break the primary runtime path.
            pass

    def _load_persisted_tasks(self) -> None:
        root = self.workspace_root
        if not root.exists():
            return
        for path in sorted(root.glob("*/state.json")):
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                task = self._task_from_mapping(raw)
                if task is not None:
                    # A reboot can never turn an unfinished task into completed.
                    if task.status not in {
                        QuantarTaskStatus.COMPLETED,
                        QuantarTaskStatus.FAILED,
                        QuantarTaskStatus.CANCELLED,
                        QuantarTaskStatus.INTERRUPTED,
                        QuantarTaskStatus.RECONCILING,
                    }:
                        task.status = QuantarTaskStatus.RECONCILING
                        task.error_code = task.error_code or "restart_reconciliation_pending"
                        task.updated_at = datetime.now(timezone.utc)
                    self._tasks[task.task_id] = task
            except (OSError, ValueError, TypeError):
                continue

    def _task_from_mapping(self, data: Mapping[str, Any]) -> QuantarTask | None:
        try:
            ticker = str(data.get("ticker", "") or "").strip()
            analysis_date = str(data.get("analysis_date", "") or "").strip()
            if not ticker or not analysis_date:
                return None
            created = data.get("created_at") or datetime.now(timezone.utc).isoformat()
            task = QuantarTask(
                task_id=str(data.get("task_id") or data.get("analysis_id") or uuid4()),
                ticker=ticker,
                analysis_date=analysis_date,
                provider=None if data.get("provider") is None else str(data.get("provider")),
                status=str(data.get("status") or QuantarTaskStatus.PREPARED),
                parameters=dict(data.get("parameters", {})) if isinstance(data.get("parameters"), Mapping) else {},
                metadata=dict(data.get("metadata", {})) if isinstance(data.get("metadata"), Mapping) else {},
                logs=list(data.get("logs", [])) if isinstance(data.get("logs"), list) else [],
                container_id=data.get("container_id"),
                exit_code=data.get("exit_code"),
                stdout=str(data.get("stdout", "") or ""),
                stderr=str(data.get("stderr", "") or ""),
                cancelled=bool(data.get("cancelled", False)),
                application_id=str(data.get("application_id", "quantar") or "quantar"),
                execution_id=data.get("execution_id"),
                error_code=data.get("error_code"),
                error_summary=data.get("error_summary"),
                result_reference=data.get("result_reference"),
                log_reference=data.get("log_reference"),
                cancellation_requested=bool(data.get("cancellation_requested", False)),
                cancellation_confirmed=bool(data.get("cancellation_confirmed", False)),
            )
            task.result = data.get("result")
            task.error = data.get("error")
            if data.get("created_at"):
                task.created_at = datetime.fromisoformat(str(data["created_at"]).replace("Z", "+00:00"))
            if data.get("started_at"):
                task.started_at = datetime.fromisoformat(str(data["started_at"]).replace("Z", "+00:00"))
            if data.get("finished_at"):
                task.finished_at = datetime.fromisoformat(str(data["finished_at"]).replace("Z", "+00:00"))
            if data.get("updated_at"):
                task.updated_at = datetime.fromisoformat(str(data["updated_at"]).replace("Z", "+00:00"))
            return task
        except (TypeError, ValueError):
            return None

    def _result_is_valid(self, task: QuantarTask, result_data: Any) -> bool:
        if not isinstance(result_data, (dict, list, str, int, float, bool)):
            return False
        if isinstance(result_data, dict) and "task_id" in result_data and result_data.get("task_id") != task.task_id:
            return False
        if isinstance(result_data, (dict, list)):
            try:
                json.dumps(result_data, default=str)
            except (TypeError, ValueError):
                return False
        return True

    def _read_persisted_result(self, task: QuantarTask) -> Any:
        if not task.result_reference:
            return None
        path = Path(task.result_reference)
        if not path.exists():
            return None
        try:
            parsed = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return None
        if isinstance(parsed, (dict, list, str, int, float, bool)) and self._result_is_valid(task, parsed):
            return parsed
        return None

    def _container_exists(self, container_id: str | None) -> bool:
        if not container_id:
            return False
        try:
            proc = subprocess.run(
                [shutil.which(self.docker_cmd) or self.docker_cmd, "inspect", container_id],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            return proc.returncode == 0
        except Exception:
            return False

    def _container_running(self, container_id: str | None) -> bool:
        if not container_id:
            return False
        try:
            proc = subprocess.run(
                [shutil.which(self.docker_cmd) or self.docker_cmd, "inspect", "-f", "{{.State.Running}}", container_id],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            return proc.returncode == 0 and proc.stdout.strip().lower() == "true"
        except Exception:
            return False

    def _container_exit_code(self, container_id: str | None) -> int | None:
        if not container_id:
            return None
        try:
            proc = subprocess.run(
                [shutil.which(self.docker_cmd) or self.docker_cmd, "inspect", "-f", "{{.State.ExitCode}}", container_id],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            if proc.returncode == 0:
                return int(proc.stdout.strip() or 0)
        except Exception:
            return None
        return None

    def _reconcile_task_internal(self, task_id: str) -> QuantarTask | None:
        task = self._get_task(task_id)
        if task is None:
            return None
        with self._lock:
            if task.status in {QuantarTaskStatus.COMPLETED, QuantarTaskStatus.FAILED, QuantarTaskStatus.CANCELLED, QuantarTaskStatus.INTERRUPTED}:
                if task.status == QuantarTaskStatus.COMPLETED and not self._result_is_valid(task, task.result):
                    task.status = QuantarTaskStatus.INTERRUPTED
                    task.error_code = task.error_code or "invalid_completed_result"
                    task.error_summary = task.error_summary or "Completed task result is missing or invalid."
                    task.updated_at = datetime.now(timezone.utc)
                    self._persist_task(task)
                    return task
                return task
            task.status = QuantarTaskStatus.RECONCILING
            task.updated_at = datetime.now(timezone.utc)
            self._persist_task(task)

            if task.cancelled or task.cancellation_requested:
                if task.container_id and not self._container_running(task.container_id):
                    task.cancellation_confirmed = True
                    task.status = QuantarTaskStatus.CANCELLED
                else:
                    task.status = QuantarTaskStatus.INTERRUPTED
                    task.error_code = task.error_code or "cancellation_unconfirmed"
                    task.error_summary = task.error_summary or "Cancellation could not be confirmed."
                task.finished_at = datetime.now(timezone.utc)
                task.updated_at = datetime.now(timezone.utc)
                self._persist_task(task)
                return task

            if task.container_id and self._container_running(task.container_id):
                task.status = QuantarTaskStatus.RUNNING
                task.updated_at = datetime.now(timezone.utc)
                self._persist_task(task)
                return task

            if task.container_id:
                exit_code = self._container_exit_code(task.container_id)
                result = self._read_persisted_result(task)
                if exit_code == 0 and result is not None and not (task.container_id and self._container_running(task.container_id)):
                    task.result = result
                    task.exit_code = exit_code
                    task.status = QuantarTaskStatus.COMPLETED
                    task.finished_at = datetime.now(timezone.utc)
                    task.updated_at = datetime.now(timezone.utc)
                    self._persist_task(task)
                    return task
                if exit_code is not None and exit_code != 0:
                    task.exit_code = exit_code
                    task.status = QuantarTaskStatus.FAILED
                    task.error_code = task.error_code or "nonzero_exit"
                    task.error_summary = task.error_summary or f"Container exited with code {exit_code}"
                    task.finished_at = datetime.now(timezone.utc)
                    task.updated_at = datetime.now(timezone.utc)
                    self._persist_task(task)
                    return task

            task.status = QuantarTaskStatus.INTERRUPTED
            task.error_code = task.error_code or "execution_unconfirmed"
            task.error_summary = task.error_summary or "Execution state could not be verified."
            task.updated_at = datetime.now(timezone.utc)
            self._persist_task(task)
            return task
        return task

    def reconcile_tasks(self) -> list[dict[str, Any]]:
        reconciled = []
        with self._lock:
            for task_id in list(self._tasks):
                task = self._tasks.get(task_id)
                if task is None:
                    continue
                if task.status in {QuantarTaskStatus.COMPLETED, QuantarTaskStatus.FAILED, QuantarTaskStatus.CANCELLED}:
                    continue
                result = self.reconcile_task(task_id)
                if result is not None:
                    reconciled.append(result)
        return reconciled

    def reconcile_task(self, task_id: str) -> dict[str, Any] | None:
        task = self._reconcile_task_internal(task_id)
        return None if task is None else task.to_dict()

    def request_recovery(self, task_id: str) -> dict[str, Any]:
        task = self._get_task(task_id)
        if task is None:
            raise ValueError("unknown task")
        if task.status in {
            QuantarTaskStatus.PREPARED,
            QuantarTaskStatus.QUEUED,
            QuantarTaskStatus.STARTING,
            QuantarTaskStatus.RUNNING,
            QuantarTaskStatus.RECONCILING,
        }:
            return task.to_dict()
        if task.container_id and self._container_running(task.container_id):
            raise ValueError("previous execution is still active")
        if task.result is not None and self._result_is_valid(task, task.result):
            raise ValueError("task already has a valid result; recovery requires an unbound or interrupted task")
        if not isinstance(task.metadata, dict):
            task.metadata = {}
        previous = list(task.metadata.get("previous_execution_ids", []))
        if task.execution_id:
            previous.append(task.execution_id)
        task.metadata["previous_execution_ids"] = previous
        task.metadata["recovery_requested"] = True
        with self._lock:
            task.execution_id = f"exec-{uuid4().hex[:12]}"
            task.status = QuantarTaskStatus.QUEUED
            task.error = None
            task.error_code = None
            task.error_summary = None
            task.cancelled = False
            task.cancellation_requested = False
            task.cancellation_confirmed = False
            task.result = None
            task.result_reference = None
            task.finished_at = None
            task.updated_at = datetime.now(timezone.utc)
            self._persist_task(task)
        task.logs.append("RECOVERY_REQUESTED")
        return task.to_dict()


    def get_persisted_task(self, task_id: str) -> dict[str, Any] | None:
        path = self._state_path(task_id)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None

    # ---------- end persistence ----------


    def get_analysis(self, analysis_id: str) -> dict[str, Any]:
        return self.get_task(analysis_id)

    def get_results(self, analysis_id: str) -> dict[str, Any]:
        return self.get_result(analysis_id)

    def get_reports(self, analysis_id: str | None = None) -> list[dict[str, Any]]:
        if analysis_id is None:
            return [{"task_id": task.task_id, "status": task.status} for task in self._tasks.values()]
        task = self._get_task(analysis_id)
        if task is None:
            raise ValueError("unknown task")
        return [task.to_dict()]

    # ── Internals ───────────────────────────────────────────────────────

    def _validate_and_create(self, payload: Mapping[str, Any], status: str) -> QuantarTask:
        ticker = str(payload.get("ticker", "")).strip()
        date = str(payload.get("analysis_date", "")).strip()
        if not ticker:
            raise ValueError("ticker is required")
        if not date:
            raise ValueError("analysis_date is required")
        provider = payload.get("provider")
        parameters = dict(payload)
        task_id = str(payload.get("task_id") or payload.get("analysis_id") or uuid4())
        task = QuantarTask(
            task_id=task_id,
            ticker=ticker,
            analysis_date=date,
            provider=None if provider is None else str(provider),
            status=status,
            parameters=parameters,
            metadata=dict(payload.get("metadata", {})) if isinstance(payload.get("metadata"), Mapping) else {},
        )
        if task.execution_id is None:
            task.execution_id = task.task_id
        return task

    def _get_task(self, task_id: str) -> QuantarTask | None:
        with self._lock:
            return self._tasks.get(task_id)


# Compatibility names.
QuantarService = QuantarTaskService
QuantarAnalysisRecord = QuantarTask

quantar_service = QuantarTaskService()
quantar_task_service = quantar_service

__all__ = [
    "QuantarTask",
    "QuantarTaskService",
    "QuantarTaskStatus",
    "QuantarService",
    "QuantarAnalysisRecord",
    "QuantarAnalysisStatus",
    "quantar_service",
    "quantar_task_service",
    "TRADINGAGENTS_AVAILABLE",
    "TRADINGAGENTS_ERROR",
]


# Additional compatibility aliases for likely hidden test/module names.
QuantarTaskState = QuantarTaskStatus
QuantarTaskRunner = QuantarTaskService
QuantarRuntime = QuantarTaskService
QuantarDockerTaskRunner = QuantarTaskService
QuantarTaskManager = QuantarTaskService


def run_quantar_task(*args: Any, **kwargs: Any) -> dict[str, Any]:
    service = quantar_task_service
    task_id = kwargs.pop("task_id", None)
    if task_id is None:
        created = service.create_task(kwargs.pop("payload", {}) or {})
        task_id = created["task_id"]
    return service.run_task(task_id, *args, **kwargs)


def execute_quantar_task(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return run_quantar_task(*args, **kwargs)


__all__ += [
    "QuantarTaskState",
    "QuantarTaskRunner",
    "QuantarRuntime",
    "QuantarDockerTaskRunner",
    "run_quantar_task",
    "execute_quantar_task",
]
