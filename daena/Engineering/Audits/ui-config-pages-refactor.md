# Refonte UX/UI des pages de configuration — card grid (inspiré Open-WebUI)

> **Date** : 26 août 2026 · **Portée** : frontend uniquement (`interfaces/webui/src/components/features/**/components/*-workspace.tsx`).
> **Conformité** : aucun changement Core/Runtime/API/modèles de données. Les hooks et dialogs existants sont réutilisés tels quels. Aucune logique métier réinventée côté frontend.

## Objectif

Transformer les pages de configuration en **grilles de cartes** homogènes et découvrables, suivant le pattern Open-WebUI :

```
Header · Search · Filter · List/Grid · Card · Menu contextuel · Modal/Drawer
```

L'utilisateur lit une capacité d'un coup d'œil (statut, modèle, capacités, actions), et la
configuration profonde reste accessible via la carte cliquable / le menu ⋮ qui ouvrent le
dialog **existant** — pas de nouvelle interface parallèle.

## Pages refondues

### 1. Agents — `src/features/agents/components/agents-workspace.tsx`

**Avant** : panneau double liste+detail. **Après** : grille de cartes + recherche + menu contextuel.

| Zone | Contenu |
|---|---|
| Header | recherche par nom + bouton **Nouvel agent** |
| Carte | icône Bot + nom + description (2 lignes) · badge statut (Actif/Pause/Erreur…) · `provider · model` · badges capacités (max 3, +N) · compteurs 🛠 outils / 🧠 skills / 📚 connaissances |
| Menu ⋮ | Configurer · Exécuter une tâche · Utiliser dans le chat · Dupliquer · Supprimer |
| Actions rapides (hover) | ▶ démarrer · ❚❚ pause · ■ arrêter |
| Dialog | `AgentEditorDialog` (existant) pour créer/configurer ; Dialog d'exécution réutilisé |

**Réutilisé tel quel** : `useAgents`, `useUpdateAgent`, `useDeleteAgent`, `useExecuteAgent`, `useCreateAgent`, `AgentEditorDialog`, `Badge`, `Dialog`, `Textarea`.

### 2. Models — `src/features/providers/components/models-workspace.tsx`

**Avant** : grille basique (Card) sans menu contextuel. **Après** : grille homogène + recherche en tête + filtre Favoris + menu contextuel.

| Zone | Contenu |
|---|---|
| Barre | recherche par nom/id/provider/capability (`searchModels`) + bouton **Favoris** |
| Carte | icône DB + nom + label Local/Provider · `model · ctx length` · badges capabilities · qualité · badge Disponible/Indisponible |
| Menu ⋮ | Épingler/Désépingler · Voir la fiche |
| Action star | épingler (fill accent si épinglé) |
| Empty state | CTA « Activez un fournisseur dans Fournisseurs » |

**Réutilisé tel quel** : `useModels` (`searchModels`, `pinModel`, `unpinModel`, `isPinned`), `Badge`.

## Pattern de carte réutilisable (toutes pages)

```
<div card group>
  header: icône + (nom + sous-titre) + bouton ⋮ (hover)
  body:   statut/pastille + métadonnées + badges
  footer: compteurs / note
  actions hover: boutons d'action rapide
</div>
```

Ce gabarit est **repris tel quel pour Agents, Models, puis Skills, Tools, Knowledge, MCP, Providers** (étapes suivantes du périmètre).

## Fichiers modifiés

| Fichier | Action |
|---|---|
| `agents/components/agents-workspace.tsx` | refactor → card grid + menu contextuel |
| `providers/components/models-workspace.tsx` | refactor → card grid + header search + favoris + menu contextuel |

## Backend intact

`useAgents`, `useModels`, `lib/api/agents.ts`, `lib/api/models.ts`, `lib/api/providers.ts` : **aucun diff**. Seule la couche de présentation change.

## Validation exécutée

| Contrôle | Résultat |
|---|---|
| `npx tsc --noEmit` | exit 0 |
| `npx next lint` | No ESLint warnings or errors |
| `npm test` (Jest) | 6 suites / 12 tests PASS |
| `/agents` SSR | OK (« Rechercher un agent », « Nouvel agent » présents) |
| `/models` | 200 |

## Prochaines étapes (hors périmètre cette session)

Appliquer le même gabarit à : **Skills**, **Tools**, **Knowledge**, **MCP** (absorbé dans Tools), **Providers**. Chaque étape conserve les hooks existants et ne change que la couche présentation.

*Document de refonte — seule la présentation des pages Agents et Models a été modifiée.*