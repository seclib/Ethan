# ETHAN WebUI — état actuel vérifié

**Date :** 13 août 2026  
**Révision ETHAN inspectée :** `c9252ca87493d0b291ba1289fa077c7ab87b86d1` (`Fix webui`)  
**Portée :** audit sans changement structurel de `interfaces/webui/`, Core, API,
Runtime/Compose, plugins et `examples/open-webui/`.

## Résumé exécutif

ETHAN dispose aujourd'hui d'une WebUI Next.js distincte d'Open-WebUI. Ce n'est
ni un fork, ni une adaptation de ses composants : `interfaces/webui/` est une
application React/Next construite séparément, tandis que `examples/open-webui/`
est un dépôt Git imbriqué, ignoré par le dépôt parent, déjà modifié localement.

La frontière d'architecture visée est globalement bonne : navigateur → proxy
Next.js → API FastAPI → managers/stores Core. Les routes API et les capacités
Core ont beaucoup progressé. En revanche, la WebUI ne peut pas encore être
qualifiée de client fonctionnel complet : plusieurs écrans visibles sont des
démos locales, plusieurs contrats UI/API divergent, le WebSocket ne correspond
à aucune route serveur, et un second jeu de domaines « WebUI » reproduit des
concepts déjà possédés par le Core.

La décision d'architecture à prendre avant toute refonte est donc claire :
**adopter Open-WebUI comme nouvelle interface de référence**, et conserver
l'API/Core ETHAN comme unique backend. Il ne faut pas tenter d'achever en
parallèle la WebUI Next existante et le bridge partiel dans `examples/open-webui`.

## 1. Architecture actuelle

### Chemin HTTP réellement implémenté

```text
Navigateur
  │  /api/* ; cookie HttpOnly ethan_token
  ▼
interfaces/webui (Next.js 15, React 19)
  └─ src/app/api/[...path]/route.ts
       - retire /api
       - transmet le JWT comme Authorization: Bearer
       - crée/supprime le cookie de l'origine Next après login/refresh/logout
  ▼
interfaces/api/main.py (FastAPI :8000)
  └─ middleware JWT + routers
       - /v1/*, /providers, /config, /chats, /files, /users, /groups
  ▼
Core managers et stores
  └─ CoreRecordStore (PostgreSQL + Redis, repli mémoire), ProviderManager,
     ConfigurationService, agents, missions, knowledge, RAG, etc.
```

Le `docker-compose.yml` racine est la topologie active : API Python, kernel
Python (`core/ethan_bootstrap.py`), modules Python, NATS, PostgreSQL, Redis et
UI. Le chemin `runtime/` n'existe pas dans ce checkout ; « Runtime » est une
responsabilité répartie entre le kernel, `core/modules/`, l'orchestrateur et
Compose. Le `core/README.md`, qui décrit un runtime Go/Gin et des fichiers Go
absents, est obsolète.

### Composition et persistance

