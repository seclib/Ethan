# QUANTAR — Préparation de l’exécution réelle sécurisée (Phase 42)

Date : 2026-11-04
Statut : readiness completé ; statut opérationnel encore PARTIALLY_VALIDATED

## 1. Architecture proposée

Flux cible :

1. ETHAN crée une tâche dans `QuantarTaskService`;
2. ETHAN initialise un workspace dédié et `task.json`;
3. la tâche est exécutée dans un conteneur one-shot avec accès réseau limité ;
4. le runner utilise `TradingAgentsGraph(...).propagate(ticker, analysis_date)` ;
5. le résultat est écrit dans `result.json` ;
6. la passerelle fournisseur HROT est le seul point de sortie autorisé pour les appels LLM ;
7. ETHAN récupère et persiste le résultat.

Le point central de sécurité reste la passerelle fournisseur.

## 2. Compatibilité TradingAgents

- Dépôt vendored : `examples/quantar/tradingagents/` version `0.7.1`.
- Dépendances déclarées via `pyproject.toml` (>=3.11), dont `langchain-openai`, `langchain-anthropic`, `langchain-google-genai`, LangGraph, yfinance, pandas, network requests.
- La construction attendue est :
  - `TradingAgentsGraph(debug=False, config=config)`
  - `graph.propagate(ticker, analysis_date)`
- Le runner lit un unique JSON, puis sort en `0` ou `1`.
- Le runner actuel ne transmet pas de provider key; il dépend de variables d’environnement.
- Le dépôt upstream n’a pas été modifié.

## 3. Conception HROT fournisseur

Principe :

- secrets conservés par ETHAN et jamais transmis au frontend ;
- seuls les noms de provider et les autorisations approuvées traversent les payloads ;
- la passerelle relaie les requêtes LLM autorisées ;
- aucune sélection silencieuse de fournisseur ;
- logs/resultats sans secret ;
- révocation par désactivation de la liaison et par expiration de l’approbation ;
- traçabilité des autorisations, horaires et opérations.

Exigences canoniques :

- permissions applicatives dédiées à QUANTAR ;
- opération `propagate` uniquement ;
- fournisseur limité à celui sélectionné ;
- kein accès aux services personnels, portefeuilles ou clés stockées ;
- hors-scope complet pour toute signature ou transaction financière.

## 4. Choix réseau

Option A recommandée : passerelle locale contrôlée.

- Quantar ne voit qu’un endpoint passerelle autorisé ;
- pas d’Internet direct ;
- endpoints et fournisseurs allowlistés ;
- secrets conservés côté ETHAN ;
- politique réseau vérifiable et documentée.

Option B (direct restreint) n’est pas recommandée sans justification, car elle élargit le périmètre de confiance et risque de détourner la politique via DNS ou endpoints non prévus.

`network: none` ne doit pas être supprimé avant validation d’une passerelle remplissant les mêmes garanties.

## 5. Persistance

États de tâche proposés :

- `COMPLETED` : résultat validé ;
- `FAILED` : erreur explicite ;
- `INTERRUPTED` : arrêt inattendu ou annulation confirmée ;
- `RECONCILING` : état à reconcilier après redémarrage.

Règles :

- une tâche interrompue sans `result.json` valide est `INTERRUPTED` ;
- le runner n’inscrit jamais `COMPLETED` sans écriture résultats atomique ;
- les métadonnées et logs sont associés au `task_id` et au workspace.

La reprise automatique de tâches n’est pas démontrée et ne doit pas être annoncée comme acquise.

## 6. Conception de l’annulation

- envoi de signal au conteneur ;
- délai de grâce ;
- arrêt forcé après délai ;
- statut final `CANCELLED` uniquement après confirmation effective ;
- nettoyage du conteneur et du workspace si applicable.

Ne pas reporter `CANCELLED` si le processus continue.

## 7. Matrice de tests

Catégories requises avant première exécution réelle :

- unitaires service et statut ;
- mocks fournisseur et graph ;
- tests de passerelle HROT ;
- tests réseau et isolation ;
- tests Docker one-shot ;
- tests persistance ;
- tests d’annulation ;
- exécution TradingAgents réelle (hors phase automatique sans autorisation).

## 8. Risques et limites

- dépendance TradingAgents non installée dans l’environnement ETHAN ;
- fournisseur LLM non crédentisé ;
- logs peuvent contenir des données sensibles si non masquées ;
- persistance à reconstruire après restart ;
- annulation réelle non démontrée.

## 9. Blocages

- pas de provider LLM clinique pour opération ;
- pas de connecteur HROT fournisseur ;
- pas de preuve de gateway vérifiable ;
- pas de test réel TradingAgents.

## 10. Critères d’autorisation

Première exécution réelle seulement si :

- provider et endpoint autorisés ;
- gateway HROT opérationnelle ;
- secrets absents du conteneur ;
- réseau allowlist ;
- uri de passerelle validée ;
- statut et résultat persistants ;
- annulation démontrée ;
- autorisation explicite reçue.

## Statut

`PARTIALLY_VALIDATED` — plan prêt, exécution réelle non réalisée et non démontrée.
