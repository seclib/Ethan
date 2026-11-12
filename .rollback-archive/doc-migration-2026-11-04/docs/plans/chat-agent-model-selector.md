# Sélecteurs Agent / Model du chat — WebUI ETHAN

**Date** : 30/08/2026 · **Cible** : `http://localhost:3001`
**Référence UX** : `examples/open-webui` (jamais importé — comportement et interactions uniquement).
**Périmètre** : sélecteurs du header chat. Aucun mock, aucun second store, aucun doublon backend.

---

## Composants Open WebUI étudiés

| Composant | Patterns retenus |
|---|---|
| `src/lib/components/chat/ModelSelector/Selector.svelte` | Recherche inline filtrante, **Escape ferme + blur du trigger**, **ArrowDown/ArrowUp** déplacent l'index clavier, **Enter** sélectionne l'item courant, saisie → reset de l'index à 0, `data-arrow-selected` + `scrollIntoView({block:"center"})`, groupes (Pinned / providers) |
| `src/lib/components/chat/ModelSelector.svelte` | Trigger compact `provider / model ▼` avec pastille d'état, changement appliqué aux prochains messages, pas de sélecteur Provider séparé (implicite par groupe) |
| `ChatPlaceholder.svelte` | Affichage de la sélection active au-dessus de la zone de saisie |

## Constat préalable : l'existant était déjà câblé

Audit préalable (avant corrections) — les briques posées lors des sessions précédentes sont **réellement fonctionnelles** :

