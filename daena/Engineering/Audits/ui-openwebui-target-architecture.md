# Architecture UX cible — WebUI ETHAN (référence Open-WebUI)

> **Date** : 27 août 2026 · Suite de `Obsidian/Engineering/Audits/ui-openwebui-refactor-audit.md`
> **Statut** : conception — aucune fonctionnalité modifiée à cette étape.
> **Cadre** : ETHAN reste le système, la WebUI reste son interface. Open-WebUI est une **référence d'ergonomie**, jamais un code à copier ni un fork.

## 0. Objectif primordial : répondre aux 7 questions en moins de 3 secondes

Un utilisateur qui arrive dans le chat doit obtenir immédiatement, **sans navigation** :

| Question | Réponse visible | Où |
|---|---|---|
| Quel LLM est utilisé ? | Nom du modèle + badge fournisseur/local | Header chat, tout moment |
| Quel agent est utilisé ? | Nom de l'agent ou « Sans agent » | Header chat, tout moment |
| Quelles capacités sont actives ? | Chips nommées (skills, knowledge, tools, fichiers) | Au-dessus du composer |
| Comment changer de LLM ? | Le sélecteur EST le nom du modèle — un clic | Header chat |
| Comment changer d'agent ? | Le sélecteur EST le nom de l'agent — un clic | Header chat |
| Comment accéder aux outils / connaissances ? | Menu [+], slash commands, liens sidebar | Composer + sidebar |
| Comment configurer l'agent ? | « Configurer » dans le popover agent ; page Agents | Popover + `/agents` |

Règle d'or : **toute action courante ≤ 2 clics depuis le chat, sans quitter la conversation.**

## 0.1 Principe architectural (rappel AGENTS.md)

- La WebUI **affiche et transmet** ; elle ne décide rien du métier.
- Les sélecteurs modèle/agent manipulent l'état via les clients API existants (`useActiveModel`, `lib/api/*`). Aucun appel hors proxy `/api/*`.
- Toute donnée affichée provient d'un endpoint réel : zéro état fantôme, zéro mock.

---

## 1. Sidebar principale

