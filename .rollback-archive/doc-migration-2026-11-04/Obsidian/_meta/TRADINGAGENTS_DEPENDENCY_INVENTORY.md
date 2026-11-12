# TRADINGAGENTS_DEPENDENCY_INVENTORY

Date : 2026-11-03
Source : `/home/fatsio/AI/TradingAgents`
Status : CONFIRMED where file exists.

## Core dependencies

- tradingagents v0.7.1
- Python >= 3.11
- langchain-core, langchain-openai, langchain-anthropic, langchain-google-genai, langchain-aws optional
- langgraph and langgraph-checkpoint-sqlite
- requests, pandas, stockstats
- cryptography
- markdown-it-py, packaging, pytz, questionary, rich, typer
- yfinance
- typing-extensions

## Optional and conditional

- bedrock via `langchain-aws`
- stock/trading data providers such as Alpha Vantage and Yahoo
- SEC, FRED, Reddit, Polymarket, StockTwits
- Ollama-compatible local endpoint
- report backtests and dependencies

## Observed implementation properties

- Runs on Python 3.11+.
- Uses LangGraph via ToolNode, state schema and checkpointing.
- No mandatory server process; CLI drives runs.
- The execution path runs tools through `tradingagents` agents and dataflows.
- External services can fail independently.

## Reuse with ETHAN

Confirmed assets in ETHAN likely adaptable:
- Provider management in `core/llm` and `core/plugins`
- API key management via `core/auth` and `api_keys.py`
- Auth and RBAC in `core/auth`
- Eventing through `core/events` and bus
- Knowledge persistence through memory service / service patterns
- WebUI pattern for APIs under `interfaces/webui`

Points of concern:
- TradingAgents has its own `config`, while ETHAN uses a centralized `ConfigurationService`.
- Both can call network services; there is a risk of duplicated credentials and timeouts.
- Provider model catalog used by TradingAgents is not identical to ETHAN catalog.
- yfinance / pandas may be substantial, but already common for analytical workloads.
- `main.py` directly instantiates TradingAgents and runs an example.

## No secrets read

No secret values were examined, printed or transferred. Only file paths and key presence were noted.

## Risks

1. Double management of provider secrets.
2. Provider-specific endpoints and expectations.
3. Runtime latency due external data and LLM.
4. Data used for decision support must be labeled as simulation only.

## Environment note

- `pytest --collect-only` failed in the current Python 3.13 runtime because `yfinance` is not installed.
- No dependency was installed.
- This is a runtime availability gap, not evidence that TradingAgents is unimportable.
