# Barre de contexte actif du chat — `ChatContextBar`

> **Date** : 27 août 2026 · **Prérequis** : audit (`ui-openwebui-refactor-audit.md`), architecture cible (`ui-openwebui-target-architecture.md`), shell (`ui-openwebui-shell-implementation.md`), sélecteur d'agent (`ui-agent-selector.md`).
> **Portée** : frontend uniquement — aucun changement Core/Runtime/API/modèles de données.

## 1. Objectif

L'utilisateur doit comprendre **en une seconde pourquoi ETHAN répond comme il le fait**. Une bande fine, proche du header du chat, expose le contexte réel :

```
┌───────────────────────────────────────────────────────────────┐
│ 🤖 Atreus ▾   ⚙ qwen2.5:7b · Ollama ●  🔧 2 outils ▾          │
│ ✦ 1 skills ▾   🗄 1 sources ▾   🧠 Mémoire · 12               │
└───────────────────────────────────────────────────────────────┘
```

Légère, wrappe sur une ligne supplémentaire si nécessaire, **jamais un panneau d'administration**.

## 2. Règle fondamentale : capacités réelles uniquement (anti-fantôme)

- Chaque chip est calculé depuis les **données chargées du Core**, jamais décoratif.
- Résolution = **UNION (agent ∪ sélection composer)** — mêmes règles que `core/chat/pipeline.py` : `skill_ids`, `metadata.knowledge_ids/tool_ids` de l'agent fusionnés aux cases cochées du composer ; dédupliqués par id.
- Un id non résoluble dans un catalogue chargé est **exclu de l'affichage** (jamais d'élément fantôme).
- La barre entière n'est **pas rendue** s'il n'existe aucune donnée réelle à montrer (ex. SSR sans backend) → jamais de ligne vide.
- La pastille « fournisseur connecté » n'apparaît que si l'API a renvoyé un `status` explicite (`undefined` = pas de pastille, pas de supposition).

### Memory

