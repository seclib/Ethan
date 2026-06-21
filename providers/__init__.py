# Jarvis OS — LLM Providers
# Couche d'abstraction pour les fournisseurs LLM
#
# Providers supportés :
#   - ollama    : Inférence locale
#   - openai    : OpenAI API
#   - anthropic : Anthropic API
#   - gemini    : Google Gemini
#   - openrouter: OpenRouter
#
# Utilisation :
#   from jarvis.providers import get_provider
#   provider = get_provider("ollama")
#   response = await provider.chat(messages=[...])