Une seule taxinomie (fin des trois couches redondantes de l'audit §3). Comportement calqué sur la philosophie Open-WebUI : la sidebar est la **bibliothèque opérationnelle** de l'utilisateur, avec vue contextuelle selon la route.

### 1.1 Structure

```
┌──────────────────────────────┐
│ [Logo ETHAN]        [« »]    │  ← toggle collapse (état persisté ui.store)
│                              │
│ [＋ Nouveau chat]            │  ← bouton pleine largeur
│ [🔍 Rechercher…]     Ctrl K  │  ← ouvre la palette (recherche chats+pages+modèles)
│                              │
│ ── CONVERSATIONS ──          │  ← présent uniquement sur route de conversation
│   Épinglés                   │
│   Aujourd'hui / Hier /       │  ← groupage temporel existant conservé
│   7 derniers jours / …       │
│   …                          │  menu item : Épingler/Renommer/Supprimer (déjà ok)
│                              │
│ ── PILOTAGE ──               │
│   ◈ Workspace                │  missions, goals, flux, mémoire
│   ◎ Missions                 │
│   🗓 Calendrier               │
│   ✎ Notes                    │
│   ✉ Boîte mail (Inbox)       │
│                              │
│ ── CAPACITÉS ──              │
│   ⬢ Agents                   │  /agents
│   ❋ Skills                   │  /skills
│   ☰ Connaissances            │  /knowledge (collections RAG)
│   ⛭ Outils & MCP             │  /tools (+ serveurs MCP intégrés)
│                              │
│ ── SYSTÈME ──                │  ← discret, usage occasionnel
│   ⊞ Modèles                  │  /models
│   ⟐ Fournisseurs             │  /providers
│   ⌖ Deep Research            │  /research
│   ⚗ Cookbook                 │  /cookbook
│                              │
│ [Avatar · Nom user ▾]        │  ← useAuth réel ; menu :
│                                 Profil · Paramètres · Administration*
│                                 · Déconnexion (*si permission)
└──────────────────────────────┘
```

### 1.2 Correspondance concept Open-WebUI → concept ETHAN

| Open-WebUI | ETHAN | Justification |
|---|---|---|
| New Chat / historique chats | Idem (déjà conforme) | garder |
| Models (workspace) | **Modèles** `/models` + **Fournisseurs** `/providers` | ETHAN sépare le catalogue de modèles et les connexions providers |
| Prompts (workspace) | *(rien)* — absorbe plus tard via Skills/Cookbook | pas d'entité Prompts dans le Core ETHAN aujourd'hui ; ne pas créer d'écran fantôme |
| Knowledge | **Connaissances** `/knowledge` | entité déjà Core-owned |
| Skills (prompts actifs) | **Skills** `/skills` | idem |
| Tools / Functions | **Outils & MCP** `/tools` | Tools + onglet Serveurs MCP (ex-Settings→mcp) |
| Channels / Notes | **Notes** (page ETHAN existante) ; pas de channels | rester fidèle au Core |
| Admin Settings | **Administration** via menu utilisateur | cf. §6 |

### 1.3 Comportements

- **Vue contextuelle** : route conversation (`/`, `/c/[id]`) → section Conversations dépliée ; autre route → navigation complète, Conversations réduite à un raccourci « Retour au chat ».
- **Collapse** : rail d'icônes conservé pour l'afféral (toggle, nouveau chat, Ctrl+K, paramètres) ; les entrées métier disparaissent du rail (fin de la double taxinomie).
- **Responsive < 768px** : overlay drawer + scrim (comportement existant auto-collapse conservé).
- **Le changement de modèle/agent n'est PAS dans la sidebar** : c'est une action de premier niveau du chat (§3/§4). La sidebar n'expose que le registre.

---

## 2. Zone de chat

```
┌────────────────────────────────────────────────────────────────┐
│ HEADER (sticky)                                                │
│ [Nom conversation ▾]        [Agent ▾] [Modèle ▾] [capa] [⋮]    │
├────────────────────────────────────────────────────────────────┤
│ ZONE CENTRALE (scroll)                                         │
│   [empty state: suggestions, rappel agent/modèle si configurés]│
│   Turn utilisateur   → texte + chips fichiers                  │
│   Turn assistant     → markdown · streaming caret              │
│                        ⌄ Tool calls (timeline repliable)       │
│                        ⌄ Sources RAG (documents cités)         │
│                        footer: provider · model · tokens       │
│                        actions: copier régénérer éditer        │
├────────────────────────────────────────────────────────────────┤
│ COMPOSER                                                       │
│  chips actifs nommés (skills/knowledge/tools/fichiers/agent)   │
│  [＋] [ textarea …                    ] [/] [⏺ send / ■ stop] │
│  hint clavier · Ctrl K palette                                 │
└────────────────────────────────────────────────────────────────┘
```

### 2.1 Header

| Élément | Contenu | Source | Nouveau ? |
|---|---|---|---|
| Titre conversation | titre éditable (double-clic déjà ok) | ChatStore Core | non |
| **Sélecteur Agent** | nom actif ou « Sans agent » ; popover §4 | `useActiveAgent` (nouveau hook) | oui |
| **Sélecteur Modèle** | `model` + badge fournisseur/local ; popover §3 | `useActiveModel` existant | monté en variant full |
| Indicateur capabilities | icônes œil/vision, 🔎 web, ⚙ tools selon capabilities du modèle actif | `GET /models` | oui |
| Menu ⋮ | Paramètres du chat futur ; déjà : « Ouvrir dans Agents », « Rechercher » | — | partiel |

Règle : le header reste **constant pendant le streaming** ; changer de modèle mid-stream n'affecte que l'envoi suivant (message d'info discret la première fois).

### 2.2 Zone centrale

- **Streaming** : conserver SSE et gestion des événements `content/done/error/tool_call/tool_result/status/history/names` (`use-chats.ts`), caret visible, bouton stop toujours atteignable.
- **Tool calls** : timeline par appel (nom, durée début→fin depuis `toolStartRef`), repliée par défaut, dépliable ; les résultats restent inspectables sans polluer le fil.
- **Fichiers** : chips cliquables au message utilisateur ; détail fichier via overlay (pattern Open-WebUI FilesOverlay) plutôt qu'une page.
- **Sources** : documents RAG cités listés sous la réponse quand `knowledge_ids` produisent un contexte (endpoint `/v1/rag/context` existe ; surface UI légère).
- **Arbre de messages** : champs `parent_id/children_ids` déjà persistés côté Core. V1 cible : bouton **« versions ‹ › »** sur les messages régénérés/édités, lecteur de branche simple. Navigation arborescente complète explicitement reportée (§10).
- **Empty state** : cartes de démarrage (nouveau chat vierge) + rappel explicite « Modèle : X — Agent : Y » avec liens directs vers les deux sélecteurs : cela enseigne l'interaction dès le premier écran.

### 2.3 Composer

| Zone | Détail |
|---|---|
| Chips actifs | nommés individuellement (« Skill: rédaction », « KB: docs-projet »), chaque chip supprimable ; ce sont les capacités vues dans Q3 |
| Bouton ＋ | menu popover : Fichiers · Skills ☐ · Connaissances ☐ · Outils ☐ (badge builtin/mcp) · Agent ☐ — structure existante conservée |
| Textarea | auto-resize, Enter=envoi / Shift+Enter=nouvelle ligne (déjà ok), placeholder dynamique « Demander à {agent ou ETHAN} ({model})… » |
| [/] slash commands | enrichissement : `/model`, `/agent`, `/skill`, `/kb`, `/tool` avec autocomplétion (les ids envoyés restent ceux du payload existant) |
| Send/Stop | arrondi accent ; devient ■ stop pendant génération (déjà ok) |
| Quick settings | PAS d'hyperparamètres (temperature etc. absents du contrat API) ; « paramètres rapides » = uniquement sélections contextuelles ci-dessus |

## 3. Sélection LLM — interaction de premier niveau

### 3.1 Déclencheur

- Bouton **toujours visible** dans le header chat : nom du modèle courant (truncaté) + badge fournisseur/local. Le nom EST le bouton : impossible de ne pas le trouver.
- Second déclencheur : slash command `/model` dans le composer.
- Aucun changement de page nécessaire pour changer de LLM.

### 3.2 Popover (composant `model-selector.tsx`, variant `full`, aujourd'hui inutilisé → promu)

```
┌─ Rechercher un modèle…        ────────────┐
│ Épinglés                                    │
│   ● llama3.3-70b     [ollama·local]  ★ ✕   │
│ Recommandés (disponibles)                   │
│   ○ gpt-4o           [openai]        ☆     │
│   ○ claude-sonnet    [anthropic]    ☆      │
│ Autres…                                     │
│ ─────────────────────────────────────       │
│ ⛭ Gérer fournisseurs   ⊞ Catalogue complet │
└─────────────────────────────────────────────┘
```

- **Recherche** instantanée client-side sur id/nom/fournisseur/capabilities (`useModels().searchModels` existe déjà).
- **Sections** : Épinglés (localStorage existant) · Disponibles · Indisponibles (grisés, non cliquables, tooltip cause) · Cartes custom.
- **Item** : nom, badge fournisseur ou « Local », capabilities en icônes, état disponibilité.
- **Clavier** : ↑/↓ navigation, Entrée sélectionne, Échap ferme — pattern Open-WebUI conservé.
- **Sélection** → `setActiveModel(provider, model)` du hook `useActiveModel` existant : persistance locale immédiate + `PUT /providers/{id}/default` (comportement backend déjà en place, à documenter dans l'UI par un toast résumé).
- **Pied de popover** : liens vers `/models` (catalogue) et `/providers` (connexions) pour la configuration complète — la config reste dans les pages dédiées.
- **Continuité conversationnelle** : la sélection ne recharge pas les messages ; seule la prochaine requête porte `provider_id/model`.

## 4. Sélection Agent — même principe

### 4.1 Déclencheurs

- Bouton **toujours visible** dans le header chat : nom d'agent actif ou « Sans agent ».
- Menu [+ ] du composer (existant, conservé) et slash `/agent`.

### 4.2 Popover (nouveau composant `agent-selector.tsx`, symétrique du modèle)

```
┌─ Rechercher un agent…         ────────────┐
│ ○ Sans agent (ETHAN brut)                  │
│ Épinglés                                   │
│   ● Analyste Doc  [gpt-4o] 2 skills KB  ✕  │
│ Tous                                       │
│   ○ Veille Web    [llama3.3] web_search    │
│   ○ Rédacteur     [claude]    3 skills     │
│ ─────────────────────────────────────      │
│ ＋ Nouvel agent        ⚙ Gérer les agents │
└────────────────────────────────────────────┘
```

- **Données** : `GET /v1/agents` (hook existant). Item = nom + description tronquée + badges `{provider}·{model}` + compteurs skills/knowledge/tools issus des vrais champs (`skill_ids`, `metadata.knowledge_ids/tool_ids`).
- **« Sans agent »** = `agent_id: undefined` : l'utilisateur voit explicitement le mode brut ETHAN.
- **Sélection** → nouveau hook `useActiveAgent` (persist localStorage `ethan.active-agent`, même modèle que `useActiveModel`). Le payload chat porte `agent_id` — champ **déjà consommé** par le pipeline Core : zéro changement backend.
- **Changement à chaud** : autorisé entre deux envois ; les capacités fusionnées affichées au composer sont recalculées instantanément (cf. §5 règles).
- **Actions item** : « Configurer » (→ `/agents?selected={id}`, la page Agents ouvre l'éditeur existant), « Exécuter une tâche » (reprend le dialog `executeAgent` existant).

## 5. Relation Agent ↔ LLM — représentation fidèle au Core

### 5.1 Ce que le backend fait RÉELLEMENT (source : `core/chat/pipeline.py`, `core/agents/executor.py`)

```
Agent (core/agents)                     Chat
 ├─ name, description ──────────────►  description = instructions système
 │                                      (« Tu es l'agent "X". {description} »)
 ├─ provider ──┐                       défauts du modèle LLM…
 ├─ model   ───┘                          utilisés SEULEMENT si l'utilisateur
 │                                        n'a pas fait de choix explicite :
 │                                        pipeline = `provider_id or agent.provider`
 ├─ skill_ids[]  ─────────────►  UNION avec skill_ids choisis au composer
 ├─ metadata.knowledge_ids[] ─►  UNION avec collections choisies
 └─ metadata.tool_ids[]      ─►  UNION avec tools cochés

Memory : capacité GLOBALE — le pipeline injecte les facts pour toute
conversation ; elle n'est PAS portée par l'agent aujourd'hui.
```

Règle de résolution effective (déjà implémentée côté Core) :

| Cas | Provider/model réellement utilisé |
|---|---|
| Agent désigné + aucun choix utilisateur | défauts de l'agent (`agent.provider`, `agent.model`) |
| Choix explicite dans le sélecteur chat | **le choix de l'utilisateur prime** sur l'agent |
| Sans agent | modèle actif par défaut (`useActiveModel` → `PUT default` / premier enabled) |
| Choix invalide/indisponible | erreur métier renvoyée par le pipeline (bannière existante) |

### 5.2 Comment l'UI représente ça SANS toucher au backend

1. **Le sélecteur d'agent affiche les cibles** `{provider}·{model}` de l'agent comme « défauts », jamais comme contraintes.
2. **Override utilisateur explicite** : si l'utilisateur choisit un modèle ≠ celui de l'agent, le header montre un chip discret `modèle remplacé {model} (défaut agent: {x})` avec infobulle expliquant la règle. Vérité ⇔ affichage.
3. **Capacités résolues** : les chips composer passent en revue l'UNION (agent ∪ sélection manuelle). Les items issus de l'agent portent une pastille « agent » et ne sont pas retirables depuis le chip (il faut éditer l'agent) — pastille cliquable → ouvre l'éditeur d'agents.
4. **Instructions système** : aujourd'hui la `description` EST le prompt système. L'UI nomme ce champ « Identité & instructions » dans l'éditeur d'agents plutôt que d'inventer un champ séparé. Si le Core ajoute un jour `system_prompt`, l'UI suivra (champ déjà encodé dans `metadata`).
5. **Memory** : présentée comme capacité globale du cockpit (indicateur « Mémoire active — N facts » dans Workspace), pas comme propriété d'agent. Une scoping par-agent est listée en évolution future §10 et exigerait une évolution Core explicite.
6. **Interdits** : pas de logique de résolution recréée côté frontend, pas d'appel direct aux providers, pas de stockage des secrets.

### 5.3 Diagramme mental à rendre visible à l'utilisateur (empty state & docs)

```
Vous parlez à        [ Agent ▾ ]        [ Modèle ▾ ]
                    définit POURQUOI    définit AVEC QUOI
                    comment répondre     on répond
              capacités actives ⌄ (chips nommés)
```

---

## 6. Navigation paramètres

Fin du fourre-tout Settings à 10 sections (audit §2). Deux scopes, deux portes :

### 6.1 `/settings` — Préférences utilisateur (menu avatar)

| Section | Contenu | Origine |
|---|---|---|
| Général | langue, comportement interface | existant settings-workspace→general |
| Apparence | thème clair/sombre/système, accent presets, Atmosphere | existant appearance |
| Conversations | préférences chat (densité, reprise auto, retour scroll) | nouveau léger, local |
| Compte & sécurité | lien vers page Sécurité (2FA TOTP existante `/security`) | réorientation |

### 6.2 `/admin` — Administration système (garde rôle via `Permission.*` déjà côté API)

| Onglet | Contenu | Migré depuis |
|---|---|---|
| Fournisseurs | CRUD providers — réutilise `ProvidersWorkspace` | `/providers` devient ici ou garde sa route avec lien (décision Phase D audit) |
| Modèles | catalogue + toggles + cartes custom | Settings→models + `/models` fusionnés |
| RAG | config RAG (`getRagConfig/updateRagConfig`), indexation | Settings→rag + Settings→knowledge |
| MCP | serveurs MCP (`/v1/tools/servers` CRUD complet existant) | Settings→mcp |
| Utilisateurs | gestion comptes admin (`listManagedUsers…`) | `/security` partie users |
| Plugins | état plugins (`/v1/plugins`) | nouveau (API prête, UI simple liste) |

- Chaque section Admin est un **composant extrait mécaniquement** de `settings-workspace.tsx` branché sur les hooks features existants — zéro duplication de logique React Query (risque R3 de l'audit).
- Les pages opérationnelles (`/providers`, `/models`, `/tools`) restent accessibles en navigation directe ; Admin n'est qu'une vue regroupée : Open-WebUI procède pareillement (Workspace vs Admin).

## 7. Principe fondamental : chat-first pour l'usage courant, pages dédiées pour la configuration

| Action | Accès chat-first (≤2 clics) | Page dédiée (gouvernance) |
|---|---|---|
| Changer de LLM | sélecteur header / `/model` | `/models` + `/providers` |
| Changer d'agent | sélecteur header / `/agent` / menu ＋ | `/agents` |
| Activer skills/knowledge/tools pour un message | chips composer, menu ＋, slash commands | `/skills`, `/knowledge`, `/tools` |
| Joindre des fichiers | bouton ＋ ou drag&drop | — |
| Créer un agent | « ＋ Nouvel agent » dans le popover | éditeur complet `/agents` |
| Ajouter une connaissance | lien direct depuis le popover knowledge du composer | `/knowledge` (ingestion complète) |
| Connecter un provider MCP/MCP server | info & liens dans le popover outils | `/tools` onglet serveurs / Admin→MCP |
| Config RAG, users, plugins | — | Admin §6.2 |
| Thèmes/accent/compte | popover rapide ? Non → Paramètres | `/settings` |

Interprétation : **le chat embarque des vues de sélection, jamais des vues d'édition**. Toute modification durable passe par sa page. C'est la ligne exacte entre simplicité Open-WebUI et respect de la frontière interface/système.

## 8. Contrats frontaux requis (aucun changement backend)

Nouveaux fichiers uniquement — rien de cassé :

```
components/features/assistant/
  ├─ components/model-selector-hero.tsx    # wrapper variant full monté au header
  ├─ components/agent-selector-popover.tsx # nouveau (données = listAgents existant)
  ├─ hooks/use-active-agent.ts             # symétrique use-active-model (localStorage)
  └─ lib/context-resolver.ts               # calcul affichage UNION agent∪composer
components/layout/
  └─ nav-config.ts                         # taxinomie unique consommée par rail+sidebar+palette
components/features/settings/components/   # extraction sections existantes → composants
components/features/admin/                 # workspace regroupé (réutilise les mêmes composants)
app/c/[id]/page.tsx                        # route conversation deep-linkable
```

Hooks/clients **inchangés** : `lib/api/*`, `use-chats.ts` (payload déjà complet), `use-active-model.ts`, `use-models/use-providers/use-skills/use-knowledge/use-memory`. Le payload `ChatCompletionRequest` porte déjà tout ce qu'il faut (`skill_ids/collection_ids/tool_ids/knowledge_ids/file_ids/agent_id/model/provider_id`) : vérifié contre `core/chat/pipeline.py`.

Évolutions backend optionnelles explicitement HORS périmètre ici : archivage/tags chats, arbre navigable paginé, scoping memory par agent, hyperparamètres par message.

## 9. Critères de validation UX

1. Les 7 questions de la section 0 ont leur réponse visible sans scroll ni navigation ; test e2e Playwright dédié.
2. Changer modèle OU agent = **1 clic + 1 clic** maximum, sans rechargement de la conversation.
3. Les capacités actives sont toujours lisibles : chaque chip nommé, supprimable si manuel, pastillé si hérité d'un agent.
4. Aucun écran de config ne se réécrit : Admin réutilise les composants des pages (grep de duplication React Query = 0).
5. L'affichage reflète le pipeline Core exactement : test unitaire du resolver §8 sur les 4 cas du tableau §5.1.
6. `tsc --noEmit`, lint, tests existants verts à chaque livraison ; aucune route publique ouverte (middleware inchangé).

## 10. Explicitement hors périmètre de cette conception

- Fork/dépendance au code Open-WebUI (SvelteKit/Bits UI/Tiptap/Socket.IO).
- Multi-modèles simultanés dans un envoi (contrat ETHAN mono-model).
- Archivage, dossiers/tags de conversations : nécessite d'abord des endpoints ChatStore Core.
- Navigation arborescente complète des messages (V1 = versions ‹ › seulement).
- Scoping mémoire par agent ; prompts indépendants façon OWUI « Prompts ».
- Toute fonctionnalité fantôme : UI uniquement si l'endpoint existe.

*Document de conception — aucune implémentation réalisée à ce stade.*




