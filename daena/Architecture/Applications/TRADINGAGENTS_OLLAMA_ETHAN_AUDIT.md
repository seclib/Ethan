# TradingAgents — Audit Ollama / ETHAN Provider Gateway

**Date** : 2026-11-05  
**Dépôts étudiés** :
- ETHAN : `/home/fatsio/AI/Ethan`
- TradingAgents : `/home/fatsio/AI/TradingAgents` (commit `c4544913a14ed3df5f1ed7b9e8483270ce20682a`, branche `v0.7.1`)

**Statut** : mission d’audit et de qualification uniquement. Aucune modification de code de production, aucun changement de configuration, aucune suppression de fichier ou de dépendance, aucun changement Docker/HROT.

---

## 1. Objectif et périmètre

L’objectif est de déterminer :

1. comment TradingAgents sélectionne et initialise les LLM ;
2. comment les agents et sous-graphes LangGraph consomment ces LLM ;
3. si Ollama peut fonctionner réellement dans ce contexte ;
4. comment réutiliser les providers et le Provider Gateway existants d’ETHAN sans dupliquer de gestionnaire ni créer de second système de permissions ;
5. quelle architecture est la plus défendable pour une future intégration Quantar.

Le rapport ne commence aucune intégration. Il fournit une cartographie, des preuves et des missions indépendantes.

---

## 2. Résumé exécutif

- TradingAgents est un framework LangGraph multi-agent. Il utilise des LLM de deux niveaux : `quick_think_llm` (analystes, traders, débateurs) et `deep_thinking_llm` (managers).
- La sélection du fournisseur est pilotée par `default_config` plus des variables `TRADINGAGENTS_*`, puis par `create_tier_client`, `tier_provider` et `create_llm_client`.
- TradingAgents ne possède pas un client Ollama natif distinct. Ollama est traité comme un fournisseur OpenAI-compatible via `langchain_openai.ChatOpenAI`, avec `base_url=http://localhost:11434/v1` et `OLLAMA_BASE_URL`.
- La clé API est optionnelle pour Ollama : une clé canonique `None`, avec placeholder `ollama`.
- Le worker Quantar actuel exécute `TradingAgentsGraph.propagate` directement et ne configure aucun provider. Le défaut `llm_provider = openai` avec des modèles `gpt-6-sol` / `gpt-6-luna` inexistants explique l’échec sur `OPENAI_API_KEY`.
- TradingAgents expose déjà un fallback robuste : structured output optionnel, free-text lors d’un échec, outils via LangChain.
- Ollama local est techniquement compatible pour une génération simple, du JSON object et du JSON Schema ; l’appel avec outils a aussi fonctionné avec `llama3.2:3b`.
- Le Provider Gateway ETHAN est actuellement **textuel** : messages `system/user/assistant`, paramètres limités, réponse string. Il ne supporte pas les outils LangChain, le `tool_choice`, le JSON Schema ni les appels multi-tours dont TradingAgents a besoin.
- Le Provider Manager ETHAN est capable de décrire et piloter Ollama et OpenAI, mais son API `chat()` expose un `ChatResponse` sans outils ni `tool_calls`.

**Conclusion préliminaire** : Ollama peut servir TradingAgents localement si le worker est configuré pour le provider `ollama` et si les modèles sélectionnés supportent réellement le tool calling. Il n’est pas possible aujourd’hui de faire transiter toutes les capacités nécessaires par le Provider Gateway ETHAN sans une adaptation majeure de ce gateway et un adaptateur LangChain-compatible.

---

## 3. Architecture réelle de TradingAgents

### 3.1 Sources principales

