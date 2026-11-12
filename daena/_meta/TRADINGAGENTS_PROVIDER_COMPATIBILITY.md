# TRADINGAGENTS_PROVIDER_COMPATIBILITY.md

Date : 2026-11-03
Statut : PROPOSED

## 1. Objectif

Documenter la compatibilité effective potentielle entre les providers TradingAgents et les mécanismes d'ETHAN.

## 2. Source observée

Factory et clients TradingAgents supportent :
- OpenAI
- xAI
- DeepSeek
- Qwen
- Qwen-CN
- GLM
- GLM-CN
- MiniMax
- MiniMax-CN
- OpenRouter
- Mistral
- Kimi
- Groq
- NVIDIA
- Ollama en compatible OpenAI
- ChatGPT plan client
- compétent OpenAI compatible
- Anthropic
- Google et Gemini
- Azure
- Bedrock optionnel

ETHAN fournit :
- `core/llm` et `core/llm/store`
- `provider_manager`
- `model management`
- API `providers` et `models`
- `Plugin` / `Tool` integration
- Permission `MEMORY`, `READ`, mécanism RBAC

## 3. Table de compatibilité

| Provider | Interface TradingAgents | Interface ETHAN | Compatibilité démontrée | Adaptateur nécessaire |
|---|---|---|---|---|
| OpenAI | Natif | Oui, native | Partielle | mapping credentials et endpoint |
| Anthropic | Natif | probablement non aujourd'hui | À valider | wrapper |
| Google/Gemini | Natif | selon ETHAN et capabilities | À valider | wrapper |
| Azure | Natif | probable | À valider | wrapper |
| DeepSeek | OpenAI compat | possible | À valider | mapping |
| xAI | OpenAI compat | possible | À valider | mapping |
| Mistral | OpenAI compat | possible | À valider | mapping |
| Ollama | OpenAI compat locale | existe dans ETHAN | À valider | URL et credentials |
| ChatGPT plan | sign-in token | ETHAN non comparable | faible | à valider |

## 4. Notes techniques

- TradingAgents accepte des secrets via `.env`.
- ETHAN gère centralisée et rbac.
- Les tiers `quick` et `deep` sont sélectionnés séparément.
- Les formats structurés sont utilisés pour les managers.
- Les formats de messages normalisés sont nécessaires pour éviter des désaccords.
