# TRADINGAGENTS_UPSTREAM_RUNTIME_STUDY

Date : 2026-11-03
Statut : étude observationnelle

## Architecture upstream observée

- Point d'entrée : `main.py` à la racine.
- Importe `DEFAULT_CONFIG` puis `TradingAgentsGraph`.
- `ta.propagate("NVDA", "2026-09-01")` puis affiche la décision.
- Projet principal dans `tradingagents/`.
- CLI dans `cli/`.

## Dépendances

- Python 3.11 recommandé (ruff target `py311`).
- Dépendances déclarées dans `pyproject.toml` (LangChain/LangGraph, OpenAI, Anthropic, Gemini, pandas, yfinance, cryptography, stockstats, etc.).
- Clés fournisseur proviennent de l'environnement.
- Pas de backend HTTP ni de serveur natif dans `main.py`.

## Exécution officielle

```bash
pip install .
python main.py
```

Le processus principal fait une analyse puis se termine. Ce n'est pas un service daemon.

## Docker upstream

Le dépôt fournit un `Dockerfile` et `docker-compose.yml`, mais le point d'exécution de `main.py` reste une analyse ponctuelle.

## Vendor

Le dépôt contient des dépendances normales via pip. Aucune manipulation de vendor nécessaire si on utilise l'installation standard.

## Sécurité et isolation

- TradingAgents utilise des appels LLM et sources financières.
- Il nécessite des secrets fournisseur.
- Il ne doit pas accéder aux secrets ETHAN ni au socket Docker.
- Quantar doit rester une capacité d'analyse, sans ordre ni connexion.

## Recommandation

Pour ETHAN, encapsuler `propagate` dans le service Quantar, avec limites et preuves d'exécution, plutôt que de l'exposer directement comme service standalone.

Ne pas présenter le processus par défaut comme un démon.
