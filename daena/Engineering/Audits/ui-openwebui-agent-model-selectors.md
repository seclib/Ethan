# ETHAN WebUI — Sélecteurs Agent + Model (niveau Open-WebUI)

## Objectif

Faire des sélecteurs **Agent** et **Model** du header du chat deux contrôles
immédiats, symétriques et de niveau Open-WebUI :

```
[ Agent ▼ ]    [ Model ▼ ]
```

Tous deux sont alimentés par les **vraies** APIs/services ETHAN (Core) — aucune
donnée mockée, aucune seconde logique Provider/Agent.

---

## Agent Selector (`agent-selector.tsx`)

### Source de vérité
`GET /v1/agents` via `useAgents()` (cache React Query partagé avec `/agents`).
Le frontend ne fait que : **récupérer · afficher · sélectionner**.

### Menu (Open-WebUI)
```
Sans agent
────────────
Rechercher un agent…
────────────
Récents            (derniers agents utilisés — localStorage)
General            (agents sans capability)
Spécialisée        (agents avec ≥ 1 capability)
────────────
+ Nouvel agent…    (→ /agents)
```

### Regroupement General / Spécialisée
Dérivé des **VRAIES `capabilities`** déclarées par le Core
(`core/agents/types.py` — champ libre utilisé aussi dans le system prompt,
`core/agents/executor.py`). Aucun champ « catégorie » n'existe côté Core ; on ne
l'invente pas. Les agents déjà listés dans Récents ne sont pas répétés.

### États gérés (nouveaux)
| État | Rendu |
|---|---|
| Chargement (`loading`) | « Chargement des agents… » |
| Erreur API (`error`) | « Erreur de chargement : … » (texte rouge) |
| Catalogue vide | « Aucun agent créé dans ETHAN. » |
| Recherche sans résultat | « Aucun agent ne correspond à “…” » |

`error` est maintenant relayé de `useActiveAgent` → `AssistantTopBar` →
`AgentSelector` (prop optionnelle, rétrocompatible).

### Cas limites (déjà couverts par `use-active-agent.ts`)
- **agent supprimé** : repli auto « Sans agent » + toast + purge localStorage.
- **agent indisponible** : id introuvable → même repli.
- **agent par défaut** : aucun agent = « Sans agent » (ETHAN brut).
- **refresh / nouvelle conversation** : préférence relue depuis localStorage.
- **conversation existante** : `agent_id` porté par le payload ; la résolution
  effective reste dans `core/chat/pipeline.py` (modèle utilisateur > défaut agent).

---

## Model Selector (`model-selector.tsx`)

### Source de vérité
- `GET /providers` + `GET /models` via `useActiveModel()` + `useModels()`.
- Sélection persistée (localStorage) + synchro backend `PUT /providers/{id}/default`.

### Dropdown (Open-WebUI) — nouvelle organisation par **provider**
```
Search models…            (recherche nom/id/provider/capability)
────────────
Pinned                    (modèles épinglés)
Ollama                    (groupe par provider)
  llama…  qwen…  mistral…
Other Providers
  …
```

### Nouveautés implémentées
1. **Regroupement par provider** : `groupedByProvider` (tri alphabétique) —
   remplace l'ancienne liste plate « All Models ».
2. **Disponibilité** : `model.is_available === false` → item grisé
   (`opacity-50`, `cursor-not-allowed`, `aria-disabled`), badge **« Indisponible »**,
   **non-sélectionnable** (souris + clavier), mais épinglage autorisé.
3. **États** : « Chargement des modèles… » (loading) ; « Aucun modèle disponible »
   (vide) ; « Aucun modèle pour “…” » (recherche sans résultat).

### Cas limites
- **aucun modèle / provider offline** : modèles `is_available=false` affichés
  grisés + badge ; si listes vides → message vide.
- **modèle supprimé** : absent de `GET /models` → non listé ; la sélection
  persistée pointe vers un id non listé mais le provider reste actif.
- **erreur API** : l'état loading reste honnête (pas d'item fantôme) ; les
  listes vides affichent le message vide.

---

## Relation Agent ↔ Model (représentée, non dupliquée)

ETHAN **permet de changer le modèle indépendamment de l'agent** (le pipeline
utilise « modèle utilisateur > défauts de l'agent »). L'UI représente donc :
- le **modèle imposé/default** de l'agent sous forme de badge dans l'item agent
  (`{provider}·{model}`) et dans le trigger `[Agent ▼ / modèle]` ;
- le **sélecteur de modèle reste indépendant** (l'utilisateur peut remplacer) ;
- les **capabilities** (tools/skills/knowledge) de l'agent sont visibles dans la
  `ChatContextBar` (non reprises ici pour éviter le doublon).

---

## Fichiers modifiés
| Fichier | Changement |
|---|---|
| `components/features/assistant/components/agent-selector.tsx` | prop `error` ; regroupement General/Spécialisée ; états loading/erreur/vide ; dédoublonnage Récents |
| `components/shared/model-selector.tsx` | capture `isLoading` ; regroupement par provider ; badge + blocage « Indisponible » ; états loading/vide |
| `components/features/assistant/components/assistant-top-bar.tsx` | prop + relais `agentsError` |
| `app/page.tsx` | destructure + passe `agentsError` |

## Validation
| Contrôle | Résultat |
|---|---|
| `tsc --noEmit` | ✅ exit 0 |
| `next lint` | ✅ No ESLint warnings or errors |
| Jest | ✅ 6 suites / 12 tests PASS |
| Dev server (3001) | ✅ actif |

## Hors périmètre
- Aucune modification Core/Runtime/API/backend.
- Pas de drag & drop, pas de « modifier l'agent » inline (→ `/agents`).
- Pas de création de catégorie agent côté Core (le regroupement est purement front,
  dérivé des capabilities réelles).
