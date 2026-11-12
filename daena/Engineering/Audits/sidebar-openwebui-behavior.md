# Sidebar — comportement Open-WebUI (refonte v5)

**Date** : 30/08/2026 · **Cible** : `http://localhost:3001`
**Référence** : comportement Open WebUI (sidebar conversation-centric, rail replié minimal).
**Périmètre** : comportement de la sidebar uniquement. Aucune suppression de fonctionnalité backend ; toutes les routes restent accessibles.

---

## Avant / Après

**AVANT** : rail replié = colonne d'une vingtaine d'icônes techniques (dashboard) ; sidebar déployée = 5 sections longues (Workspace technique + Pilotage + Système + Préférences + Administration).

**APRÈS** :

```
Replié                                Déployé
┌────┐                                ┌──────────────────────────────┐
│ ☰  │   (logo — déplier)             │ ETHAN                     ☰ │
│ +  │   Nouveau chat                 │ [+ Nouveau chat]             │
│ 🔍 │   Rechercher (Ctrl+K)          │ [🔍 Rechercher…    Ctrl K]   │
│    │                                │ CHATS (conversations)        │
│ ⚙  │   Settings (UserBar)           │   • conversation A…          │
└────┘                                │ ASSISTANTS                   │
                                      │   Agents                     │
                                      │ PILOTAGE                     │
                                      │   Missions · Calendar · …    │
                                      │ ──────────────────────────   │
                                      │ ⚙ Settings → (navigation     │
                                      │    secondaire technique)      │
                                      │ ADMINISTRATION (compacte)     │
                                      │ Diagnostics · Logs · …        │
                                      │ [👤 …  ⚙  ⏻]                 │
                                      └──────────────────────────────┘
```

Le rail replié est **minimal** (3 icônes utiles : déplier, nouveau chat, recherche) — plus de colonne d'icônes techniques. L'utilisateur déplie pour découvrir la navigation complète + les conversations.

## 1. État compact — minimal

`src/components/layout/sidebar.tsx`
- Suppression de la boucle `NAV_SECTIONS.flatMap(...)` qui rendait **toutes** les icônes.
- Rail replié = `☰` (toggle, logo) + `+` (Nouveau chat) + `🔍` (Rechercher Ctrl+K) + UserBar compact (Settings + déconnexion).
- Chaque icône porte `title`/`aria-label` (tooltip) — utilité claire.

## 2. Sidebar déployée — conversation-centric

- Header `ETHAN` + bouton replier (`PanelLeftClose`).
- Actions : `Nouveau chat` + `Rechercher… (Ctrl K)`.
- **CHATS** : conversations du store (`ChatSection` — épinglées, récentes, période) — cœur Open-WebUI.
- **Navigation quotidienne** : `Assistants` (Agents) + `Pilotage` (Missions, Calendar, Notes, Inbox, Deep Research, Cookbook).
- **`Settings`** : entrée dédiée en bas de la sidebar (avec indicateur `↳` quand actif) = porte d'entrée de la navigation secondaire technique.
- **`Administration`** : section compacte en bas, réellement fonctionnelle (audit : option A).

## 3. Navigation secondaire (sections techniques)

Les entrées techniques ne remplissent plus la sidebar principale. Elles sont déléguées à :

- **Page Settings** (nav par sections) : General, Appearance, Models, Providers, Knowledge, RAG, Skills, Agents, Tools, MCP — avec liens `WorkspaceLink` vers `/knowledge`, `/skills/lab`, `/agents`, `/tools`, et désormais `/models` (ajouté).
- **Palette Ctrl+K** : commandes « Go to Agents / Models / Providers / Knowledge / Tools / Missions / Settings… » (déjà présentes, vérifié).
- **Routes directes** : intactes (`/providers`, `/models`, `/knowledge`, `/tools`, `/skills`, `/diagnostics`, `/security`… toutes en 200).

`nav-config.ts` v5 restructure en `NAV_SECTIONS_PRIMARY` (sidebar) + `NAV_SECTIONS_ADMIN` + `NAV_SECTIONS_SECONDARY` (Settings/Ctrl+K) + `NAV_SECTIONS` (union pour résolution du label du header).

## 4. Persistence (inchangée — déjà conforme)

- `sidebarPreference` (localStorage `ethan-ui-storage`) : écrite **uniquement** par l'action de l'utilisateur (toggle).
- `sidebarExpanded` (runtime) : jamais persistée, `true` au boot → **nouvel utilisateur voit la sidebar déployée** (découvrabilité).
- `onRehydrateStorage` restaure la préférence explicite au refresh.
- Fermeture automatique mobile : ne persiste rien.

## 5. Responsive (inchangé — déjà conforme)

- Desktop : sidebar inline repliable.
- Laptop : adaptable (< 768px uniquement).
- Mobile : **drawer overlay** (`sidebar-mobile-open`, backdrop cliquable, animation `drawer-in`) — jamais un simple rétrécissement.

## 6. Routes — intactes

Vérifié après build : `/`, `/login`, `/agents`, `/models`, `/providers`, `/skills`, `/knowledge`, `/tools`, `/settings`, `/workspace`, `/missions`, `/calendar`, `/notes`, `/inbox`, `/research`, `/cookbook`, `/security`, `/diagnostics` → **18/18 HTTP 200**.

## Validation

| Contrôle | Résultat |
|---|---|
| `tsc --noEmit` | ✅ 0 erreur |
| `next build` | ✅ exit 0 |
| `next lint` | ✅ propre (fichiers modifiés) |
| `jest` | ✅ 6 suites / 12 tests |
| Rebuild Docker + routes | ✅ conteneur healthy sur :3001 |

## Problèmes restants (non bloquants)

1. Pas de module « Projets » dans ETHAN → **pas** de bouton/New Project factice (règle anti-fantôme). Si un système de dossiers/projets voit le jour côté Core, il suffira d'ajouter une section `Projets` au-dessus des conversations.
2. Les sections du rail replié ne montrent plus la navigation quotidienne — le dépliage est le chemin primaire (comportement Open-WebUI assumé).
3. `openGroups` (groupes ouvertes/repliés) n'est pas persisté — réinitialisé « ouvert » à chaque montage (choix découvrabilité, inchangé).