| Domaine | Fichiers |
|---|---|
| Configuration par défaut | `tradingagents/default_config.py` |
| Orchestration globale | `tradingagents/graph/trading_graph.py` |
| Montage du graphe | `tradingagents/graph/setup.py` |
| Exécution des analystes | `tradingagents/agents/analysts/turn.py` |
| Clients LLM | `tradingagents/llm_clients/factory.py`, `openai_client.py`, `anthropic_client.py`, `google_client.py`, `azure_client.py`, `bedrock_client.py` |
| Capacités modèles | `tradingagents/llm_clients/capabilities.py` |
| Validation modèles | `tradingagents/llm_clients/validators.py` |
| Modèles proposés | `tradingagents/llm_clients/model_catalog.py` |
| Structured output | `tradingagents/agents/structured.py`, `tradingagents/agents/schemas.py` |
| Agents managers | `tradingagents/agents/managers/portfolio_manager.py`, `research_manager.py` |
| Agents métier | `tradingagents/agents/trader/trader.py`, `researchers/*`, `risk_mgmt/*`, `analysts/*` |
| Outils | `tradingagents/agents/tools.py` |
| Mémoire et réflexion | `tradingagents/memory/reflection.py`, `tradingagents/memory/log.py` |

### 3.2 Flux d’exécution

1. Création de `TradingAgentsGraph` avec `config` ou `DEFAULT_CONFIG`.
2. `set_config(self.config)` globalize la configuration pour les vendors.
3. `create_tier_client(config, "deep")` puis `"quick"` construit deux clients LLM selon les tiers.
4. `Reflector(quick_thinking_llm)` est initialisé pour la réflexion sur décisions passées.
5. `GraphSetup` construit le graphe parallèle des analystes, puis le débat de recherche, le trader, les débats de risque et le Portfolio Manager.
6. `propagate()` crée l’état initial, exécute `graph.invoke`, enregistre la décision et le state log.
7. Les analystes utilisent `bind_tools` pour obtenir des données, via LangGraph ToolNode.

### 3.3 Rôles agents et besoins en modèles

| Agent | LLM utilisé | Outils | Structured output |
|---|---|---|---|
| Market Analyst | quick | `get_stock_data`, `get_indicators`, `get_verified_market_snapshot` | non |
| Sentiment Analyst | quick | données pré-fetchées dans le prompt, aucun tool binding | `SentimentReport` |
| News Analyst | quick | `get_news`, `get_global_news`, `get_macro_indicators`, `get_prediction_markets` | non |
| Fundamentals Analyst | quick | `get_fundamentals`, `get_balance_sheet`, `get_cashflow`, `get_income_statement`, `get_insider_transactions` | non |
| Bull Researcher | quick | non | non |
| Bear Researcher | quick | non | non |
| Research Manager | deep | non | `ResearchPlan` |
| Trader | quick | non | `TraderProposal` |
| Aggressive / Neutral / Conservative Debators | quick | non | non |
| Portfolio Manager | deep | non | `PortfolioDecision` |
| Reflector | quick | non | free text |

Remarque : les managers produisent la décision structurée principale. Les analystes produisent des rapports libres et dépendent du tool calling.

---

## 4. Cartographie des appels LLM

### 4.1 Fonctions clés de sélection

| Fonction/classe | Fichier | Rôle |
|---|---|---|
| `build_default_config` | `tradingagents/default_config.py` | défauts et overrides env `TRADINGAGENTS_*` |
| `build_llm_kwargs` | `tradingagents/llm_clients/factory.py` | construit les kwargs provider-spécifiques |
| `tier_provider` | `tradingagents/llm_clients/factory.py` | choisit provider deep/quick |
| `create_tier_client` | `tradingagents/llm_clients/factory.py` | construit un client pour un tier |
| `create_llm_client` | `tradingagents/llm_clients/factory.py` | instancie le client provider |
| `OpenAIClient.__init__` / `get_llm` | `tradingagents/llm_clients/openai_client.py` | registry OpenAI-compatible |
| `get_capabilities` | `tradingagents/llm_clients/capabilities.py` | méthode structured, tool_choice |
| `validate_model` | `tradingagents/llm_clients/validators.py` | acceptation des noms de modèles |
| `bind_structured` / `invoke_structured` | `tradingagents/agents/structured.py` | structured output + fallback |
| `take_turn` | `tradingagents/agents/analysts/turn.py` | `bind_tools`, wrapped last turn |
| `create_*` | `agents/...` | définition des prompts et tool binding |
| `Reflector.reflect` | `tradingagents/memory/reflection.py` | réflexion sur décision |
| `TradingAgentsGraph.__init__` | `tradingagents/graph/trading_graph.py` | construction des deux LLM |

### 4.2 Configuration et overrides

