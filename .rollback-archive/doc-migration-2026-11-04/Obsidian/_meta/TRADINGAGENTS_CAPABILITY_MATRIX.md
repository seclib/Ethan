# TRADINGAGENTS_CAPABILITY_MATRIX

Date : 2026-11-03
Mode : lecture et audit seulement.

| Fonctionnalité | TradingAgents | ETHAN existant | Intégration nécessaire |
|---|---|---|---|
| Moteur multi-agents | oui | oui | adaptateur, non réimplémentation |
| Analyse financière | oui | non | ETHAN doit exposer l'exécution comme service |
| Analystes fondamentaux | oui | providers / LLm clients | mapper provider et modèles |
| Analystes sentiment/news | oui | rag / recherche interne | respecter les sources de données |
| Technical analyst | oui | non | contrôleur d'exécution et affichage |
| Research debate (bull/bear) | oui | conversation agents | mapping possible, hors phases |
| Trader / decision | oui | non | exposer le résultat, ne pas exécuter d'ordre réel |
| Risk management | oui | security / policies ETHAN | adapter les gates de permissions |
| Portfolio manager | oui | aucune simulation existante | gestion de requête, read-only |
| Graphique / workflow | LangGraph | ETHAN / WebUI | UI controller et récupération de statut |
| Backtesting | oui | tests / benchmarks | nécessite audit de données temporelles |
| Checkpoint resume | oui | non | wrapper ou service d'exécution
