# WebUI — Cartographie UX (route → composant → API → Core)

> **Date** : 2026-09-30 · **Rôle** : Lead Product Architect + Senior UX Engineer
> **Périmètre** : `interfaces/webui` uniquement — **aucune modification Core**
> **Port dev** : WebUI sur **3001** (inchangé)
> **Règle** : AGENTS.md — « Les interfaces révèlent ETHAN ; elles ne le définissent
> pas ». Aucune logique métier dans cette carte : elle décrit du **lien**, pas du
> comportement.
>
> **Méthode** : inventaire généré depuis le source (pages `src/app/**/page.tsx`,
> imports `@/lib/api/*`, décoration `@router.*` des routeurs FastAPI,
> imports `core.*` de `interfaces/api/routers/*.py`), puis revue manuelle.
> **Aucune suppression ni fusion sans apparaitre dans la section 5.**

---

## 1. Inventaire des routes

Légende menu : **S** = sidebar (PRIMARY/ADMIN) · **P** = palette Ctrl+K / en-tête
(SECONDARY) · **G x** = séquence clavier · **—** = route profonde sans entrée.

| Route | Page → composant racine | Client(s) API (endpoints) | Routeur FastAPI → service Core | Menu |
|---|---|---|---|---|
| `/` | `page.tsx` → `AssistantChat` + `ChatSecondaryBar` + `ChatContextBar` + `ChatSections` + `PluginPicker` | `chat`, `files`, `knowledge`, `skills`, `tools`, `plugins`, store `projects` | `openwebui.py`/`v1.py` → `core/chat` (ChatPipeline) ; `v1.py` → `core/skills`, `core/tools`, `core/plugins` | S (CONVERSATIONS) · G a |
| `/agents` | `AgentsWorkspace` | `agents` → `/v1/agents*` | `v1.py` → `core/agents` | S · P · G e |
| `/projects` | `ProjectsList` | `projects` → `/v1/projects` | `projects.py` → `core/projects` | S |
| `/projects/[id]` | `ProjectWorkspace` (4 onglets) | `projects` → `/v1/projects/{id}` + `/context` | `projects.py` → `core/projects` | — |
| `/projects/[id]/files` | `FileUploadDropzone` + `ProjectFilesTable` | `projects` → `/v1/projects/{id}/documents` | `projects.py` → `core/projects` | — |
| `/missions` (+ `/runs`, `/connections`) | page + `use-missions`/`use-goals` | `missions`, `goals`, `connections` | `v1.py` → `core/missions`, `core/goals` ; `connections.py` → `core/integrations.connections` | S · G m |
| `/missions/{settings,templates,workflows}` | `WorkspacePlaceholder` (`planned: true`) | — | — | nav interne Missions |
| `/calendar` | page + `lib/api/capabilities` | `/v1/calendar*` | `capabilities.py` → capability managers (calendar) | S |
| `/notes` | page + `lib/api/capabilities` | `/v1/notes*` | `capabilities.py` → capability managers (notes) | S |
| `/inbox` | page + `lib/api/extensions` | `/v1/email/messages*` | `email.py` → `core/mailbox.manager` | S |
| `/research` | page + `lib/api/extensions` | `/v1/research` | `research.py` | S |
| `/automations` | `AutomationsWorkspace` | `automations` → `/v1/automations*` | `capabilities.py` → capability managers (automations) | S |
| `/cookbook` | page + `lib/api/extensions` | `/v1/cookbook*` | `cookbook.py` → `core/cookbook` | S |
| `/diagnostics` | page + `lib/api/diagnostics` | `/diagnostics`, `/health/detailed` | `diagnostics.py` → `core/diagnostics` | S (ADMIN) |
| `/logs` | `AuditExplorer` | `/internal/audit/search` | `internal.py` → `core/audit` | S (ADMIN) |
| `/analytics` | page + `lib/api/analytics` | `/v1/analytics/summary`, `/v1/evaluations` | `capabilities.py` → capability managers (analytics/evaluations) | S (ADMIN) |
| `/groups` | page + `groups`, `security` | `/groups*`, `/users*` | `domains.py` → `core/auth` (groups/users) | S (ADMIN) |
| `/plugins` | page + `lib/api/plugins` | `/v1/plugins*` | `v1.py` → `core/plugins` | S (ADMIN) |
| `/connections` | page + `lib/api/connections` | `/connections*` | `connections.py` → `core/integrations.connections` | S (ADMIN) |
| `/monitoring` | page + `lib/api/diagnostics` (+ Grafana :3002) | `/diagnostics*` | `diagnostics.py` → `core/diagnostics` | S (ADMIN) |
| `/security` | page + `lib/api/security` | `/auth/2fa/*`, `/security/status`, `/api-keys`, `/internal/audit` | `security.py`/`api_keys.py`/`internal.py` → `core/auth.totp`, `core/security.status`, `core/audit` | S (ADMIN) |