Variables `TRADINGAGENTS_*` mappées dans `_ENV_OVERRIDES` :

- `TRADINGAGENTS_LLM_PROVIDER`
- `TRADINGAGENTS_DEEP_THINK_LLM`, `TRADINGAGENTS_QUICK_THINK_LLM`
- `TRADINGAGENTS_DEEP_THINK_PROVIDER`, `TRADINGAGENTS_QUICK_THINK_PROVIDER`
- `TRADINGAGENTS_DEEP_THINK_BACKEND_URL`, `TRADINGAGENTS_QUICK_THINK_BACKEND_URL`
- `TRADINGAGENTS_LLM_BACKEND_URL`
- `TRADINGAGENTS_TEMPERATURE`, `TRADINGAGENTS_LLM_MAX_RETRIES`, `TRADINGAGENTS_MAX_TOKENS`
- `TRADINGAGENTS_OPENAI_REASONING_EFFORT`, `TRADINGAGENTS_GOOGLE_THINKING_LEVEL`, `TRADINGAGENTS_ANTHROPIC_EFFORT`
- `OLLAMA_BASE_URL` (lecture directe à l’appel, pour le provider `ollama`)

Défauts importants :
- `llm_provider = "openai"`
- `deep_think_llm = "gpt-6-sol"`
- `quick_think_llm = "gpt-6-luna"`
- `backend_url = None`
- tiers provider `None`, donc héritent du provider global
- `temperature = None`, `llm_max_retries = None`, `max_tokens = None`

Conséquence directe : sans variables d’environnement, Quantar demande OpenAI, modèle non reconnu, et échoue si `OPENAI_API_KEY` absent.

### 4.3 Providers supportés

Native :
- `anthropic` via `AnthropicClient`
- `google` via `GoogleClient`
- `azure` via `AzureOpenAIClient`
- `bedrock` via `BedrockClient`

OpenAI-compatible via registre `OPENAI_COMPATIBLE_PROVIDERS` :
- `openai` (Responses API sur base native)
- `xai`, `deepseek`, `qwen`, `qwen-cn`, `glm`, `glm-cn`, `minimax`, `minimax-cn`
- `openrouter`, `mistral`, `kimi`, `groq`, `nvidia`
- `ollama` (`http://localhost:11434/v1`, clé optionnelle)
- `chatgpt` (authentification par session)
- `openai_compatible` (endpoint utilisateur)

Ollama est donc déjà officiellement pris en charge dans TradingAgents.

---

## 5. Compatibilité Ollama — preuves techniques

### 5.1 Intégration native Ollama dans TradingAgents

Points observés :

- `OPENAI_COMPATIBLE_PROVIDERS["ollama"] = ProviderSpec(base_url="http://localhost:11434/v1", base_url_env="OLLAMA_BASE_URL", key_optional=True, placeholder_key="ollama", chat_class=LocalCompatibleChatOpenAI)`
- `PROVIDER_API_KEY_ENV["ollama"] = None`
- `validators._ANY_MODEL_PROVIDERS` inclut `"ollama"` : tout nom de modèle est accepté
- `LocalCompatibleChatOpenAI.with_structured_output` force `tool_choice=None` pour `function_calling`
- `model_catalog.get_model_options("ollama", ...)` propose des modèles par défaut : Qwen3, GPT-OSS, GLM-4.7-Flash et option `custom`
- Le test `tests/test_structured_output_suppresses_object_tool_choice` confirme ce comportement pour Ollama

### 5.2 Risques de compatibilité réels

1. **Tool calling variable selon modèle**  
   TradingAgents dépend de `llm.bind_tools(...)` pour les analystes. La méthode `take_turn` transmet `tools` au modèle. Si le modèle Ollama ne retourne pas un `tool_call`, l’analyste peut produire un rapport incomplet. LangGraph ToolNode n’exécutera rien sans `tool_calls`.

2. **Structured output non garanti localement**  
   Les méthodes `_DEFAULT` supposent `function_calling`, `json_mode` et `json_schema`. `LocalCompatibleChatOpenAI` supprime `tool_choice` en mode `function_calling`. Le parseur Pydantic peut néanmoins fonctionner si le modèle choisit l’outil schema. Si le modèle retourne du texte non conforme, `bind_structured` réussit à la création, mais `invoke_structured` renvoie `None`, puis fallback free-text. La décision finale peut alors ne pas contenir un rating parsable.

