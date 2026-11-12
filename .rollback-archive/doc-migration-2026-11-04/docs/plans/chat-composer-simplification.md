# Simplification du composer de chat — WebUI ETHAN

**Date** : 30/08/2026 · **Cible** : `http://localhost:3001`
**Périmètre** : zone de composition du message uniquement. **Aucune modification d'ETHAN Core, du Runtime, ni de la logique de génération.**

---

## Éléments retirés visuellement du composer

| Élément retiré | Raison | Où la capacité reste accessible |
|---|---|---|
| QuickAction **Skills** (popper de sélection) | Surcharge ; sélection par requête non indispensable | Page `/skills` (CRUD + toggle réels), API `/skills` |
| QuickAction **Tools** (popper de sélection) | Idem | Page `/tools` + onglet MCP (réels), API `/tools`, sync serveurs |
| QuickAction **Knowledge** (popper de sélection) | Idem | Page `/knowledge` (collections/ingestion réelles), API `/knowledge` |
| Bouton **Joindre** (paperclip) + strip de pièces jointes | Hors structure cible | Upload intact via `lib/api/files.ts` et la page Knowledge |
| Bouton **modèle actif** dans le composer | Redondant : le sélecteur **Model ▼** est déjà dans la top bar du chat | Top bar chat (ModelSelector) + page `/models` |
| Hint clavier texte « Entrée ↵ · Maj + Entrée » | Encombrant ; remplacé par tooltip sur le bouton Send | Tooltip « Envoyer (Entrée) » |

- **Aucune fonctionnalité backend supprimée** : `skill_ids`, `collection_ids`, `tool_ids`, `file_ids` restent des champs valides de `ChatCompletionRequest` (`src/lib/api/chat.ts`) et des API Core.
- Les props du composant (`skills`, `collections`, `tools`, `onToggle*`, `onOpenModelSelector`, `activeProvider/Model`, `onFileAttached`) sont **conservées dans l'interface** d'`AssistantInput` pour compatibilité d'appel (`assistant-chat.tsx` inchangé) mais ne sont plus rendues — documenté dans le code.

## Éléments conservés

```
┌─────────────────────────────────────────────┐
│  Message ETHAN...                           │
│                                             │
│  [Act]  [Plan]  [Agent ▼]           [ ↑ ]   │
└─────────────────────────────────────────────┘
```

- Zone de saisie auto-extensible (max 200px), placeholder « Message ETHAN... ».
- Trois contrôles à gauche, **Send/Stop toujours visible** à droite.
- Le sélecteur Agent n'apparaît que si le Core expose des agents (état réel, zéro mock).

## Comportement Act

- **État** : mode standard, actif par défaut (badge accenté, `aria-pressed="true"`).
- **API** : envoi standard `POST /v1/chat/completions` (+ stream) — le comportement réel actuel d'ETHAN.
- **Véracité** : c'est le mode existant, simplement nommé explicitement. Non désactivable : mode par défaut du système.

## Comportement Plan

- **Constat backend** : le Core possède un module planner (`core/modules/planner/main.py`, routage d'intention « plan » dans `core/orchestrator/router.py`), **mais** l'API chat (`/v1/chat/completions` + stream, `interfaces/api/routers/v1.py`) n'expose **aucun paramètre de mode** — le payload (`ChatCompletionRequest`) ne contient que message/chat/provider/model/agent/skills/collections/tools/files/metadata.
- **Décision** : bouton **visible mais désactivé** (`disabled` + `aria-disabled` + `cursor-not-allowed`), tooltip explicite : « Planification gérée automatiquement par le Core — sélection manuelle non encore disponible ». **Aucune simulation** : pas de faux état actif, pas d'appel API fantôme.
- Évolution future : si l'API expose un champ `mode: "plan"`, le contrôle se câble en quelques lignes.

## Comportement Agent

- **État** : dropdown réel conservé (agents du Core via `GET /v1/agents`, hook `useAgents` — zéro mock).
- **API** : `agent_id` transmis dans `ChatCompletionRequest` (« Routage Chat → Agent, résolu par le Core »).
- Options : « Sans agent » (défaut) + agents disponibles + lien « Créer/Configurer un agent » → `/agents`.
- Note : le même choix reste possible dans la top bar (AgentSelector) — les deux sont synchronisés par la page (`useActiveAgent`).


## Comportement du bouton Send

| Situation | Rendu |
|---|---|
| Message vide | Disabled (`bg-line-2`, curseur grisé) |
| Message valide | Actif, rond `h-9 w-9`, fond accent, icône Send, ombre légère |
| Génération en cours | Devient **Stop** : rond rouge (`bg-red-500`), icône carré plein, `aria-label="Arrêter la génération"` |
| Accessibilité | `title="Envoyer (Entrée)"` + `aria-label="Envoyer le message"` |

- Toujours visible, indépendant d'Enter (le clic est le chemin primaire, Enter le raccourci).
- Taille augmentée (h-8 → h-9) pour la visibilité ; contraste assuré par les tokens `--accent` (dark & light).

## Raccourcis clavier

| Touche | Action | État |
|---|---|---|
| **Enter** | Envoyer | ✅ inchangé (vérifié `handleKeyDown`) |
| **Shift + Enter** | Nouvelle ligne | ✅ inchangé (`!e.shiftKey` conditionne l'envoi) |
| **Échap** | Fermer le dropdown Agent | ✅ conservé |

## Fichiers modifiés

| Fichier | Changement |
|---|---|
| `src/components/features/assistant/components/assistant-input.tsx` | Restructuration en colonne (textarea / rangée contrôles) ; retrait QuickActions Skills/Tools/Knowledge, paperclip + strip, bouton modèle, hint clavier ; ajout modes Act/Plan ; Send agrandi + aria-labels ; suppression code mort (`OptionGroup`, `QuickAction`, logique upload locale) et imports ; props d'interface conservées (compat) |
| `docs/plans/chat-composer-simplification.md` | Ce rapport |

**Non modifiés** : `assistant-chat.tsx` (appelle toujours `AssistantInput` avec les mêmes props), `assistant-top-bar.tsx`, `use-chats.ts`, `lib/api/chat.ts`, tout le backend.

## Test

| Cas | Résultat | Vérification |
|---|---|---|
| Message vide | Send disabled | ✅ `!message.trim()` |
| Message valide | Send actif → `onSend(trimmed)`, textarea vidé et hauteur réinitialisée | ✅ `handleSend` |
| Multilignes | Textarea auto-extensible jusqu'à 200px | ✅ `handleInput` |
| Enter | Envoi | ✅ |
| Shift + Enter | Saut de ligne | ✅ |
| Send au clic | Envoi sans dépendre d'Enter | ✅ bouton dédié |
| Génération | Stop rouge visible (`disabled && onStop`) | ✅ |
| Stop | `onStop?.()` → stream marqué « stopped » (logique existante) | ✅ inchangé |
| Act / Plan / Agent | Act actif ; Plan désactivé explicite ; Agent fonctionnel (API réelle) | ✅ |
| Responsive | Labels raccourcis (`A`/`P`) sous `sm`, layout colonne intact | ✅ |
| Dark / light | Tokens `--accent`, `--line-*`, `--bg-*` — aucun hex codé en dur | ✅ |

## Validation

| Contrôle | Résultat |
|---|---|
| `tsc --noEmit` | ✅ 0 erreur |
| `next build` | ✅ exit 0 |
| `next lint` | ✅ uniquement le warning `<img>` préexistant (logo) |
| `jest` | ✅ 6 suites / 12 tests |
| Rebuild Docker + routes | ✅ conteneur healthy sur :3001 |
