# Refonte du Composer de chat ETHAN (inspiré Open-WebUI)

> **Date** : 27 août 2026 · **Portée** : frontend uniquement — `interfaces/webui/src/components/features/assistant/components/assistant-input.tsx`.
> **Conformité** : aucun changement Core/Runtime/API. Le composer continue d'appeler le système de chat ETHAN existant (`onSend`/`onStop`). Aucune nouvelle logique de génération.

## Objectif

Transformer le composer en une zone de saisie moderne et extensible, avec une **barre d'outils visible** (au lieu d'un menu « + » qui cachait tout), conforme à Open-WebUI :

```
Message…
────────────────────────────
📎 Joindre   🧠 Skills   🛠 Tools   📚 Knowledge   🤖 Agent   ⚙ …   [Send ↵]
```

Chaque capacité est un bouton direct, découvrable, avec un **compteur** des éléments actifs — plus rien n'est enfoui dans un menu unique.

## Structure du nouveau composer

```
┌──────────────────────────────────────────┐
│  Message… (textarea auto-resize)        │
│  ──────────────────────────────────────  │
│  📎 Joindre · Skills · Tools · Knowledge │
│  · Agent                        Send ↵  │
│  [popper de sélection rattaché]          │
└──────────────────────────────────────────┘
```

## Ce qui a changé

| Avant | Après |
|---|---|
| Un seul menu « + » ouvrant un dropdown unique | Barre d'outils persistante avec boutons directs |
| Toutes les capacités masquées derrière le + | Chaque capacité (Skills/Tools/Knowledge/Agent) = bouton visible + compteur |
| Agent accessible uniquement dans le menu | Bouton **Agent** à part entière (libellé = nom de l'agent actif) |
| Un seul état `menuOpen` global | État `activeMenu` (`skills`/`tools`/`knowledge`/`agent`/`files`/null), ouvert + fermeture par clic extérieur/Échap |

## Fonctionnalités ETHAN réelles utilisées (intactes)

- **Pièces jointes** : `uploadFile(file)` depuis `lib/api/files` → chips retirables + `onFileAttached` (même flux qu'avant).
- **Skills** : catalogue `skills` + `selectedSkillIds` + `onToggleSkill`.
- **Tools** : catalogue `tools` + `selectedToolIds` + `onToggleTool`.
- **Knowledge** : catalogue `collections` + `selectedCollectionIds` + `onToggleCollection`.
- **Agent** : catalogue `agents` + `selectedAgentId` + `onSelectAgent` — sélection unique désactivable, cohérent avec le **Agent Selector** du header.
- **Envoi** : `onSend(message)` (streaming piloté par le parent) — aucun changement.
- **Stop generation** : bouton Arrêter ⊓ (`onStop`) quand `disabled && onStop`.
- **Raccourcis clavier** : `Enter` = envoyer · `Shift+Entrée` = saut de ligne · `Échap` = fermer un menu.

## Interface inchangée (composant réutilisable)

`AssistantInputProps` : toutes les props existantes sont conservées à l'identique
(`onSend`, `onStop`, `disabled`, `onFileAttached`, `skills`, `collections`, `tools`, `agents`,
`selected*Ids`, `onToggle*`, `onSelectAgent`). Aucun parent (`page.tsx`, `assistant-chat.tsx`) n'a besoin d'être modifié.

## Comportements couverts

- Nouveau chat / conversation existante : inchangé (le parent gère le chat courrant).
- Streaming : bouton Envoyer → bouton Arrêt (piloté par `disabled`+`onStop`).
- Erreur backend : remontée par le parent sous forme de bannière (inchangé).
- Changement de modèle / d'agent : le header (Model/Agent Selector) reste la source ; le bouton Agent reflète la sélection.
- Pièce jointe : upload réel + chips retirables.

## Validation

| Contrôle | Résultat |
|---|---|
| `npx tsc --noEmit` | exit 0 |
| `npx next lint` | No ESLint warnings or errors |
| `npm test` (Jest) | 6 suites / 12 tests PASS |
| Route `/` SSR | render OK : boutons Joindre/Skills/Tools/Knowledge/Agent présents |

## Hors périmètre

- Aucune modification de la logique de génération / streaming (reste dans `use-chats` + Core).
- Pas de changement aux sélecteurs header (Agent Selector / Model Selector).
- Pas de refactor du parent `page.tsx` ni `assistant-chat.tsx`.