| `/providers` | `ProvidersWorkspace` | `providers` → `/providers*` | `providers.py` → `core/llm.provider_manager`, `provider_factory` | P · G p |
| `/models` | `ModelsWorkspace` | `models` → `/models*` | `models.py` → `core/llm.model_store` | P · G n |
| `/gallery` | **état vide honnête** (aucun `/v1/gallery` en Core) | — | — | — *(entrée retirée du menu, R5)* |
| `/knowledge` | `KnowledgeHub` | `knowledge`, `rag`, `web-*` → `/v1/knowledge*` | `knowledge_imports.py`/`v1.py` → `core/knowledge`, `core/rag` | P · G k |
| `/library` | `LibraryWorkspace` | `library` → `/files`, `/v1/knowledge*`, `/v1/rag/documents` | `v1.py` → `core/knowledge`, `core/state.files` | P · G l |
| `/workspace` (Memory) | page + `use-memory`/`use-flux`/`use-goals` | `memory`, `flux`, `goals` → `/v1/memory*`, `/v1/flux`, `/v1/goals` | `v1.py` → `core/memory`, `core/flux`, `core/goals` | P (« Memory ») · G d |
| `/folders` | `FoldersWorkspace` | `folders` → `/v1/folders*` | `folders.py` → `core/folders` | P |
| `/domains` | `DomainsWorkspace` | `domains` → `/v1/domains*` | `core_domains.py` → `core/domains` | P |
| `/dedup` | `DedupWorkspace` | `dedup` → `/v1/dedup*` | `dedup.py` → `core/dedup` | P |
| `/skills` | `SkillsWorkspace` | `skills` → `/v1/skills*` | `v1.py` → `core/skills` | P |
| `/skills/lab` | `SkillsLabWorkspace` | `skills` → `/v1/skills/lab/*` | `v1.py` + `internal.py` → `core/skills.lab` | P |
| `/tools` | `ToolsWorkspace` | `tools` → `/v1/tools*` | `v1.py`/`capabilities.py` → `core/tools` | P · G t |
| `/mcp` | `McpServersWorkspace` | `mcp` → `/v1/tools/servers*` | `v1.py` → `core/tools` (serveurs MCP) | P |
| `/prompts` | `PromptsWorkspace` | `prompts` → `/v1/prompts*` | `capabilities.py` → capability managers (prompts) | P |
| `/channels` | `ChannelsWorkspace` | `channels` → `/v1/channels*` | `capabilities.py` → capability managers (channels) | P |
| `/settings` | `SettingsWorkspace` (21 sections, 8 groupes) | 15 clients (§2) | 12 routeurs (§2) | P · G s |
| `/(auth)/login`, `/(auth)/register` | `LoginForm` / formulaire | `auth-provider` | `interfaces/api/auth.py` | — |

**Constat** : chaque lien de la taxinomie pointe une route réelle de l'App
Router (`internal-links.test.ts`, garde-fou anti-fantôme) et chaque entrée de
menu une destination unique (`nav-dedup.test.ts`, §9).

---

## 2. Settings — 21 sections / 8 groupes

Arborescence **validée** (§6). Motif répété partout : la section Settings est un
**résumé + lien workspace** (`WorkspaceLink`), jamais une seconde implémentation.

