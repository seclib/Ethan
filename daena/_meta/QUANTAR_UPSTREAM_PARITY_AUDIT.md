# QUANTAR — Audit de parité avec TradingAgents upstream

Date : 2026-11-04
Statut : audit uniquement, aucune modification effectuée

## 1. Upstream TradingAgents

Dépôt : `/home/fatsio/AI/TradingAgents`
Version TradingAgents vendored dans Quantar : `0.7.1`

Upstream expose un runtime interactif `main.py` et une CLI, avec cache sous `~/.tradingagents`, var env `TRADINGAGENTS_*` et image Docker `tradingagents` (user `appuser`).

## 2. Intégration Quantar

- `examples/quantar/tradingagents/` contient le moteur vendored (`__version__` = 0.7.1).
- `quantar_task_runner.py` appelle une fois `TradingAgentsGraph(...).propagate(ticker, date)`.
- Docker Quantar utilise `quantar-runtime:latest`, UID/GID 1000, read-only, `network: none`.
- Quantar ne démarre pas l'interface CLI de TradingAgents.

## 3. Tableau de parité

| Composant upstream | Fonction | Présent dans Quantar | État | Écart |
|---|---|---|---|---|
| `TradingAgentsGraph` | agent principal | oui | présent | intact |
| `propagate()` | exécution | oui | one-shot réelle/mockable | ok |
| CLI interactive upstream | utilisateur | non | absent | volontaire, API ETHAN remplace |
| stockage `~/.tradingagents` | cache/résultats | absence | non monté | risque de non-persistence |
| Docker upstream | service interactif | remplace | one-shot | intentional |
| providers LLM | model | présent | nécessite envprovider | pas de gateway réel |
| providers données (yfinance etc) | données | présent | bloqué par réseau `none` | permission required |
| tests upstream | validation | non intégrés 8tests Locally | volontaire? | non exécuté |

## 4. Architecture cible

- TradingAgents reste moteur d'analyse et tooling ;
- Quantar restreindre l'environnement pour sécurité ;
- ETHAN garde le gateway, l'auth, la supervision ;
- le cache et résultats doivent être persistés de façon contrôlée ;
- aucune différence de code au dépôt upstream.

## 5. Risques

- incompatibilité si TradingAgents utilise réseau externe ;
- pas de démonstration réelle ;
- dépendances volumineuses ;
- absence de health endpoint dans le runner.

## Conclusion

La version est paritaire, une exécution réelle avec un fournisseur local démontré est à faire. Le statut reste `PARTIALLY_VALIDATED`.
