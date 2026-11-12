# Première expérience de navigation — WebUI ETHAN

**Date** : 30/08/2026 · **Cible** : `http://localhost:3001`
**Périmètre** : navigation, découvrabilité, première expérience après login. Aucune refonte de thème ni d'architecture ; aucune fonctionnalité supprimée.

---

## Comportement avant

```
Login → Chat → sidebar RÉDUITE (rail d'icônes) → structure illisible
```

- La sidebar démarre repliée pour un nouvel utilisateur : les 5 sections ne sont visibles que comme icônes sans contexte.
- Cause racine : l'effet responsive de `sidebar.tsx` appelait `toggleSidebar` sous 768px — or `toggleSidebar` **persiste** l'état dans `localStorage` (`ethan-ui-storage`). Un login sur fenêtre étroite/mobile écrivait donc `sidebarExpanded: false` comme préférence définitive, appliquée ensuite partout.
- Sections au nommage peu explicite (Explore / Settings mixant Providers+Memory+General+Interface).

## Comportement après

```
Login → Chat → sidebar DÉPLOYÉE (icônes + libellés) → structure lisible immédiatement
```

### Hiérarchie (nav-config v4)

Chaque en-tête de section porte un tooltip descriptif (`title`), aucune catégorie vide, aucune route fictive :

| Section | Contenu | Description affichée (tooltip) |
|---|---|---|
| (haut) | Nouveau chat · Rechercher · Conversations | — |
| **Workspace** | Agents, Models, Knowledge, Skills, Tools, MCP | « Capacités intelligentes d'ETHAN » |
| **Pilotage** | Missions, Calendar, Notes, Inbox, Deep Research, Cookbook | « Suivi au quotidien » |
| **Système** | Providers, Memory | « Fournisseurs de modèles et mémoire » |
| **Préférences** | Settings, Interface | « Comportement et apparence » |
| **Administration** | Diagnostics, Logs (ext.), Monitoring (ext.), Security | « Outils système et diagnostic — supervision » |

- **Pilotage conservé** : fonctionnalités réelles, aucune suppression (héritage des audits précédents).
- Groupes **ouverts par défaut** (`openGroups ?? true`) : la structure complète est visible d'emblée ; chaque groupe reste repliable individuellement.
- Administration assumée comme section de supervision (audit précédent : option A, réellement fonctionnelle) ; les liens externes Grafana restent marqués `external`.

## État initial sidebar & persistance

| Situation | Comportement |
|---|---|
| Nouvelle session / nouvel utilisateur (aucune préférence) | **DÉPLOYÉE** |
| Utilisateur a replié explicitement (bouton) | Repliée, préférence mémorisée |
| Utilisateur a redéployé explicitement | Déployée, préférence mémorisée |
| Session mobile sans préférence | Rail compact ; ouverture = **drawer overlay** |

Implémentation (`src/store/ui.store.ts`) :

- Nouveau champ `sidebarPreference: boolean | null` (persisté) distinct de l'état runtime `sidebarExpanded` (jamais persisté, toujours `true` au boot).
- `toggleSidebar()` (action utilisateur) écrit la préférence ; `setSidebarExpanded(v)` (programmatique : responsive, backdrop) **ne l'écrit jamais**.

## Premier écran Chat

Le chat reste le centre. État vide enrichi (`assistant-chat.tsx`) :

```
[logo]  ETHAN
        Posez une question, demandez une analyse, ou lancez une tâche.
        ( Agents ) ( Models ) ( Providers ) ( Skills ) ( Settings )   ← nouveaux raccourcis
```

- Sélecteurs **Agent ▼** et **Model ▼** toujours visibles dans la top bar du chat.
- Les raccourcis pointent vers des pages réelles uniquement — pure affichage, zéro logique métier (règle AGENTS.md).

## Sidebar repliée (rail)

- Icônes conservées + tooltips natifs (`title`) + état actif (`active`) — inchangé.
- Bouton de redéploiement évident en tête de rail (logo, `aria-label="Ouvrir la sidebar"`).
- Bouton de repli évident dans l'en-tête déployé (`PanelLeftClose`, `aria-label="Replier la sidebar"`).
- Animation de largeur conservée (`.sidebar` transition 0.25s).

## Navigation active

- `AppHeader` affiche le label de la page courante (résolution `NAV_ITEMS_FLAT` avec fallback par préfixe) + bouton retour chat — déjà en place, inchangé.
- `PageHeader` (titre + description) présent sur les pages migrées.
- L'item de sidebar actif est surligné (`active`) et son groupe auto-ouvert.

## Responsive

| Écran | Comportement |
|---|---|
| Desktop (≥ 768px) | Sidebar inline déployée par défaut, repliable |
| Laptop étroit | Identique (breakpoint mobile < 768px seulement) |
| Mobile (< 768px) | Rail compact par défaut ; ouverture = **drawer overlay** (position fixed, largeur `min(280px, 85vw)`, backdrop cliquable, animation `drawer-in`, z-index 48/49) |

- Le drawer mobile n'écrase plus le contenu (overlay) — fin du « simple rétrécissement » desktop.
- Fermer via backdrop ne persiste rien.
- Hook `useIsMobile()` (SSR-safe, `matchMedia`) ; fermeture runtime au montage mobile et au franchissement desktop→mobile uniquement (ref `prevMobile`, pas d'oscillation).

## Routes testées (SSR :3001, cookie probe)

`/login`, `/`, `/agents`, `/models`, `/providers`, `/skills`, `/knowledge`, `/tools`, `/settings`, `/workspace`, `/missions`, `/calendar`, `/notes`, `/inbox`, `/research`, `/cookbook`, `/security`, `/diagnostics` — **18/18 → 200**.

Parcours demandé : Login → Chat (sidebar déployée) → Agents → Models → Providers → Settings → retour Chat → collapse → **refresh → préférence persistée** ✅ (persist `sidebarPreference` + hydratation).

## Validation

| Contrôle | Résultat |
|---|---|
| `tsc --noEmit` | ✅ 0 erreur |
| `next build` | ✅ exit 0 |
| `next lint` | ✅ uniquement le warning `<img>` préexistant (logo, volontaire) |
| `jest` | ✅ 6 suites / 12 tests |
| Rebuild Docker `ui` + routes | ✅ conteneur healthy, 18/18 routes 200 |

## Problèmes restants (non bloquants)

1. Le rail mobile ne distingue pas visuellement les sections (flat) — acceptable, tooltips présents ; une future version pourrait grouper par séparateurs.
2. `openGroups` (ouvert/replié par groupe) n'est pas persisté — réinitialisé à « tout ouvert » à chaque montage. Choix assumé pour la découvrabilité.
3. La persistance de la préférence est par navigateur (localStorage) et non par compte — cohérent avec le scope actuel (pas de sync serveur des préférences UI).

- `onRehydrateStorage` applique la préférence explicite à l'hydratation.
- `partialize` ne persiste plus que `sidebarPreference` — un ancien `sidebarExpanded: false` stocké avant cette migration est simplement ignoré (clé non restaurée).
