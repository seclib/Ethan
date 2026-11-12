# Dé-duplication des contrôles du chat — WebUI ETHAN

**Date** : 30/08/2026 · **Cible** : `http://localhost:3001`
**Problème** : régression UX — menus/contrôles ajoutés au centre du chat dupliquaient les sélecteurs du header.
**Périmètre** : uniquement la suppression des doublons visuels. **Aucun nouveau contrôle ajouté**, aucune fonctionnalité backend retirée.

---

## Inventaire avant correction

| Zone | Contrôles présents | Doublon ? |
|---|---|---|
| **Header** | `[Agent Selector ▼]` · `[Model Selector ▼]` | — (positions principales) |
| **Centre (ChatContextBar)** | chip Agent cliquable, chip Model cliquable, chips Tools/Skills/Knowledge (info), chip Mémoire (info) | ✅ **Agent doublé** — clic ouvrait l'Inspector ; **Model doublé** — clic déroulait le menu du header |
| **Centre (état vide)** | logo ETHAN + phrase + pills Agens Models Providers Skills Settings | ✅ pills = doublons de navigation |
| **Composer** | Act · Plan · Agent · saisie · Send/Stop | — (conforme à l'architecture cible) |

## Suppressions effectuées

### 1. ChatContextBar — chips Agent/Model retirées
`src/components/features/assistant/components/chat-context-bar.tsx`
- Suppression des props `agentName`, `agentDescription`, `onAgentClick`, `modelName`, `modelConnected`, `onModelClick` de l'interface.
- Suppression des deux `ContextChip` rendus sous le header.
- La barre ne conserve que le contexte de capacités **absent du header** : Tools, Skills, Knowledge, Mémoire (règle anti-fantôme inchangée : rendue seulement si ≥ 1 capacité réelle).
- Note documentée dans le composant : « ces sélecteurs ont UNE position principale : le header du chat ».

### 2. page.tsx — props et code mort retirés
- Retrait des props dupliquées passées à `<ChatContextBar>`.
- Retrait des constantes `providerObj` / `modelLabel` / `modelConnected` (utilisées uniquement par les chips dupliquées) et de `openInspector` (utilisé uniquement par le chip Agent).
- Retrait de l'import `useUIStore` (devenu inutilisé) et des props `activeProvider`/`activeModel`/`onOpenModelSelector` passées à `AssistantChat` (le composer ne rend plus le sélecteur de modèle).

### 3. État vide minimaliste
`src/components/features/assistant/components/assistant-chat.tsx`
- Retrait des 5 pills de navigation du centre (Agents, Models, Providers, Skills, Settings).
- La présentation d'un nouveau chat est désormais : logo ETHAN + « Posez une question, demandez une analyse, ou lancez une tâche. » — aucune sélection en zone centrale.
- Retrait de l'import `Link` devenu inutilisé.

## Architecture cible (après)

```
HEADER
  [Agent Selector ▼]  [Model Selector ▼]        ← positions uniques
CENTRE
  (messages / streaming / état vide minimal)
  + barre de contexte CAPACITÉS uniquement      (outils/skills/connaiss./mémoire actives)
COMPOSER
  [Act] [Plan] [Agent]  saisie  [Send/Stop]
```

## Tests mis à jour

`tests/unit/assistant/ChatContextBar.test.tsx` :
- « rend les capacités pré-résolues SANS dupliquer Agent/Model (dé-duplication) » — vérifie que `Atreus` / `qwen2.5:7b · Ollama` ne sont **plus rendus**.
- « antifantôme : ne rend RIEN avec seulement des agents/modèles » — remplace l'ancien test clic Agent/Model (props supprimées).

## Validation

| Contrôle | Résultat |
|---|---|
| `tsc --noEmit` | ✅ 0 erreur |
| `next build` | ✅ exit 0 |
| `next lint` | ✅ aucun warning sur les fichiers modifiés |
| `jest` | ✅ 6 suites / 12 tests |
| Rebuild Docker + routes | ✅ conteneur healthy sur :3001 |