- **AgentSelector** (`agent-selector.tsx`) : dropdown au clic, recherche filtrante, sections Récents / General / Spécialisée (dérivées des vraies `capabilities` du Core), état sélectionné coché, « Nouvel agent… » → `/agents`, états loading / erreur / vide affichés, click outside, Escape dans la recherche, items `role="option"` avec Enter/Espace.
- **ModelSelector** (`model-selector.tsx`) : trigger compact `● provider / model ▼` (pastille d'état du provider), recherche, épinglage (localStorage), **regroupement par provider** (Provider implicite — pas de troisième sélecteur), modèles `is_available === false` grisés non sélectionnables, click outside, states loading/vide.
- **Sources réelles** : agents via `GET /v1/agents` (`useAgents` — cache React Query partagé avec `/agents`) ; modèles via `GET /models` (`useModels`) ; providers via `/providers` (`useActiveModel`).
- **Application réelle au chat** : `src/app/page.tsx` `runStream()` transmet `provider_id`, `model`, `agent_id` (+ skills/tools/knowledge/files) à `POST /v1/chat/completions/stream`. La sélection est **lue au moment de l'envoi** → s'applique au **prochain message**, sans casser la conversation en cours.
- **Persistance** : `ethan.active-agent` + `ethan.recent-agents` (max 3) ; `ethan.active-provider` + `ethan.active-model` ; `ethan.pinned-models` (localStorage). La sélection d'un provider non-défaut appelle en plus `PUT /providers/{id}/default` (synchronisation backend réelle).

## Corrections apportées (cette session)

Le manque identifié face au pattern Open-WebUI : **pas d'Escape global** (ModelSelector) et **pas de navigation flèches** dans les deux menus. Ajouté :

| Correction | AgentSelector | ModelSelector |
|---|---|---|
| `ArrowDown` / `ArrowUp` : déplacement de l'index clavier | ✅ (liste aplatie Sans agent → Récents → groupes) | ✅ (liste aplatie Pinned → providers) |
| `Enter` : sélection de l'item courant | ✅ | ✅ (jamais sur un modèle `is_available === false`) |
| `Escape` : fermeture du menu | ✅ (recherche) | ✅ (ajouté) |
| Saisie → index clavier ramené à 0 | ✅ | ✅ |
| Surlignage item courant (`ring-accent/60`) + `data-arrow-selected="true"` + `scrollIntoView({block:"center"})` scopé au dropdown | ✅ | ✅ |

Détails : `flatItems`/`flatAgents` (`useMemo`) reconstruisent l'ordre exact du rendu pour que l'index clavier corresponde visuellement ; le `scrollIntoView` est scopé au `dropdownRef` du menu (pas de collision entre menus) ; `requestAnimationFrame` garantit un DOM à jour avant le scroll.

## Source réelle des données (aucun doublon)

```
ETHAN Core
  ├─ GET /v1/agents   → useAgents (React Query) → AgentSelector
  ├─ GET /models      → useModels (React Query) → ModelSelector (menu)
  └─ GET /providers   → useActiveModel          → trigger compact + défaut backend
         ↓ sélection
  localStorage (préférences) + PUT /providers/{id}/default (défaut backend)
         ↓ envoi
  POST /v1/chat/completions/stream { provider_id, model, agent_id, … }

## Logique Provider

- **Provider implicite dans le Model Selector** (recommandation appliquée) : les groupes du menu sont les providers (Ollama, autres…), le trigger affiche `provider / model`, choisir un modèle du groupe **sélectionne le provider** (`setProvider` + `setModel`).
- Relation technique ETHAN respectée : le payload porte `provider_id` + `model` — la résolution reste Core-side.
- Pastille d'état du provider actif (connecté/gris) visible sur le trigger ; provider offline → ses modèles passent « Indisponible » (grisés, non sélectionnables, épinglage conservé).

## Comportement après changement

| Sélection | Effet | Persistance |
|---|---|---|
| Agent | `agent_id` du prochain message ; métriques du header mises à jour ; agent disparu → repli « Sans agent » + toast | localStorage + Récents |
| Model (+provider implicite) | `provider_id` + `model` du prochain message ; si provider ≠ défaut → `PUT /providers/{id}/default` | localStorage |
| Conversation en cours | **Jamais cassée** : l'historique reste affiché, le changement vaut pour les messages suivants | — |

## Limitations backend (documentées, non simulées)

1. Pas de paramètre « mode » (Act/Plan) dans l'API chat — voir `chat-composer-simplification.md`.
2. Le changement de modèle s'applique au prochain message ; il n'existe pas d'API de « re-génération avec un autre modèle » au-delà de la régénération existante (renvoi du dernier message utilisateur).
3. Les préférences agent/modèle sont par navigateur (localStorage) — pas de sync serveur des préférences UI à ce jour.

## Test

| Cas | Vérification |
|---|---|
| Agent : clic → ouverture → recherche → sélection → fermeture | ✅ dropdown + filtre + `handleSelect` + `close()` |
| Agent : click outside / Escape | ✅ listener `mousedown` + Escape |
| Agent : clavier (flèches + Enter) | ✅ ajouté (pattern OWUI) |
| Agent : loading / erreur / aucun agent | ✅ messages dédiés dans le menu |
| Model : clic → recherche → groupes provider | ✅ |
| Model : sélection → `setProvider`+`setModel` → payload suivant | ✅ `runStream()` |
| Model : modèle indisponible / provider offline | ✅ grisé, non sélectionnable, badge « Indisponible » |
| Model : clavier (flèches + Enter + Escape) | ✅ ajouté (pattern OWUI) |
| Refresh | ✅ préférences restaurées depuis localStorage |
| Mobile / responsive | ✅ trigger compact, menu `right-0` `w-80`, items tactiles |
| Dark / light | ✅ tokens uniquement |

## Validation

| Contrôle | Résultat |
|---|---|
| `tsc --noEmit` | ✅ 0 erreur |
| `next build` | ✅ exit 0 |
| `next lint` | ✅ uniquement le warning `<img>` préexistant (logo) |
| `jest` | ✅ 6 suites / 12 tests |
| Rebuild Docker + routes | ✅ conteneur healthy sur :3001 |

```

- Un seul catalogue par ressource, partagé entre chat et pages dédiées (invalidation React Query croisée).
- Aucun agent/modèle hardcodé ; aucun second store créé.