| Groupe | Section | Composant | Client API → endpoints | Routeur → service Core |
|---|---|---|---|---|
| General | Chat | `ChatSection` | store `chat-mode` (intent envoyé au Core) | `openwebui.py`/`v1.py` → `core/chat` |
| General | Reminders | `RemindersSection` | `reminders` → `/reminders*` | `reminders.py` → `core/reminders` |
| General | Shortcuts | `ShortcutsSection` | registre UI (`G_SEQUENCE_ROUTES`) | — (présentation) |
| General | Library | `LibrarySection` | `library` + préférence consommée par `/library` | `v1.py` → `core/knowledge` |
| AI | Providers | `ProvidersSection` | `providers` → `/providers*` | `providers.py` → `core/llm.provider_manager` |
| AI | Models | `ModelsSection` | `models` → `/models*` | `models.py` → `core/llm.model_store` |
| AI | Model Routers | `ModelRoutersSection` | `rag`/`components` → `/v1/rag/*` | `v1.py` → `core/rag` |
| AI | Speech-to-Text | `SpeechToTextSection` | `audio` → `/v1/audio/*` | `v1.py` → TTS Core |
| Knowledge | Knowledge | `KnowledgeSection` | `knowledge` → `/v1/knowledge*` | `knowledge_imports.py` → `core/knowledge` |
| Knowledge | RAG | `RagSection` | `rag` → `/v1/rag/config|status|strategies` | `v1.py` → `core/rag` |
| Knowledge | Embeddings | `EmbeddingsSection` | `rag` | `core/rag` (embeddings) |
| Knowledge | Vector Database | `VectorDatabaseSection` | `rag` | `core/rag` (vector store) |
| Knowledge | Text Splitting & Chunking | `ChunkingSection` | `rag` | `core/rag` (ingestion) |
| Knowledge | Retrieval & Reranking | `RerankingSection` | `rag` | `core/rag` (retrieval) |
| Knowledge | Search | `SearchSection` | `search` → `/v1/search`, `/v1/search/types` | `search.py` → `core/search` |
| Skills | Skills | `SkillsSection` | `skills` → `/v1/skills*` | `v1.py` → `core/skills` |
| Integrations | Integrations | `IntegrationsSection` | `integrations` → `/integrations*` | `integrations.py` → `core/integrations` |
| Security | Security | `SecuritySection` | `security` → `/auth/2fa/status`, `/security/status` | `security.py` → `core/auth.totp`, `core/security.status` + lien `/security` |
| Appearance | Appearance | `AppearanceSection` | thème/accents (préférence locale UI) | — (affichage) |
| Advanced | System | `SystemSection` | `diagnostics` → `/health/detailed` | `diagnostics.py` → `core/diagnostics` |
| Advanced | Capabilities | `CapabilitiesSection` | `components` → `/v1/components/*` | `component_lifecycle.py` → `core/capability_manager` |

---

## 3. Le chat est le centre

| Exigence du brief | Composant | Câblage (état / payload) | Preuve (test) |
|---|---|---|---|
| Nouveau chat | sidebar `sidebar-new-chat` → `handleNewChat` | `createChat(title, activeProjectId)` — chat du scope projet | `chat.spec.ts`, `ChatSecondaryBar.test.tsx` |
| Sélection **Project** | `ChatSecondaryBar` → `ProjectSelector` | store `projects` (Core `/v1/projects`, `setActiveProject`) | E2E scénarios 1–2 |
| **Modèle** | `ChatSecondaryBar` → `ModelSelector` compact | store `model` → payload `model`/`provider_id` | E2E scénario 3 |
| **Agent** | `ChatSecondaryBar` → `AgentSelector` | store `agent` → payload `agent_id`/`metadata.agent_id` | E2E scénario 4 |
| **Mode** (plan/act/debug + effort) | composer → `ChatModeToggle` | store `chat-mode` → payload `mode`, `reasoning_effort` — **l'intent** part au Core, qui arbitre | `settings-chat-defaults` |
| **Attachments** | composer → `AssistantInput` (picker natif) | upload `POST /files` (Core) → payload `file_ids` | E2E scénario 5 |
| **Contexte Project** | `ChatContextBar` (outils/skills/connaissances/plugins/mémoire) + scope des conversations | payload `project_id`, `knowledge_ids`, `collection_ids` ; `loadChats(activeProjectId)` isole l'historique | E2E scénario 2 |
| Capacités résolues visibles | `ChatContextBar` | union (agent ∪ composer) = mêmes règles que `core/chat/pipeline.py` ; id non résoluble = jamais affiché | tests unitaires composant |

**Non-dupliqué** : sélecteurs = **UNE** position (barre secondaire) ·
mode = **UNE** position (composer) · contexte = **UNE** position (barre de
contexte) · titre = **UNE** position (barre secondaire).

---

## 4. Projects — les 6 facettes du brief

