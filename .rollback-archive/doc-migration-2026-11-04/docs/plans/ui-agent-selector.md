# Sélecteur d'agent du chat — Implémentation

> **Date** : 27 août 2026 · **Branche** : `main`
> **Prérequis** : `docs/plans/ui-openwebui-shell-implementation.md` (shell), `docs/plans/ui-openwebui-target-architecture.md` (§4–5), `docs/plans/ui-openwebui-refactor-audit.md`.
> **Périmètre** : frontend uniquement — Core, Runtime, API, modèles de données **intacts**.

## 1. Objectif

Changer d'agent depuis le chat avec la même simplicité que le changement de modèle :

```
[ Agent ▼ ]  [ Model ▼ ]        ← header du chat, toujours visibles
```

Règles absolues respectées :

- **Agents réels uniquement** : le catalogue vient de `GET /v1/agents` (ETHAN Core) via le hook `useAgents` existant. Aucun agent fictif, aucun jeu de données local.
- **Pas de deuxième système d'agents** : création/configuration = navigation vers la page `/agents` existante (éditeur AgentEditorDialog déjà branché sur le Core). Le bouton « Nouvel agent… » du menu ne fait qu'y naviguer.
- **Pas de logique métier frontend** : le frontend récupère · affiche · sélectionne · active. La résolution effective (instructions système, provider/model par défaut, fusion skills/knowledge/tools, routage) reste dans `core/chat/pipeline.py` ; le payload chat porte simplement `agent_id` — champ déjà consommé par le pipeline.

## 2. Architecture implémentée

```
GET /v1/agents ──► useAgents() (React Query, cache partagé avec /agents)
                      │
              useActiveAgent()           ← nouveau : état de sélection
              ├─ selectedAgentId (localStorage ethan.active-agent)
              ├─ recentAgentIds (localStorage ethan.recent-agents, max 3)
              ├─ activeAgent = agents.find(id) ?? null
              └─ validation de disparition → repli « Sans agent » + toast
                      │ (props)
        ┌─────────────┴──────────────┐
AssistantTopBar                 AssistantChat → AssistantInput
[AgentSelector][ModelSelector]  (cases Agent du menu ＋ — même état)
```

**Propriétaire de l'état** : `app/page.tsx` (ChatHomePage). Le header ET le composer lisent/écrivent la même sélection — plus aucun état agent local dupliqué. `metrics.agentName` affiche désormais l'agent réellement actif (auparavant : « premier agent de la liste », information fausse).

### Fichiers (liste exacte)

| Fichier | Rôle |
|---|---|
| `interfaces/webui/src/components/features/assistant/hooks/use-active-agent.ts` | **nouveau** — symétrique de `use-active-model` ; localStorage, Récents, validation d'existence |
| `interfaces/webui/src/components/features/assistant/components/agent-selector.tsx` | **nouveau** — popover du header (recherche, Sans agent, Récents, Agents, Nouvel agent…) |
| `interfaces/webui/src/components/features/assistant/components/assistant-top-bar.tsx` | **modifié** — layout `[Agent ▼] [Model ▼]`, props agent |
| `interfaces/webui/src/app/page.tsx` | **modifié** — état unique via `useActiveAgent` ; TopBar + composer alimentés ; payload `agent_id` ; métriques véridiques |

Clients API, hooks `use-agents`/`use-chats`, types `@/types` : **inchangés**.

## 3. Menu du sélecteur

```
┌────────────────────────────────┐
│ 🔍 Rechercher un agent…        │
│ ○ Sans agent (ETHAN brut)      │
│ Récents                        │
│   ● Analyste Doc   [qwen2.5]   │
│ Agents                         │
│   ○ Veille Web     [llama3.3]  │
│   ○ Rédacteur      [claude-3]  │
│────────────────────────────────│
│ ＋ Nouvel agent…               │ → /agents (interface existante)
└────────────────────────────────┘
```

- **Recherche** instantanée sur `name` + `description` (client-side, catalogue déjà en cache).
- **« Sans agent »** explicite (`agent_id: undefined`) : mode ETHAN brut, jamais implicite.
- **Récents** = derniers agents utilisés (max 3, localStorage), filtrés sur l'existence courante et l'agent actif.
- **Déclencheur** (fermé) : icône bot + nom de l'agent + modèle par défaut de l'agent (`agent.model` s'il existe) ; « Sans agent » sinon. Même gabarit visuel que le trigger compact du `ModelSelector`.
- Clavier/souris : Échap ferme, clic extérieur ferme, focus auto dans la recherche.

## 4. Relation agent ↔ capacités rendue compréhensible

L'encapsulation décrite côté Core est reflétée sans la réinventer :

| Capacité encapsulée | Affichage |
|---|---|
| Instructions | la `description` EST le prompt système injecté par le pipeline ; l'éditeur `/agents` la nomme comme telle |
| Modèle | badge `[provider·model]` dans le menu ; défaut uniquement — un choix utilisateur au `[Model ▼]` **prime** (vérité pipeline : `provider_id or agent.provider`) |
| Skills / Knowledge / Tools / MCP | compteurs des champs réels (`skill_ids`, `metadata.knowledge_ids/tool_ids`) — brique par brique dans l'éditeur existant |
| Memory | capacité globale ETHAN (pipeline), pas une propriété d'agent affichée ici |

Le frontend ne recalcule AUCUNE résolution : les chips capabilities du composer montrent la sélection manuelle ; celles issues de l'agent sont appliquées par le Core à l'exécution.

## 5. Cas limites gérés

| Cas | Comportement implémenté |
|---|---|
| Agent supprimé côté Core pendant qu'il est actif | détection au retour du catalogue → repli auto « Sans agent », purge localStorage, toast d'avertissement ; jamais d'envoi vers un id inexistant |
| Agent indisponible/invalide à l'exécution | erreur métier du pipeline → bannière d'erreur chat existante (dismissable) |
| Agent par défaut | ETHAN n'a pas de notion backend « agent par défaut » ; la préférence locale persiste et préremplit chaque session |
| Refresh page | sélection restaurée depuis localStorage puis revalidée contre le catalogue fraîchement fetché |
| Nouveau chat | l'agent actif persiste (préférence de session utilisateur) |
| Conversation existante | changement à chaud permis entre deux envois ; les messages historiques conservent leur contexte (`metadata.agent_id`) ; l'envoi suivant porte le nouvel agent |
| Catalogue en cours de chargement | trigger affiche « Agents… » (état neutre) |

## 6. Validation exécutée

- `tsc --noEmit` → exit 0 · `next lint` → ✔ no warnings · tests Jest → **7/7 PASS**
- Serveur dev Next.js : toutes les routes testées en **200** (`/`, `/workspace`, `/agents`, `/settings`, `/knowledge`, `/tools`, `/providers`, `/models`, `/login`) — log de compilation propre.
- Page `/` rend le déclencheur « Agents… » (sélecteur d'agent) aux côtés du ModelSelector compact.
- Aucune fonctionnalité retirée : cases Agent du composer (toujours fonctionnelles, désormais synchronisées avec le header), `/agents` inchangée, payload enrichi seulement via champ déjà consommé.

## 7. Hors périmètre

- Notion backend d'agent par défaut ou scoping mémoire/permissions par agent (exigerait évolution Core — cf. doc cible §10).
- Rendu multi-agents simultanés ; assignation d'un agent par conversation persistée côté ChatStore (la référence vit aujourd'hui dans la préférence locale + metadata du message).