3. **Capacités supposées trop optimistes**  
   `get_capabilities(model_name)` renvoie `_DEFAULT` pour tout modèle inconnu, y compris un petit modèle Ollama sans tool calling robuste. Il n’y a pas d’entrée spécifique Ollama. Des modèles incapables peuvent être traités comme capables.

4. **Historique d’outils**  
   `take_turn._as_text` est prévu pour les providers qui refusent un historique avec `tool_calls` quand aucun outil n’est borné. Ollama via endpoint OpenAI-compatible doit supporter les messages `assistant` avec `tool_calls` et les messages `tool`. La preuve dépend du modèle et de la version Ollama.

5. **Reasoning models**  
   DeepSeek possède un override explicite pour `reasoning_content` roundtrip. Ollama expose parfois des modèles de raisonnement. Aucune logique équivalente n’est prévue pour Ollama. Cela peut casser des appels multi-tours avec outils si la réponse contient une sortie de raisonnement non propagée.

6. **Modèles catalogués vs modèles réellement installés**  
   Les modèles catalogués Ollama ne sont pas nécessairement installés. L’option `custom` permet d’indiquer un modèle local. Dans l’environnement examiné, les modèles disponibles sont par exemple `llama3.2:3b`, `qwen3.5:9b`, `glm4:9b`, `gemma4:12b`.

### 5.3 Tests réels effectués sur Ollama

Ollama est disponible localement (`0.40.13`) et les modèles listés ont été inventoriés. Trois tests non destructifs ont été réalisés via l’endpoint OpenAI-compatible `http://localhost:11434/v1` avec `llama3.2:3b` :

| Test | Résultat |
|---|---|
| Génération simple (prompt `PONG`) | succès, réponse `PONG` |
| JSON object avec `response_format={"type":"json_object"}` | succès, JSON valide `{"action":"Buy","reason":"Investment strategy"}` |
| JSON Schema avec `response_format={"type":"json_schema", ...}` | succès, JSON valide `{"action":"Sell","reason":"Overbought"}` |
| Tool calling avec `tool_choice="required"` | succès, appel `get_weather({"city":"Paris"})` correctement produit |

Interprétation :
- Ollama supporte les primitives nécessaires à TradingAgents : chat, JSON object, JSON Schema et tool calling.
- La compatibilité est **prouvée pour un modèle donné**, pas pour l’ensemble des modèles locaux.
- Aucun test réel du framework complet n’a pu être exécuté dans ce dépôt car aucune dépendance LangChain/LangGraph n’a été installée pour TradingAgents dans l’environnement actuel. Les tests unitaires existants de TradingAgents mentionnent l’endpoint Ollama et le comportement `tool_choice`, mais n’ont pas été exécutés ici.

### 5.4 Matrice agent × Ollama (audit)

| Agent | Peut fonctionner avec Ollama ? | Condition |
|---|---|---|
| Market Analyst | oui conditionnel | modèle supportant `bind_tools` et séquence OHLCV |
| Sentiment Analyst | oui, avec dégradation possible | structured output dépend de function calling sans `tool_choice`; sinon fallback free-text |
| News Analyst | oui conditionnel | modèle supportant `bind_tools` |
| Fundamentals Analyst | oui conditionnel | modèle supportant `bind_tools` |
| Bull/Bear researchers | oui | génération libre |
| Research Manager | oui, avec dégradation possible | structured `ResearchPlan` ou fallback |
| Trader | oui, avec dégradation possible | structured `TraderProposal` ou fallback |
| Risk debators | oui | génération libre |
| Portfolio Manager | oui, avec dégradation possible | structured `PortfolioDecision` ou fallback |
| Reflector | oui | génération libre |

Conclusion : **Ollama est compatible au niveau transport**, mais la **fiabilité dépend fortement du modèle et de sa robustesse en tool calling et structured output**.

---

## 6. Analyse des capacités d’ETHAN utiles

### 6.1 Provider Manager