Injectée par le pipeline pour toute conversation (**capacité globale**, non portée par l'agent). Affichée uniquement si `memoryFacts.length > 0`, libellé `Mémoire · <n>`. Un scoping par agent exigerait une évolution Core explicitement hors périmètre.

## 3. Fichiers

| Statut | Fichier | Rôle |
|---|---|---|
| **Créé** | `src/components/features/assistant/components/chat-context-bar.tsx` | Composant réutilisable et présentationnel |
| Modifié | `src/app/page.tsx` | Propriétaire de l'état : résolution des capacités, handlers, rendu sous le header |
| Modifié | `src/components/features/assistant/components/assistant-top-bar.tsx` | Transmission `modelSelectorOpen/onModelSelectorOpenChange` au ModelSelector compact |
| Modifié | `src/components/shared/model-selector.tsx` | Props optionnelles `open` / `onOpenChange` (pattern semi-controlled) — comportement interne inchangé sans elles |
| Créé | `tests/unit/assistant/ChatContextBar.test.tsx` | 5 tests unitaires |

Aucun autre fichier touché. Aucune modification backend.

## 4. Contrat du composant (`ChatContextBarProps`)

| Prop | Type | Effet |
|---|---|---|
| `agentName` / `agentDescription` | `string \| null` | Chip agent (tooltip = description réelle) ; absent si aucun agent actif |
| `onAgentClick?` | `() => void` | Détails de l'agent (voir §5) |
| `modelName` | `string \| null` | Libellé réel `model · provider` ; absent tant qu'inconnu |
| `modelConnected` | `boolean \| undefined` | Pastille verte/ambre — `undefined` ⇒ pas de pastille |
| `onModelClick?` | `() => void` | Déroule le sélecteur de modèle existant |
| `tools`/`skills`/`knowledge` | `ChatContextItem[]` (`{id, name, detail?}`) | Chips agrégés `<n> outils/skills/sources`, seulement si n>0 |
| `onCapabilityPageClick?` | `(kind) => void` | Lien « Gérer… » du panneau déroulant |
| `memoryFactCount` | `number \| null` | Affiché si > 0 |
| `onMemoryClick?` | `() => void` | Navigation vers la vue mémoire |

Sous-composants internes : `ContextChip` (chip simple), `PanelChip` (chip + popover), `CapabilityPanel` (liste des items réels + badge `detail` comme `builtin`/`mcp`).

## 5. Interactions (câblage effectif dans `page.tsx`)

| Clic sur | Résultat |
|---|---|
| Agent | `openInspector("agent", selectedAgentId)` — l'inspecteur global **existant** (détails agent). Handler fourni seulement si un agent est réellement sélectionné |
| Modèle | déroule le **ModelSelector compact** du header via l'état contrôlé de la page — aucun second popover créé, même source de vérité `useActiveModel` |
| Outils / Skills / Sources | panneau local listant les items résolus (noms réels, badge builtin/mcp) + lien vers `/tools`, `/skills`, `/knowledge` (pages dédiées existantes) |
| Mémoire | navigation vers `/workspace` (vue Memory Explorer existante) |

Fermeture des panneaux : clic extérieur ou Échap (listeners nettoyés au démontage).

## 6. Données — sources uniques, aucune duplication

- Agent actif : hook `useActiveAgent` (déjà en place côté sélecteur d'agent).
- Catalogues skills/collections/tools : **déjà chargés** par `page.tsx` pour le composer — la barre réutilise exactement ces données (aucun appel API supplémentaire).
- Modèle : `useActiveModel` via le libellé du header ; statut fournisseur = champ `status` réel du provider.
- Memory : `useFacts()` — cache React Query partagé avec `/workspace` (une seule requête pour toute l'app).

## 7. Cas limites couverts

| Cas | Comportement |
|---|---|
| Catalogues en cours de chargement | ids non encore résolus exclus → les chips apparaissent à mesure, sans fantôme |
| Agent retiré/disparu (`useActiveAgent` repli) | chip agent disparaît automatiquement (source = même état) |
| Provider sans `status` exploitable | pas de pastille d'état plutôt qu'une supposition fausse |
| Aucune donnée (SSR sans backend, fresh install) | barre non rendue (`return null`) |
| Capacités héritées de l'agent | visibles dans l'UNION — suppression côté composer impossible (non retrayables ici) |

## 8. Test unitaire (`tests/unit/assistant/ChatContextBar.test.tsx`)

1. Ne rend **rien** sans capacité réelle (règle anti-fantôme) ;
2. Rend agent/modèle/capacités pré-résolues, compteurs réels (`2 outils`, `1 skills`, `1 sources`), `title="Outils actifs (2)"` accessible ;
3. Mémoire : affichée si 4 facts, **jamais** si 0 ;
4. Panneau détaillé au clic liste les items réels (`web_search`, `sql_query`, badges `builtin`/`mcp`) et se ferme sur Échap ;
5. Handlers `onAgentClick`/`onModelClick` invoqués.

## 9. Validation exécutée

| Contrôle | Résultat |
|---|---|
| `tsc --noEmit` | exit 0 |
| `next lint` | ✔ No ESLint warnings or errors |
| Jest | **6 suites, 12/12 PASS** (dont 5 nouveaux) |
| Serveur dev (hot-reload :3002) | `/`, `/workspace`, `/agents`, `/settings`, `/knowledge`, `/tools`, `/login` → toutes **200** |
| Anti-fantôme vérifié en live | sans backend répondant, la barre ne s'affiche pas (comportement attendu) |

## 10. Hors périmètre

- Édition des capacités depuis la barre (sélection = composer uniquement) ;
- Scoping mémoire par agent, historique memory events (API prête, UI future) ;
- Arborescence exhaustive des tool calls par message (les sections repliables de message existent déjà) ;
- Toute évolution Core/Runtime/API.

*Document d'implémentation — livraison effective réalisée et validée.*