Au démarrage FastAPI compose les dépendances mais ne devrait pas porter de
métier : `CoreRecordStore` est injecté dans les managers Agents, Missions,
Knowledge et RAG, puis dans Chats/Fichiers/Utilisateurs/Groupes. Douze
capacités supplémentaires sont également composées dans `CapabilityManagers`
(automations, calendrier, audio, images, évaluations, analytics, channels,
notes, serveurs d'outils, fonctions/pipelines, prompts, SCIM).

Cela respecte le principe ETHAN pour ces domaines. Le repli mémoire du store
reste intentionnel pour les environnements sans PostgreSQL/Redis, donc il ne
constitue pas une promesse de durabilité en mode dégradé.

## 2. État réel de la WebUI ETHAN

### Ce qui existe et est relié au backend

| Zone | État vérifié | Chaîne |
|---|---|---|
| Login / logout / refresh | Implémenté | Next proxy → `/auth/*` FastAPI → JWT/DB |
| Protection de routes | Implémentée | `middleware.ts` teste le cookie, FastAPI valide le JWT |
| Providers | API et écran connectés | `/api/providers` → `ProviderManager` |
| Agents | Liste, création, mise à jour, suppression | `/api/v1/agents` → `AgentManager` |
| Missions | API Core disponible ; écran bloqué par contrat | `/api/v1/missions` → `MissionManager` |
| Knowledge | Liste/recherche affichables | `/api/v1/knowledge` → `KnowledgeManager` |
| Documents RAG | Liste et ingestion texte | `/api/v1/rag/documents` → `RAGPipeline` |
| Conversations | CRUD de conversations et messages | `/api/chats` → `core/state/chats.py` |
| Capacités Open-WebUI-like | API exposée, pas d'écrans dédiés | `/v1/automations`, calendrier, audio, images, etc. |

La vérification locale du 13 août a fait passer `npm run typecheck`, `npm run
lint`, `npm test -- --runInBand` (5 suites, 7 tests) et `npm run build` (23
routes générées). Le build valide TypeScript et le rendu statique ; il ne valide
pas les contrats HTTP ou les boutons métier.

Le Compose actif était sain lors de l'audit et son OpenAPI exposait 126 chemins,
dont `/providers`, `/v1/goals`, `/v1/chat`, les domaines WebUI et les douze
capacités. Les appels non authentifiés via l'UI et directement via l'API
retournaient tous deux 401 : le proxy actif pointe donc bien vers l'API active.
Les parcours authentifiés n'ont pas été rejoués : aucun compte de test n'a été
créé ou utilisé par cet audit.

### Authentification à préserver, avec réserve

Le login existant doit être conservé : il utilise le cookie HttpOnly
`ethan_token`, le proxy Next le convertit en Bearer et le middleware FastAPI
vérifie le JWT. C'est le bon point de départ pour Open-WebUI.

Deux limites doivent être corrigées avant de considérer le flux complet :

1. `/auth/register` retourne un JWT mais n'écrit aucun utilisateur ni hash de
   mot de passe en base. Un compte enregistré ne peut donc pas se reconnecter
   par `/auth/login`.
2. `/auth/login` calcule le rôle depuis PostgreSQL pour le JWT, puis retourne
   pourtant `user.role: "user"` dans sa réponse. L'état React créé juste après
   un login peut donc ne pas refléter le rôle réel.

### Fonctions visibles mais non fonctionnelles ou incomplètes

| Écran / action | Constat dans le code | Conséquence |
|---|---|---|
| Dashboard | Boutons New Mission, Pause/Kill/View et Quick Actions sans `onClick` | Actions mortes |
| Planner | tâches fixes en `useState`; Pause/Run sans action | Démo, pas orchestration Core |
| Models | liste fixe en `useState` | Ne reflète aucun provider/modèle ETHAN |
| Plugins | liste et toggle locaux | Ne gère pas `plugins/manager.py` |
| Terminal | ajoute `[$ input]: executed` localement | N'exécute aucun shell ou outil ETHAN |
| Logs | `DEMO_LOGS` et Clear local | Pas d'observabilité réelle |
| Memory | UI attend une enveloppe `{data}` ; l'API renvoie une liste | Faits affichés vides ; recherche/filtres/export/detail sont des placeholders |
| Missions / Skills | hooks attendent `{data}` ; API renvoie brut | Listes vides malgré une réponse API valide |
| Goals | type UI exige `tasks`; le store renvoie un goal sans `tasks` | `/planner/goals` peut lever une erreur dès qu'un goal existe |
| Assistant | sidebar persiste dans `ChatStore`, génération dans `/v1/chat` et `CoreWebUIStore` | Deux historiques et deux sources de vérité pour la même conversation |
| Temps réel | client tente `ws://…/api/v1/ws`; aucune route WebSocket n'est déclarée dans API/Core | reconnect/heartbeat sans serveur compatible |

Le composant et les styles peuvent donc être réemployés comme référence locale,
mais aucun écran ne doit être jugé « fait » sur la seule base de son rendu.

## 3. État réel d'Open-WebUI

`examples/open-webui/` est Open-WebUI 0.9.1 (commit
`0a8a620fb6fd4c914494f56ac06475bd5f95a985`, 21 avril 2026). C'est une
application complète SvelteKit/Vite + FastAPI/SQLAlchemy, avec 30 routers
backend et 46 routes Svelte. Elle possède son propre backend, ses propres
modèles de données et ses propres mécanismes d'authentification, stockage,
RAG, outils et providers.

Elle n'est pas suivie par le Git parent (`examples/` est ignoré), mais elle est
bien un dépôt Git imbriqué avec son propre `origin` Open-WebUI. Elle n'est pas
propre : cinq fichiers suivis sont modifiés, un compose est supprimé et un
client ETHAN non suivi est ajouté. Ce n'est donc pas une référence immuable ni
un fork ETHAN publiable en l'état.

Les modifications locales tentent de remplacer une partie des routes auth,
chats et OpenAI par `services/ethan_client.py`. Elles sont incomplètes et ne
peuvent pas fonctionner contre l'API ETHAN actuelle : ce client appelle des
chemins `/api/auth/*` et `/api/chats/*`, alors que FastAPI ETHAN expose
`/auth/*` et `/chats/*`; le préfixe `/api` n'existe que côté navigateur dans le
proxy Next. Il réduit également les messages au dernier prompt et remplace des
contrôles Open-WebUI (accès modèles, outils, multimodalité) sans contrat ETHAN
équivalent vérifié.

**Conclusion :** Open-WebUI est une excellente base UX/fonctionnelle, mais son
backend ne doit pas être conservé comme seconde source de vérité et le bridge
local ne doit pas être pris comme point de départ fiable sans redéfinir les
contrats.

## 4. Différences ETHAN / Open-WebUI

| Sujet | ETHAN actuel | Open-WebUI de référence |
|---|---|---|
| Frontend | Next.js/React | SvelteKit/Svelte |
| Backend de l'UI | proxy Next vers FastAPI ETHAN | FastAPI intégré + SQLAlchemy |
| Source de vérité | Core/Runtime ETHAN, partiellement dupliqué | Modèles et DB Open-WebUI |
| Chat | deux chemins (`/chats` et `/v1/chat`) | chat, historique et complétion cohérents |
| Providers / modèles | `ProviderManager`, UI Providers seulement | catalogue, accès, administration et UX riches |
| RAG / mémoire | Core existe ; surfaces UI partielles | flux documents/knowledge/memory mature |
| Tools, functions, pipelines | API désormais disponible, UI absente | surfaces d'administration et d'usage existantes |
| Auth | JWT ETHAN/proxy cookie | auth Open-WebUI à remplacer par JWT ETHAN |
| Temps réel | client sans endpoint | mécanisme intégré à son application |

La compatibilité ne peut donc pas être obtenue par un copier-coller de
composants : la migration implique Svelte → React, ou l'adoption d'Open-WebUI
comme application frontend avec un adaptateur ETHAN. Dans les deux cas, le
contrat ETHAN doit être défini avant les écrans.

## 5. Fonctionnalités déjà présentes

### Capacités Core/API disponibles

Agents, missions, knowledge, RAG, providers, configuration, chats, fichiers,
utilisateurs, groupes, facts/memory, skills, flux, goals, plugins et les douze
capacités énumérées plus haut disposent d'un module Core et/ou d'une route
FastAPI. Les routes déclarées sont visibles dans l'OpenAPI local actif.

Cette présence ne signifie pas que chaque capacité est implémentée de bout en
bout : les endpoints `goals`, `facts`, `skills`, flux, providers legacy et
plugins passent par `CoreWebUIStore`, pas par les managers spécialisés
`core/goals`, `core/facts`/`core/memory`, `core/skills`, `ProviderManager` et
`plugins/manager.py`.

### Capacités UX disponibles

La WebUI possède un shell de dashboard, sidebar, thème, palette de commande,
inspector, animations, providers React Query, assistant, sélection de modèle,
documents RAG, agents, missions et le login ETHAN. Ce sont des fondations UI,
pas un verdict de fonctionnalité métier.

## 6. Manques à combler

1. Un contrat versionné et cohérent pour les réponses API (brut ou enveloppe,
   jamais les deux) et les types TypeScript dérivés de ce contrat.
2. Une intégration conversationnelle unique : chat, messages, génération,
   documents, mémoire et outils doivent partager un `conversation_id` Core.
3. Des gateways API vers les vrais managers Core pour goals, facts/memory,
   skills, providers et plugins ; pas des copies génériques WebUI.
4. Un endpoint et un protocole temps réel ETHAN, ou la suppression temporaire
   de la promesse WebSocket.
5. Les surfaces Open-WebUI prioritaires : conversations, gestion modèles et
   providers, fichiers/RAG, outils/MCP/functions/pipelines, administration et
   observabilité. Les routes API existent majoritairement, les vues non.
6. Des tests de contrats UI → proxy → API → Core, puis des E2E authentifiés
   utilisant un compte de fixture.

## 7. Dette technique et incohérences

### P0 — à traiter avant une migration UI

- Les contrats de réponse cassent Missions, Memory et Skills ; Goals peut
  planter avec des données créées par l'API.
- Deux chemins de conversation divergent dans l'Assistant.
- Le bridge Open-WebUI non suivi cible des URLs inexistantes et n'a pas de
  contrat de compatibilité.
- L'inscription n'est pas persistée ; ce flux ne peut pas être conservé comme
  fonctionnel sans correction backend.

### P1 — frontière Core/API et sécurité d'exploitation

- `CoreWebUIStore` a déplacé l'état hors du router, ce qui est une amélioration,
  mais il duplique encore providers et plugins par défaut et contourne plusieurs
  managers spécialisés.
- Providers existent à la fois dans `/providers` (réel `ProviderManager`) et
  `/v1/providers` (records WebUI) ; leurs données peuvent diverger.
- Le `docker-compose.yml` local de `interfaces/webui/` est une topologie
  différente et vieillie : il pointe vers `localhost:8080`, alors que le Compose
  racine actif utilise `api:8000`. Il est syntaxiquement valide mais ne doit pas
  servir de déploiement de référence.
- L'interface stocke `ethan.current-chat-id` et l'utilisateur `anonymous` côté
  client. Le premier est de préférence UI acceptable ; le second ne doit pas
  gouverner les données métier.

### P2 — qualité et maintenabilité

- Nombreux `any`, doublon/ambivalence de services API, et écrans mock.
- Seulement 7 tests unitaires WebUI ; les E2E présents ne couvrent pas le
  backend réel authentifié ni les mutations importantes.
- Les artefacts `.next/` sont suivis par Git, ce qui rend les validations build
  bruyantes et fragiles.

## 8. Risques

| Risque | Impact | Mesure |
|---|---|---|
| Réécrire la WebUI sans contrat Core | Haut | stabiliser contrats et ownership avant composant/page |
| Garder deux backends (ETHAN + Open-WebUI) | Haut | Open-WebUI frontend seulement ; backend ETHAN seul |
| Continuer deux chats | Haut | consolider sur un modèle Core de conversation |
| Fausse confiance issue du build | Haut | E2E authentifiés et tests de contrats obligatoires |
| Référence Open-WebUI modifiée/non suivie | Moyen | rendre le fork explicite, propre et reproductible |
| Documentation historique prise pour l'état actuel | Moyen | ce document prévaut jusqu'au prochain audit de code |

## 9. Documentation vérifiée

La recherche plein texte a recensé 140 Markdown mentionnant WebUI, Open-WebUI,
frontend, auth ou architecture. Ils ont été confrontés au code et aux manifests
pour les affirmations exploitables. Les documents de proposition ou de rapport
historique restent utiles comme contexte, mais ne sont pas des sources de
vérité.

| Documents | Verdict actuel |
|---|---|
| `docs/audit/WEBUI_CURRENT_STATE.md` précédent | Remplacé : il annonçait à tort Open-WebUI propre/non suivi, des capacités API absentes et une WebUI prête à la production. |
| `docs/audit/ETHAN_WEBUI_GAP_ANALYSIS.md`, `WEBUI_PRIORITIES.md`, `WEBUI_IMPLEMENTATION_STATUS.md` | Partiellement obsolètes : beaucoup de routes/capacités ont été ajoutées, mais leurs problèmes de contrats ne sont pas résolus. |
| `docs/audit/OPENWEBUI_FUNCTIONAL_REFERENCE.md`, `OPENWEBUI_FORK_FEASIBILITY.md` | Référence/faisabilité à conserver, mais à lire avec l'état Git modifié de `examples/open-webui`. |
| `docs/architecture/OPENWEBUI_TO_ETHAN_API_MIGRATION.md`, `docs/development/ETHAN_WEBUI_FORK_STRATEGY.md` | Propositions, pas état d'implémentation : elles décrivent un fork/bridge qui n'existe pas dans `interfaces/webui`. |
| `interfaces/webui/README.md`, `API_CLIENTS.md`, `FRONTEND_COMPONENTS.md`, `WEBUI_ROADMAP.md` | Obsolètes : chemins, auth Bearer/localStorage, composants et actions planifiées ne correspondent plus au code. |
| `ETHAN_WEBUI_AUDIT_FINAL.md`, `MIGRATION_STATUS.md`, `SCORECARD.md`, `PRODUCTION_CHECKLIST.md` | Validation historique de rendu/build seulement ; le verdict « production » n'est pas soutenu par les contrats actuels. |
| `docs/AUTH_FINAL_VALIDATION.md`, `frontend_auth_audit.md`, `auth_flow_audit.md`, `DOUBLE_AUTH_AUDIT.md`, `AUTH_ARCHITECTURE.md` | Les bugs de proxy historiques sont corrigés, mais les rapports ne couvrent pas la persistance actuelle de register ni le rôle de réponse login. |
| `README.md`, `core/README.md`, `docs/architecture/current.md` et les audits/roadmaps généraux | À considérer historiques : ils décrivent notamment un runtime Go, des dossiers et des modules absents, ou des capacités désormais présentes. |

## 10. Prochaines étapes recommandées — sans refonte immédiate

1. **Geler et tester les contrats** : générer les types depuis OpenAPI, choisir
   les réponses brutes ou enveloppées, corriger les hooks et ajouter les tests
   proxy/API/Core de Goals, Missions, Facts, Skills et Chat.
2. **Rétablir l'ownership Core** : supprimer progressivement les doublons de
   `CoreWebUIStore` au profit des managers spécialisés ; décider explicitement
   si Goals est `core/goals` ou `core/planner`, une seule fois.
3. **Consolider l'auth et les conversations** : persister register, propager le
   vrai utilisateur/role, unifier l'historique et définir le WebSocket/event
   protocol ETHAN.
4. **Assainir la référence Open-WebUI** : créer un fork ETHAN suivi, sans
   modifications non versionnées, et isoler un adaptateur API ETHAN testé. Ne
   pas porter les routes Open-WebUI une à une dans son backend.
5. **Seulement ensuite, refondre l'interface** : conserver le login ETHAN,
   adopter les flux et la UX Open-WebUI par incréments (chat, sidebar,
   documents/RAG, modèles/providers, outils/MCP, administration), chaque écran
   étant branché sur une capacité ETHAN déjà testée.

## Méthode et limites

Inspection statique de `core/`, `interfaces/api/`, `interfaces/webui/`,
`plugins/`, `docker-compose.yml` et `examples/open-webui/`; OpenAPI de l'API
Compose active ; validation de configuration Compose ; compilation Python ;
typecheck, lint, tests unitaires et build WebUI. Aucune donnée métier ni compte
n'a été créé/modifié. L'audit n'établit donc pas le succès d'un parcours
authentifié, d'un provider externe ou d'une exécution LLM réelle.