| Facette | Onglet | Composant | API → Core |
|---|---|---|---|
| Conversations | **Conversations** | liste + « New conversation » + « Open in chat » | `createChat(project_id)` → `core/chat` (scope projet) |
| Instructions | **Instructions** | éditeur `instructions` | `PATCH /v1/projects/{id}` → `core/projects` |
| Fichiers | **Fichiers** | `FileUploadDropzone` + `ProjectFilesTable` | `/v1/projects/{id}/documents` → `core/projects` |
| Knowledge | **Configuration** (checklist Knowledge) | `CheckList` sur `knowledge_ids` | `PATCH knowledge_ids/collection_ids` → portée RAG lue par `core/chat/pipeline.py` |
| Modèle par défaut | **Configuration** | selects `provider`/`model` | `PATCH provider_id`, `model` — défauts appliqués par le Core si la requête ne précise rien |
| Agent par défaut | **Configuration** | select `agent_id` | `PATCH agent_id` → routage Core |

*Choix validé* : Knowledge/Skills/Tools vivent dans **Configuration** — ce sont
des **défauts d'exécution**, pas du contenu. Un onglet « Knowledge » séparé
recréerait le doublon que le brief interdit (deux endroits pour la même
capacité). La ligne de partage est **contenu ⇄ défaut d'exécution**.

---

## 5. Redondances trouvées → décisions

| # | Symptôme (preuve) | Décision | Statut |
|---|---|---|---|
| **R1** | Deux entrées de menu pour UNE destination : `Settings` et `Interface` → `/settings` et `/settings#appearance` (après normalisation : `/settings` ×2) | **Suppression de l'entrée « Interface »** ; le hash reste supporté comme lien profond (E2E/docs) | ✅ **fait ce lot** |
| **R2** | Deux composants rendant les mêmes sélecteurs (projet/agent/provider/modèle) : `AssistantTopBar` (jamais importé) vs `ChatSecondaryBar` | **Suppression du code mort** + correction des commentaires qui le désignaient comme actif | ✅ **fait ce lot** |
| **R3** | Menus historiques `Models / AI Models / LLM / Model Configuration` (motif cité par le brief) | Vérifié **absent** du source actuel ; verrouillé par `nav-dedup.test.ts` (libellés + destinations uniques) | ✅ verrouillé |
| **R4** | Palette `Providers`/`Models` **et** sections Settings AI `Providers`/`Models` | **Conservé** : motif « overview + `WorkspaceLink` ». La section affiche l'état et pointe le workspace — jamais une seconde logique | ✅ règle documentée |
| **R5** | `/gallery` : page « bientôt disponible », aucun `/v1/gallery` en Core | **Entrée retirée du menu** (palette + en-tête) ; la route reste joignable en URL profonde comme état vide honnête et reprendra une entrée dès l'arrivée de `/v1/gallery` | ✅ **fait ce lot** |
| **R6** | `/security` (sidebar ADMIN) **et** section Settings `Security` | **Conservé** : section = résumé (2FA/statut) + lien vers le workspace qui possède tous les flux | ✅ |
| **R7** | Motif « entrée de palette pointant un hash d'une autre page » (le mécanisme de R1) | **Interdit** par `nav-dedup.test.ts` | ✅ fait ce lot |
| **R8** | `missions/{settings,templates,workflows}` = placeholders | **Conservés** : marqués `planned: true` (état vide honnête, couverts par `mission-workspace.test.tsx`) | ✅ |
| **R9** | Groupe Settings `Knowledge` contenant la section `Knowledge` | **Conservé avec exception documentée** : l'en-tête est une légende, pas un bouton (`settings-nav.test.ts`, `LABEL_EXCEPTIONS`) | ✅ |

---

## 6. Arborescence Settings cible — **validée**

```
Settings
├── General       chat · reminders · shortcuts · library
├── AI            providers · models · routers · speech
├── Knowledge     knowledge · rag · embedding · vector-db · chunking · reranking · search
├── Skills        skills
├── Integrations  integrations
├── Security      security
├── Appearance    appearance
└── Advanced      system · capabilities
```

Le brief propose `AI → { Providers, Models, Advanced }` et un `Advanced` racine.
**Amendements retenus (justifiés)** :

1. **Pas de sous-groupe imbriqué** : la sidebar Settings est un modèle
   groupe → sections (plat). `routers` + `speech` **sont** le cluster avancé de
   l'AI ; imbriquer ajouterait un niveau de navigation pour 4 entrées.