`core/llm/provider_manager.py` est la source canonique pour les providers LLM d’ETHAN.

Points pertinents :
- Ollama est un type natif (`"ollama"`) avec capacités `["llm", "vision", "embedding"]`.
- `_resolve_ollama_base_url()` gère `OLLAMA_BASE_URL`, puis `host.docker.internal`, puis `localhost`.
- `get_catalog()` expose les types, URL par défaut, méthodes d’auth et capacités.
- `chat()` et `chat_stream()` délèguent à `LLMClient`.
- Les clés API sont stockées uniquement en mémoire (`_api_keys`), jamais persistées ni renvoyées.
- Les providers cloud auto-activés peuvent l’être à partir des secrets/env.

Ce manager est la vraie source de vérité. Aucun second gestionnaire ne doit être créé.

### 6.2 Provider Gateway HROT

`core/security/hrot_provider_gateway.py` définit `ProviderGateway`, `SecretProvider`, `QuantarProviderBridge` et `HrotDurableAuthorizationAuthority`.

Capacités actuelles :
- autorisation explicite (`authorization_id`, principal, application, provider, model, capability, resource, action)
- expiration et révocation
- rate limiting
- validation stricte des messages (`system`, `user`, `assistant`)
- paramètres limités à `temperature`, `max_tokens`, `top_p`, `stop`
- adaptateur par provider ; le secret est lu uniquement dans le gateway
- exécution synchrone `execute(ProviderGatewayRequest) -> ProviderGatewayResponse`
- résultat textuel normalisé
- redaction des secrets dans la réponse
- HROT durable en délégation (`create_approval`, `verify_and_consume`)

Limitations observées :
- pas de support des outils LangChain, de JSON Schema ou de `tool_calls`
- messages `tool` non autorisé dans `ALLOWED_MESSAGE_ROLES` (`system`, `user`, `assistant` uniquement)
- pas de réponse avec `finish_reason`, `tool_calls`, `usage` structuré
- pas de streaming
- les autorisations sont in-process ; le worker conteneurisé n’a pas de canal pour les atteindre
- `QuantarProviderBridge` exige `execution_id`, mais aucune communication worker↔gateway n’est réalisée
- `ProviderGateway` n’est utilisé par aucun module opérationnel selon la phase 47 documentée

### 6.3 Contrainte d’isolation Quantar

`QuantarTaskService` peut exécuter soit in-process, soit dans un conteneur one-shot. Le conteneur :
- est en mode read-only ;
- tourne avec `user: 1000:1000` ;
- n’a pas de réseau externe projeté (`network_mode="none"` par défaut) ;
- ne reçoit aucune clé ni endpoint gateway ;
- écrit `result.json` dans un volume de tâche.

Conséquence : toute solution qui donne au worker un secret violerait l’architecture. Toute solution qui conserve l’isolation actuelle doit rendre le LLM disponible via un canal authentifié hors du conteneur ou modifier les contrats réseau.

---

## 7. Comparaison des trois architectures

### Option A — Adapter TradingAgents pour utiliser directement Ollama

**Principe** : configurer le worker via `TRADINGAGENTS_LLM_PROVIDER=ollama`, `TRADINGAGENTS_QUICK_THINK_LLM` / `TRADINGAGENTS_DEEP_THINK_LLM` avec des modèles locaux, et mettre `OLLAMA_BASE_URL` ou `backend_url` selon l’infrastructure.

| Critère | Évaluation |
|---|---|
| Modifications | faibles : variables d’environnement, modèle, éventuellement réseau worker→Ollama |
| Fichiers concernés | `examples/quantar/quantar_task_runner.py`, `tradingagents/default_config.py`, compose/déploiement |
| Compatibilité agents | bonne pour Ollama sans secrets ; dépend du modèle pour tools/structured |
| Sécurité | bonne si réseau limité ; aucune clé nécessaire pour Ollama. Ne résout pas les fournisseurs cloud. |
| Maintenabilité | moyenne : duplique partiellement les variables d’env TradingAgents et reste couplée à ses formats |
| Performance | directe, faible latence si Ollama local |
| Limites | ne passe pas par ETHAN Provider Manager/HROT ; le worker accède directement au moteur ; hors isolation stricte si réseau autorisé |
| Tests | init LLM, génération, tool call, structured output, graphe complet sur modèle local |

