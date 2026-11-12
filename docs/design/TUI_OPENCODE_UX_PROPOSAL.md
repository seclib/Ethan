# Proposition de refonte UX — TUI ETHAN (référence OpenCode)

Date : 2026-11-10  
Statut : Proposition corrigée (en attente de validation avant implémentation)

## 1. Identité visuelle

- **Nom affiché** : « Ethan » (texte sobre, pas de logo, pas d'ASCII art, pas de symbole graphique).
- **Typographie** : sobre, dans l'esprit d'OpenCode et Claude Code.
- **Thème** : sombre, élégant, professionnel, minimaliste.
- **OpenCode** : référence d'apparence et d'ergonomie, pas d'architecture ni de moteur.

## 2. Layout définitif

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  Ethan  │  agent: Atreus  │  model: lfm3-omni  │  provider: ollama  │  …   │  ← header discret (1 ligne, sans bordure)
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  conversation (sans bordure, flux continu)                                    │
│    ▸ vous                                                                    │
│      message                                                                 │
│    ◆ ethan                                                                   │
│      réponse Markdown                                                        │
│      ▶ tool X  ✓ success  1.2s  [+]                                          │
│      ⚠ permission_request: tool Y                                            │
│        [a]utoriser  [r]efuser                                                │
│                                                                              │
│  ❯ composer (multiligne, toujours visible)                                   │
│                                                                              │
│  ● connecté  │  session: d2f8…  │  ↑/↓ scroll  │  Tab sidebar  │  Ctrl+K  │  ← status bar compacte (1 ligne)
└──────────────────────────────────────────────────────────────────────────────┘
```

**Zones :**
1. **Header** (1 ligne, haut) : « Ethan » + agent + modèle + provider + session + erreur. Sans bordure.
2. **Conversation** (centre, espace maximal) : flux continu sans bordure. Messages, tool calls inline, permissions inline.
3. **Composer** (bas, 3-7 lignes) : saisie multiligne, toujours visible.
4. **Status bar** (1 ligne, bas) : connexion, session, raccourcis.
5. **Sidebar** (droite, optionnelle) : masquée par défaut, activée avec Tab. Session list + agent/model/provider/tools/HROT.

**Sidebar** : facultative, adaptative, ne jamais à gauche. Apparaît à partir de 100 colonnes.

## 3. Raccourcis clavier (sans conflit)

| Touche | Action | Contexte |
|---|---|---|
| `Enter` | Envoyer le message | Composer |
| `Ctrl+J` | Nouvelle ligne | Composer |
| `Tab` | Focus sidebar (si entrée vide, ≥100 cols) / autocomplétion | Global |
| `Ctrl+K` | Palette de commandes | Global |
| `↑` / `↓` | Historique (monoligne) / déplacement ligne (multiligne) / navigation sidebar | Contextuel |
| `PgUp` / `PgDn` | Défilement conversation | Global |
| `e` | Développer/réduire le dernier tool call | Si entrée vide, pas de panneau |
| `a` / `r` | Autoriser / refuser HROT | Si permission en attente |
| `Esc` | Fermer panneau / refuser permission / sortir du focus sidebar | Global |
| `Ctrl+C` | Annuler le flux / quitter si inactif | Global |
| `Ctrl+D` | Quitter si entrée vide | Global |

**Aucun conflit** : `Tab` est soit autocomplétion (entrée non vide) soit focus sidebar (entrée vide). `Ctrl+K` est exclusivement la palette. `e` ne se déclenche que si l'entrée est vide.

## 4. Composants actuels à réutiliser

- `TuiCoreClient` (frontière HTTP unique).
- `TuiState` (état mutable, étendu).
- `Terminal` (lecture clavier, étendu pour multi-ligne et bracketed paste).
- `run_stream_worker` (thread SSE).
- Modèles typés (`Agent`, `Model`, `Provider`, `Tool`, `ChatSummary`, `ChatMessage`, `StreamEvent`).
- Slash commands et handlers.
- `_load_initial`, `_submit`, `_apply_event`.
- Contrats Core (aucune modification).

## 5. Composants de présentation à restructurer

- `_render_header` : 3 lignes → 1 ligne sans bordure.
- `_render_conversation_panel` : panneau bleu → flux continu sans bordure.
- `_render_input` : monoligne → multiligne (déjà fait).
- `_render_sidebar_panel` : 6 sections compactes → garder mais simplifier (déjà fait).
- `_render_status` : enrichir (déjà fait).
- Blocs Tool `┌─ tool ─┐` → chevron inline (déjà fait).
- Overlay permission → bloc inline (déjà fait).

## 6. Plan d'implémentation visuelle incrémental

| Phase | Action | Risque | Tests |
|---|---|---|---|
| 1 | Header 1 ligne sans bordure, status bar enrichie | Faible | `"ETHAN TUI" in frame` |
| 2 | Conversation sans bordure, messages inline | Moyen | Contenu des messages dans le rendu |
| 3 | Tool calls inline (chevron, durée, expand/collapse) | Moyen | `tool` et `status` dans le rendu |
| 4 | Permission prompts inline | Moyen | `permission_request` affiche le bloc |
| 5 | Composer multiligne | Élevé | Saisie, soumission, historique |
| 6 | Sidebar masquée par défaut, activable | Faible | Affichage avec/sans sidebar |
| 7 | Spinner animé pendant le streaming | Faible | Spinner pendant le streaming |

## 7. Critères de validation sur terminal réel

- 120 × 40, 100 × 30, 80 × 24.
- Captures PTY réelles pour chaque phase.
- Comparaison avec OpenCode.
- Vérification des interactions réelles (pas uniquement les tests unitaires).

## 8. Ce qui ne change pas

- `TuiCoreClient` (frontière HTTP).
- `TuiState` (étendu, pas remplacé).
- `Terminal` (lecture clavier, étendu).
- `run_stream_worker` (thread SSE).
- Modèles typés.
- Slash commands et handlers.
- `_load_initial`, `_submit`, `_apply_event`.
- Contrats Core (aucune modification).
- `ethan cli` et `ethan tui` (distincts, non aliasés).
- HROT (aucun contournement).
- Aucune nouvelle dépendance.

## 9. Prochaine étape

En attente de votre validation. Après validation, implémentation phase par phase. Chaque phase testée avant la suivante. Aucun fichier n'a été modifié lors de cette analyse.