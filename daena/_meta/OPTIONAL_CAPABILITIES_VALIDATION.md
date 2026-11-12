# Validation réelle — capacités optionnelles

Date : 2026-11-04

## État d'inventaire

- `core/capability_manager/builtin.py` expose 10 capabilities:
  `memory`, `ollama`, `qdrant`, `chromadb`, `redis`, `searxng`, `whisper`,
  `mcp-filesystem`, `langchain`, `langgraph`.
- Après rebuild et redéploiement de `ethan-api`, l'API `/v1/components` renvoie bien les quatre capacité:
  `qdrant`, `chromadb`, `langchain`, `langgraph`.
- Le frontend lit ces composants via l'API existante et n'implémente pas de logique d'installation.

## Réellement validé

- Qdrant / ChromaDB :
  - déclarations optionnelles présentes dans `builtin.py`
  - images officielles déjà référencées indirectement via compose/dev
  - aucun démarrage automatique par cette phase
- LangChain / LangGraph :
  - déclarées comme `python_package` optionnelles
  - import vérifié non effectué dans l'environnement actuel

## Verifications techniques

- `build_manager()` charge 10 composants
- `tests/core/test_capability_manager.py`: 110 passed, 1 échec preexistant `test_health_gate_pas_ready_sans_endpoint`
- `interfaces/api/tests/test_components_lifecycle_api.py` : 9 passed

## Limites

- LangChain et LangGraph sont déclarés, mais leur installabilité réelle dépend de l'environnement pip courant.
- La vérification d'import n'a pas été exécutée sur ces paquets.
- Aucune documentation manuelle n'a été créée; l'interface peut afficher leur metadata native si disponibles.

## Conclusion

Les capacités optionnelles sont déclarées et discoverables via Core. La validation runtime réelle reste conditionnée à des tests d'installation effectifs et à un frontend testé avec session.
