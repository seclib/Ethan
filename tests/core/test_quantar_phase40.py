from core.applications.quantar_service import QuantarService, TRADINGAGENTS_AVAILABLE


class FakeGraph:
    def __init__(self, debug=False, config=None):
        self.debug = debug
        self.config = config

    def propagate(self, ticker, date):
        return "ok", {"decision": f"HOLD {ticker} {date}"}


def test_engine_lifecycle_with_controlled_engine(monkeypatch) -> None:
    import core.applications.quantar_service as qs
    monkeypatch.setattr(qs, "TRADINGAGENTS_AVAILABLE", True)
    monkeypatch.setattr(qs, "TradingAgentsGraph", FakeGraph)

    service = qs.QuantarService()
    prepared = service.prepare_analysis({"ticker": "NVDA", "analysis_date": "2026-09-01"})
    assert prepared["status"] == "PREPARED"

    started = service.start_analysis({"ticker": "NVDA", "analysis_date": "2026-09-01"}, execute=True)
    assert started["status"] == "COMPLETED"
    assert "HOLD NVDA 2026-09-01" in str(started["result"]["decision"])

    result = service.get_results(started["analysis_id"])
    assert result["decision"] == "HOLD NVDA 2026-09-01"

    analysis = service.get_analysis(started["analysis_id"])
    assert analysis["status"] == "COMPLETED"
    assert analysis["started_at"] is not None
    assert analysis["finished_at"] is not None

    assert service.list_analyses()
    assert service.get_reports(started["analysis_id"])
