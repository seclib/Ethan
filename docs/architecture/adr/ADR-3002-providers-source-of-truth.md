# ADR-3002 — Providers : ProviderManager = seule source de vérité

**Statut** : Proposition (brouillon)
**Date** : 2026-09-07
**Contexte** : Le WebUI (ort de Settings) et certains fallbacks affichent des providers
« par défaut » définis statiquement dans `core/state/webui_store.py` (`_DEFAULT_PROVIDERS` :
openai, anthropic, huggingface, pinecone…), alors que la source réelle est
`core/llm/provider_manager.py` (ProviderManager, monté dans `main.py`). En mode fallback,
l'UI peut donc afficher des providers non réellement configurés.

**Décision** :

1. `core/llm/provider_manager.py` est la **seule** source de vérité (providers + models + test + default).
2. Le fallback statique `_DEFAULT_PROVIDERS` de `webui_store` est **supprimé** ; en l'absence de
persistance, le ProviderManager répond une liste vide plutôt qu'une liste fictive.
3. L'API (`providers.py`, `models.py`) n'expose que ce que le ProviderManager renvoie réellement.

**Conséquences** :

- Plus aucun provider « fantôme » dans l'interface.
- La page Providers WebUI dépend uniquement de `GET /providers` (ProviderManager).
- Fin de la double écriture settings/providers.

**Alternatives écartées** :

- Conserver les défauts statiques comme « exemples » (contradiction avec « ne montrer que du réel »).