2. **Deux `Advanced` homonymes** (un sous AI, un racine) recréeraient
   l'ambiguïté de libellé que le brief interdit. Un seul `Advanced` racine.
3. Aucune section ajoutée ni retirée : **21 sections / 8 groupes**, verrouillés
   par `settings-nav.test.ts` (couverture exacte, aucun doublon).

---

## 7. Règles UX du brief → conformité

| Écran | Règle | État | Preuve |
|---|---|---|---|
| **Chat** | Cockpit, pas dashboard | ✅ | §3 — 0 doublon de sélecteur, contexte visible |
| **Projects** | Richesse en 6 facettes | ✅ | §4 |
| **Settings** | Consolider + cartographier avant fusion | ✅ | §2 + §5 (R1, R2 traités ; R5 à arbitrer) |
| **Palette / sidebar** | Vocabulaire unique, une entrée = une destination | ✅ | `nav-dedup.test.ts` |
| **Tous** | Aucune logique métier côté WebUI | ✅ | pages = ligueurs vers `@/lib/api/*` ; arbitrage Core |
| **Honnêteté** | Aucun écran fantôme | ✅ | `/gallery` sorti du menu (R5) ; seuls restants les placeholders `planned` de Missions (R8), tracés et testés |
| **Port** | WebUI sur 3001 | ✅ | `next dev -p 3001` + `playwright.config.ts` |

---

## 8. Décisions de ce lot / ouvertes

**Appliquées (diff minimal, réversibles)**

1. `nav-config.ts` : suppression de l'entrée `Interface` (+ import `Palette`).
2. Suppression du composant mort `assistant-top-bar.tsx` et correction des
   commentaires qui le présentaient comme actif (5 fichiers, commentaires).
3. Commentaire de `settings-workspace.tsx` : le hash n'est plus ouvert par un
   menu, il reste un lien profond.
4. Nouveau garde-fou `tests/unit/ui/nav-dedup.test.ts` : destinations uniques,
   libellés uniques, pas de hash dans le menu, séquences `G` cohérentes avec la
   taxinomie, entrées ⇔ routes réelles, **vocabulaire canonique** (aucun
   ensemble de synonymes — type `Models / AI Models / LLM / Model
   Configuration` — ne coexiste entre palette, sections et groupes Settings).
5. **R5** : entrée `Gallery` retirée de la palette (description du groupe AI
   mise à jour) ; la route `/gallery` est conservée comme état vide honnête.

**Ouvertes**

- Onglet **Knowledge** dédié pour les Projects ? → **non** pour l'instant
  (voir §4 : règle contenu ⇄ défaut) — à réexaminer si le besoin émerge.
- Écarts **interfaciaux** (Shell / CLI / Channels / Desktop) : voir
  `docs/design/2026-09-30-cartographie-interfaciale.md` (I1→I5, phases B→E).

---

## 9. Validations

```bash
cd interfaces/webui
npm run validate          # tsc --noEmit + eslint + jest
npx playwright test       # E2E (webServer auto sur :3001)
```

Résultats (exécution réelle du lot, 2026-09-30) :

| Commande | Résultat |
|---|---|
| `npm run validate` (tsc --noEmit + eslint src + jest) | ✅ **50 suites / 297 tests** en vert |
| `npx playwright test` (webServer auto sur **:3001**) | ✅ **19 passed / 1 skipped**, `PLAYWRIGHT_EXIT=0` |
| Rejeu ciblé `scenarios.spec.ts` (rapport JSON) | ✅ 7 expected / 0 unexpected / 1 skipped |
| Résidus Core après E2E | ✅ 0 projet « E2E Smoke » (nettoyage vérifié) |

Le **skip unique** est `scénario 4 : changer d'agent depuis le chat` :
`test.skip` déclenché car le Core de dev n'expose **aucun agent réel** au-delà
de « Sans agent » (condition environnementale identique au lot précédent —
données Core, pas une régression WebUI).

Identifiants E2E : compte éphémère créé par `POST /auth/register`
(`e2eux<timestamp>`, rôle `standard`), mot de passe généré dans la session et
stocké hors repo (`/tmp/e2e_user`, `/tmp/e2e_pass`, mode 600) — jamais commité,
jamais journalisé. Nettoyage : `rm -f /tmp/e2e_user /tmp/e2e_pass`.