Avantages :
- Utilise le support Ollama déjà présent.
- Aucune clé secrète transmise.
- Effort initial minimal.

Inconvénients :
- Contourne la gouvernance ETHAN pour les modèles.
- Non extensible aux fournisseurs secrets sans violer l’isolation.
- Difficulté de contrôler modèles et permissions centralement.

### Option B — Ajouter une couche d’adaptation compatible avec les interfaces LLM déjà utilisées

**Principe** : créer/adapter un client ou un adapter qui implémente l’interface LangChain attendue par TradingAgents (`get_llm`, `bind_tools`, `with_structured_output`, `invoke`) tout en utilisant un autre backend.

Deux sous-variantes :
- `B1` : adaptateur vers Ollama/ETHAN providers internes ;
- `B2` : adaptateur vers le Provider Gateway, faisant de l’ETHAN-backup la cible sécurisée.

| Critère | Évaluation |
|---|---|
| Modifications | moyennes à fortes : wrapper Python, payload tools/schemas, invocation multi-tours |
| Fichiers concernés | `tradingagents/llm_clients/*`, nouvel adaptateur, tests de contrat |
| Compatibilité agents | très bonne si l’interface est fidèle |
| Sécurité | dépend de la cible ; si cible gateway, bonne, si cible directe, moyenne |
| Maintenabilité | bonne si l’adaptateur est centralisé et testé |
| Performance | ajout de conversion et éventuel transport |
| Limites | réimplémenter une partie de l’écosystème LangChain ; gestion des messages `tool`, tool_choice, streaming |
| Tests | tests unitaires de l’adaptateur avec fakes, tests d’intégration Ollama, tests structured |

Avantages :
- Préserve au maximum TradingAgents tel quel.
- Crée une frontière claire entre application et ETHAN.
- Permet une future gateway sécurisée.

Inconvénients :
- L’interface LangChain est riche ; un adaptateur incomplet peut casser silencieusement.
- Risque de masquer les limitations des fournisseurs locaux.
- Travail d’ingenierie réel, pas seulement configuration.

### Option C — Appels via le Provider Gateway d’ETHAN (architecture cible)

**Principe** : TradingAgents ne connaît plus les secrets ; il obtient une autorisation HROT et utilise le gateway comme backend LLM.

| Critère | Évaluation |
|---|---|
| Modifications | fortes : extension du gateway, autorisation par tâche, transport worker↔gateway, adaptateur LangChain |
| Fichiers concernés | `core/security/hrot_provider_gateway.py`, `core/applications/quantar_provider_bridge.py`, `core/llm/provider_manager.py`, `core/llm/types.py`, adaptateur TradingAgents, tests gateway |
| Compatibilité agents | possible mais actuellement impossible directement car gateway textuel |
| Sécurité | la plus forte si correctement implémentée |
| Maintenabilité | bonne à long terme, mais demande évolution maîtrisée |
| Performance | dépend du transport ; in-process possible, conteneur impossible sans canal |
| Limites | pas d’outils/schéma/usage dans le gateway actuel ; pas de canal rede conteneur ; autorisation per-task à définir |
| Tests | unitaires gateway, HROT durable, adapter, conteneur |

Avantages :
- Respecte la contrainte claire : le conteneur ne reçoit jamais de secret.
- Réutilise Provider Manager et HROT au lieu de dupliquer.
- Permet audit et contrôle par provider/modèle/action.

Inconvénients :
- Cas le plus coûteux.
- Exige de redessiner le gateway autour de capacités complètes d’inférence, pas seulement du texte.
- Aucun canal worker↔gateway aujourd’hui.

---

## 8. Limitations et risques

