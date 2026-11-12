# TRADINGAGENTS_PHASE_1_REPORT.md

Date : 2026-11-03
Status : PHASE_1_DESIGN_COMPLETE_WITH_DECISIONS_PENDING

## 1. Architecture proposée
Controller dedicated, Python orchestration, read-only Analytical engine, scheduling via API and status.

## 2. Choix techniques recommandés
- Reuse current ETHAN `core/llm` only after provider mapping.
- Keep TradingAgents as external command/package.
- Require a controller.
- Store reports as external references.
- Preserve memory log as evidence.

## 3. Alternatives écartées
- Direct embedding in ETHAN.
- Full rewrite of TradingAgents.
- Auto orchestration without permissions.
- Publishing without allowlist.

## 4. Points confirmés
- TradingAgents is a research analysis engine.
- File entry points and graph exist.
- CLI exists.
- Project has tests and modular dataflows.

## 5. Inconnues
- Provider mapping.
- Performance.
- Dependency errors.
- Data vendor budgets.
- Disk cache sizing.
- Async cancellapping.

## 6. Risques bloquants
- External network dependence.
- Cost and compliance.
- unsafe assumptions around finance.
- lack of observability.

## 7. Décisions humaines requises
- Outside worker or embedded.
- provider profile.
- resources.
- output ownership.
- public visibility of results.

## 8. Ordre d'implémentation
- Phase 1 decision, then Phase 2 implementation.

## 9. Confirmation du code
Aucun code ETHAN n'a été modifié pendant cette phase.
