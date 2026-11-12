import json
import subprocess
import sys
import types
from pathlib import Path

import core.applications.quantar_service as qs
from core.applications.quantar_service import QuantarTaskService, TRADINGAGENTS_AVAILABLE


class FakeGraph:
    def __init__(self, debug=False, config=None):
        self.debug = debug
        self.config = config

    def propagate(self, ticker, date):
        return (
            {"final_trade_decision": f"HOLD {ticker} {date}", "market_report": "r"},
            {"decision": f"HOLD {ticker} {date}"},
        )


def test_controlled_task_completes_with_propagate(monkeypatch) -> None:
    monkeypatch.setattr(qs, "TRADINGAGENTS_AVAILABLE", True)
    monkeypatch.setattr(qs, "TradingAgentsGraph", FakeGraph)

    service = qs.QuantarTaskService()
    prepared = service.prepare_analysis({"ticker": "NVDA", "analysis_date": "2026-09-01"})
    assert prepared["status"] == "PREPARED"

    started = service.start_analysis({"ticker": "NVDA", "analysis_date": "2026-09-01"}, execute=True)
    assert started["status"] == "COMPLETED"
    assert started["result"]["decision"] == "HOLD NVDA 2026-09-01"
    assert "propagate() invoked" in started["logs"]

    result = service.get_result(started["task_id"])
    assert result["decision"] == "HOLD NVDA 2026-09-01"
    assert result["reports"]["final_trade_decision"] == "HOLD NVDA 2026-09-01"


def test_task_can_be_cancelled_before_run() -> None:
    service = qs.QuantarTaskService()
    task = service.create_task({"ticker": "AAPL", "analysis_date": "2026-09-01"})
    cancelled = service.cancel_task(task["task_id"])
    assert cancelled["status"] == "CANCELLED"
    assert cancelled["cancelled"] is True


def test_container_result_is_required_for_completed(monkeypatch, tmp_path) -> None:
    def fake_run(command, **kwargs):
        result = subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")
        return result

    monkeypatch.setattr(qs.subprocess, "run", fake_run)
    monkeypatch.setattr(qs.shutil, "which", lambda _cmd: "/usr/bin/docker")

    service = qs.QuantarTaskService(workspace_root=tmp_path)
    task = service.create_task({"ticker": "NVDA", "analysis_date": "2026-09-01"})
    outcome = service.run_task_in_container(task["task_id"])
    assert outcome["status"] == "FAILED"
    assert "no result.json" in outcome["error"] or "no valid result" in outcome["error"]


def test_container_completion_requires_valid_result(monkeypatch, tmp_path) -> None:
    def fake_run(command, **kwargs):
        for i, arg in enumerate(command):
            if arg == "-v" and i + 1 < len(command):
                local = command[i + 1].split(":", 1)[0]
                result_path = Path(local) / "result.json"
                result_path.write_text(
                    json.dumps({"task_id": "x", "decision": "HOLD NVDA 2026-09-01", "status": "COMPLETED"}),
                    encoding="utf-8",
                )
        return subprocess.CompletedProcess(command, 0, stdout="done", stderr="")

    monkeypatch.setattr(qs.subprocess, "run", fake_run)
    monkeypatch.setattr(qs.shutil, "which", lambda _cmd: "/usr/bin/docker")

    service = qs.QuantarTaskService(workspace_root=tmp_path)
    task = service.create_task({"ticker": "NVDA", "analysis_date": "2026-09-01"})
    outcome = service.run_task_in_container(task["task_id"])
    assert outcome["status"] == "COMPLETED"
    assert outcome["result"]["decision"] == "HOLD NVDA 2026-09-01"
    assert outcome["exit_code"] == 0


def test_runner_writes_atomic_result(monkeypatch, tmp_path) -> None:
    # Inject a fake TradingAgents package without modifying the upstream repo.
    fake_config_module = types.ModuleType("tradingagents.default_config")
    fake_config_module.DEFAULT_CONFIG = {"llm_provider": "ollama", "deep_think_llm": "x", "quick_think_llm": "y"}

    fake_graph_module = types.ModuleType("tradingagents.graph.trading_graph")

    class RunnerFakeGraph:
        def __init__(self, debug=False, config=None):
            self.debug = debug
            self.config = config

        def propagate(self, ticker, date):
            return ("ok", {"decision": f"BUY {ticker} {date}", "final_trade_decision": f"{ticker} {date}"})

    fake_graph_module.TradingAgentsGraph = RunnerFakeGraph
    fake_package = types.ModuleType("tradingagents")
    fake_graphs = types.ModuleType("tradingagents.graph")

    monkeypatch.setitem(sys.modules, "tradingagents", fake_package)
    monkeypatch.setitem(sys.modules, "tradingagents.default_config", fake_config_module)
    monkeypatch.setitem(sys.modules, "tradingagents.graph", fake_graphs)
    monkeypatch.setitem(sys.modules, "tradingagents.graph.trading_graph", fake_graph_module)

    # The runner imports package modules inside functions.
    from examples.quantar.quantar_task_runner import run_once

    task_file = tmp_path / "task.json"
    result_file = tmp_path / "result.json"
    task_file.write_text(
        json.dumps({"task_id": "task-1", "ticker": "NVDA", "analysis_date": "2026-09-01", "provider": "ollama"}),
        encoding="utf-8",
    )

    result = run_once(task_file, result_file)
    assert result["task_id"] == "task-1"
    assert result["decision"] == "BUY NVDA 2026-09-01"
    assert result_file.exists()
    on_disk = json.loads(result_file.read_text(encoding="utf-8"))
    assert on_disk["decision"] == "BUY NVDA 2026-09-01"
    assert (tmp_path / "result.json.tmp").exists() is False


def test_runner_failure_writes_failed_result(monkeypatch, tmp_path) -> None:
    fake_config_module = types.ModuleType("tradingagents.default_config")
    fake_config_module.DEFAULT_CONFIG = {}

    fake_graph_module = types.ModuleType("tradingagents.graph.trading_graph")

    class FailingGraph:
        def __init__(self, debug=False, config=None):
            pass

        def propagate(self, ticker, date):
            raise RuntimeError("provider unavailable")

    fake_graph_module.TradingAgentsGraph = FailingGraph
    fake_package = types.ModuleType("tradingagents")
    fake_graphs = types.ModuleType("tradingagents.graph")

    monkeypatch.setitem(sys.modules, "tradingagents", fake_package)
    monkeypatch.setitem(sys.modules, "tradingagents.default_config", fake_config_module)
    monkeypatch.setitem(sys.modules, "tradingagents.graph", fake_graphs)
    monkeypatch.setitem(sys.modules, "tradingagents.graph.trading_graph", fake_graph_module)

    from examples.quantar.quantar_task_runner import main

    task_file = tmp_path / "task.json"
    result_file = tmp_path / "result.json"
    task_file.write_text(
        json.dumps({"task_id": "task-2", "ticker": "NVDA", "analysis_date": "2026-09-01"}),
        encoding="utf-8",
    )

    exit_code = main(["--task-file", str(task_file), "--result-file", str(result_file)])
    assert exit_code == 1
    on_disk = json.loads(result_file.read_text(encoding="utf-8"))
    assert on_disk["status"] == "FAILED"
    assert "provider unavailable" in on_disk["error"]