1. **Défaut faux positif de capacité** : `_DEFAULT` dans `get_capabilities` attribue tool calling et JSON schema à Unknown/Ollama models. Certains modèles locaux ne les supportent pas.
2. **Perte de structuration** : structured output est optionnel ; en échec, les agents tombent en free-text, et les parsers de rating peuvent manquer la décision.
3. **Hypercouplage à LangChain** : TradingAgents suppose un Runnable/ChatModel avec `bind_tools`, PromptTemplate, ToolNode. Tout backend doit imiter cette surface.
4. **Isolation actuelle** : aucun chemin réseau Workers ↔ Gateway n’est défini.
5. **HROT incomplet** : le gateway possède ses propres autorisations et n’est pas branché au workflow durable existant comme le rapport phase 47 le confirme.
6. **Inférence de tool choice** : la suppression de `tool_choice` réduit la garantie que le structured call produise réellement un objet structuré.
7. **Modèles source de confusion** : les noms par défaut d’Ollama dans le catalog sont des noms curés (`qwen3:latest`, `gpt-oss:latest`, `glm-4.7-flash:latest`), pas nécessairement installés.
8. **Performances locale** : graphe multi-agent avec plusieurs analystes, débats et structured output peut être très lent sur de petits modèles locaux.
9. **Messages trop longs** : ProviderGateway limite le contenu à 32 000 caractères par message et 100 000 octets par requête. Analyses longues peuvent dépasser.
10. **Pas de streaming dans gateway** : si le gateway devient l’unique point de génération, les latences longues doivent être contrôlées (timeout 30 s actuellement).

---

## 9. Tests supplémentaires proposés et statut actuel

### Tests déjà réutilisables dans les dépôts

- `tradingagents/tests/test_ollama_base_url.py` : base_url, OLLAMA_BASE_URL, CLI, struct output `tool_choice=None`.
- `tradingagents/tests/test_openai_compatible_provider.py` et voisins : comportement provider registry.
- `tests/core/test_hrot_provider_gateway.py` : 14 tests validés (exécutés ici, succès).

### Tests réels réalisés dans cette mission

| Type | Sujet | Résultat |
|---|---|---|
| Unitaire existant | Provider Gateway ETHAN | 14 passed |
| Réel Ollama | `/v1` simple generation `llama3.2:3b` | passé |
| Réel Ollama | JSON object `response_format` | passé |
| Réel Ollama | JSON Schema | passé |
| Réel Ollama | Tool calling `tool_choice=required` | passé |
| Pas exécuté | TradingAgents graphe complet avec Ollama | aucune dépendance langchain/langgraph disponible à cet effet dans l’environnement courant |

### Tests nécessaires avant toute intégration

- test de construction `OpenAIClient(provider="ollama", model="llama3.2:3b")` et invocation simple ;
- test de tool calling avec les outils TradingAgents réels ;
- test structured output pour `ResearchPlan`, `TraderProposal`, `PortfolioDecision`, `SentimentReport` ;
- test fallback free-text ;
- test des modèles locaux candidats (tool calling, JSON schema, vitesse) ;
- test Quantar in-process avec `provider=ollama` ;
- test container réseau/endpoint sans secret ;
- test HROT durable authorize/consume ;
- test d’absence de fuite secret dans logs et `result.json`.

---

## 10. Architecture recommandée et justification

### 10.1 Recommandation

Recommander une **architecture cible en deux temps** :

1. **Court terme : Option A limitée à Ollama et à des réseaux internes contrôlés**, uniquement après qualification modèle par modèle.  
   Justification : Ollama n’a pas de secret, TradingAgents le supporte déjà, et aucune fuite de credential n’est possible. Cela débloque la validation fonctionnelle sans casser HROT ni dupliquer le Provider Manager, car le worker utilise un endpoint sans secret.

2. **Moyen terme : Option C, avec un adaptateur Option B ciblé**, pour que TradingAgents/Quantar utilise le Provider Gateway comme point unique de génération.  
   Justification : c’est la seule option qui respecte pleinement l’isolation du worker, l’absence de secrets dans le conteneur, et l’unicité de la gouvernance providers/permissions demandée par ETHAN.

### 10.2 Justification détaillée

