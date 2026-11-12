# TRADINGAGENTS_INTEGRATION_GAPS

Date : 2026-11-03
Mode : audit en lecture seule.

## Gaps réels

1. Aucun service HTTP ou agent harness dans TradingAgents.
   - File: `main.py`, `cli/main.py`, `tradingagents/graph/trading_graph.py`
   - Impact: CDC/ETHAN doit créer un contrôleur externe.

2. Point-in-time and look-ahead integrity requirements are significant.
   - Memory and reports are tied to dated data.
   - An ETHAN wrapper must pass explicit `trade_date`.
   - INFERRED: caching of report outputs could reintroduce stale data.

3. Provider mismatch with ETHAN.
   - TradingAgents uses its own provider registry.
   - ETHAN manages `core/llm` providers differently.
   - Bridge needed before reuse.

4. Secrets management.
   - TradingAgents relies on `.env` and direct API keys.
   - ETHAN uses service-side permissions and (potential) vault.
   - Required adapter: mask credentials and validate key optionality.

5. Data provider limitations.
   - Yahoo, Alpha Vantage, SEC, FRED, Polymarket and other vendors vary in availability.
   - Lookahead guards exist and indicate known prior issues.

6. Runtime availability.
   - The run can be long and consume CPU and bandwidth.
   - Backtesting and full reports create disk load.
   - No controller in TradingAgents means ETHAN must add cancellation/timeout/polling.

7. Persistence model.
   - TradingAgents maintains memory logs under user home.
   - ETHAN's private memory should store only state decisions, not raw engine outputs.

8. Security.
   - No network permission isolation demonstrated.
   - No sandboxing in the inspected surface.
   - Credentials, data and output reports must remain in appropriate boundaries.

## NOT_TESTED

- Network integration
- Provider compatibility against ETHAN account policies
- Full runtime under Debit 13 with CPU-only
- long horizon data provider behavior and throttling
- full report generation and storage output
- preflight of assets in restricted or offline conditions

## Risques non clos

- Indisponibilité des fournisseurs
- Latence des rapports complets
- coûts LLM
- accès concurrents à un même ticker/date
- confusion entre simulation et ordre réel si la gouvernance est levée par erreur
- inconsistences mapping de symboles
- modifications de dépendances

Conclusion: integration is feasible via dedicated controller, but only with explicit auditing of providers, data vendors and resource limits.

## Current environment limitation

- Pytest collection failed due missing `yfinance`.
- No repository change was made.
- This is a NOT_TESTED environment condition.
