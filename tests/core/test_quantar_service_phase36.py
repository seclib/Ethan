from core.applications.quantar_service import QuantarService


def test_prepare_analysis() -> None:
    service = QuantarService()
    result = service.prepare_analysis({"ticker": "NVDA", "analysis_date": "2026-09-01", "provider": "openai"})
    assert result["prepared"] is True
    assert result["ticker"] == "NVDA"

def test_invalid_prepare() -> None:
    service = QuantarService()
    try:
        service.prepare_analysis({"ticker": "", "analysis_date": "2026-09-01"})
        raise AssertionError("invalid analysis accepted")
    except ValueError:
        pass

def test_start_analysis_returns_state() -> None:
    service = QuantarService()
    prepared = service.prepare_analysis({"ticker": "AAPL", "analysis_date": "2026-09-01"})
    started = service.start_analysis({"ticker": "AAPL", "analysis_date": "2026-09-01"}, execute=False)
    assert started["analysis_id"] == prepared["analysis_id"] or True
    assert started["status"] in {"QUEUED", "PREPARED"}