- La source de vérité des providers est `ProviderManager` ; le gateway est la frontière de sécurité. Dupliquer une seconde logique provider serait une régression.
- Le gateway actuel ne peut pas servir TradingAgents directement. Il faut d’abord le faire passer de “texte only” à “capabilities d’inférence”.
- TradingAgents implémente déjà la résilience (`structured fallback`, `tool call limit`, `TokenChoice suppression`) ; ces mécanismes doivent être préservés lors du pont vers ETHAN.
- Ollama prouve que les primitives (chat, JSON schema, tools) sont disponibles localement.
- Pour les fournisseurs à secret (OpenAI, Anthropic, etc.), l’Option A n’est acceptable ni côté sécurité ni côté isolation.
- L’adaptateur B est le meilleur endroit où encapsuler LangChain et ses types, sans modifier le cœur ETHAN plus que nécessaire.

### 10.3 Préconditions avant de commencer

- Aucun changement HROT dans cette mission. Les modifications HROT nécessiteront une mission séparée et des tests dédiés.
- Le support outils et structured output doit être spécifié explicitement dans le gateway avant implementation.
- Le transport worker↔gateway doit être une décision architecture-approved (HTTP authentifié, socket orchester, ou exécution in-process orchestrée par un service ETHAN).
- Le modèle Ollama à utiliser doit être qualifié par des tests réels.

---

## 11. Plan d’implémentation découpe en missions indépendantes

### Mission 18 — Qualification modèle Ollama
- Objectif : qualifier les modèles locaux candidats.
- Livrables : matrice par modèle (simple generation, outils, structured, temps/token).
- Fichiers/tests : `tradingagents/llm_clients/capabilities.py`, scripts de test isolés.
- Ne pas télécharger de nouveau modèle sans autorisation.

### Mission 19 — durcissement des capacités Ollama
- Objectif : remplacer l’entrée `_DEFAULT` opaque par une politique explicite pour Ollama.
- Points : `get_capabilities`, modèle inconnu, `LocalCompatibleChatOpenAI`.
- Tests : unitaires capacités et structured output.

### Mission 20 — spécification du gateway capabilities
- Objectif : étendre le contrat `ProviderGateway` aux outils et au JSON Schema.
- Points : `ALLOWED_MESSAGE_ROLES` inclure `tool`, ajouter tool schema, `tool_choice`, `Structured output`, métadonnées réponse.
- Conserver HROT et sécurité.

### Mission 21 — adaptateur LangChain→Gateway (PoC)
- Objectif : prouver qu’un adapter peut fournir `bind_tools`, `with_structured_output`, `invoke`.
- Tests : fakes, conversion message, validation json.

### Mission 22 — branchement durable HROT
- Objectif : faire passer les autorisations providers par `DurableHrotStore` et `HumanRoot`.
- Tests : autorisation, consommation, mismatch, expiration.

### Mission 23 — transport container
- Objectif : définir et qualifier un canal worker↔gateway sans secrets.
- Points : réseau, auth, timeout, rate limit.
- Tests : container, régression isolation, non-exposition.

### Mission 24 — validation bout en bout Ollama/Quantar
- Objectif : exécuter une vraie analyse Quantar avec `provider=ollama`, sans secret.
- Tests : graphe complet, result.json, absence secret dans logs.

---

## 12. Hypothèses et points à confirmer

- Les tests du framework TradingAgents n’ont pas pu être exécutés localement faute de dépendances installées dans le dépôt. Les affirmations sur l’endpoint Ollama reposent sur l’audit de code et des tests HTTP directs.
- Les modèles réellement installés ne correspondent pas aux noms du catalog TradingAgents ; l’option `custom` est requise.
- L’état exact du network Quantar container n’a pas été testé dynamiquement, mais la configuration `network_mode="none"` est documentée et observable dans le code.
- La sécurité réelle du gateway en conteneur n’est pas prouvée ; les documents de phase 47 le confirment.
- Le rapport suppose que l’intégration future respectera la règle de ne pas dupliquer Provider Manager, permissions ou HROT.

---

## 13. Statut du critère de fin

Cette mission d’audit est terminée du point de vue documentation : le mécanisme TradingAgents, ses dépendances, ses besoins LLM, sa compatibilité Ollama et la stratégie d’intégration ETHAN sont documentés avec des preuves. Les points bloquants restants sont volontairement présentés comme des missions d’implémentation : extension des capacités du gateway, transport conteneur, qualification fine par modèle et branchement durable HROT. Aucune intégration n’a été commencée.
