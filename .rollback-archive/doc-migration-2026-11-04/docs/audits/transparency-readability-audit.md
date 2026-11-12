# Audit — Suppression des effets de transparence (WebUI)

## Date
11/09/2026

## Cause et sources identifiées

Toutes les transparences sont définies **statiquement côté frontend** (classes Tailwind,
CSS global, styles inline). Aucune classe/style n'est généré ou transmis par l'API :
le backend n'est pas responsable et n'a pas été modifié.

## Corrections appliquées (cause à la source)

### Backdrop-blur / glassmorphism — supprimés (11 + 1 CSS)

| Fichier | Avant | Après |
|---|---|---|
| `app/globals.css` (`.app-header`) | `color-mix(--bg 82%)` + `backdrop-filter: blur(8px)` | `var(--bg)` opaque |
| `components/ui/toast-provider.tsx` | `color-mix(--panel 88%)` + `backdrop-blur-md` | `var(--panel)` opaque |
| `components/ui/dialog.tsx` | overlay `bg-black/50 backdrop-blur-sm` | `bg-black/50` |
| `components/ui/command-palette.tsx` | overlay `backdrop-blur-sm` | supprimé |
| `providers/models-workspace.tsx` | dropdown `bg-bg-1/95 backdrop-blur-sm` | `bg-bg-1` opaque |
| `agents/agents-workspace.tsx` | dropdown `bg-bg-1/95 backdrop-blur-sm` | `bg-bg-1` opaque |
| `assistant/assistant-top-bar.tsx` | `bg-background/60` + `backdrop-blur` + `/40` | `bg-background` opaque |
| `layout/global-inspector.tsx` | backdrop mobile `backdrop-blur-sm` | supprimé |
| `layout/mission-control-overlay.tsx` | overlay `backdrop-blur-sm` | supprimé |
| `login/top-bar.tsx` | `bg-[#07090d]/70 backdrop-blur-sm` | `bg-[#07090d]` opaque |
| `login/loading-overlay.tsx` | `bg-[#07090d]/95 backdrop-blur-sm` | `bg-[#07090d]` opaque |
| `assistant/typing-indicator.tsx` | bulle `bg-background/40` | `bg-background` opaque |

### Surfaces semi-transparentes contenant du texte — opaquées (sed bulk)

Toutes les classes `bg-bg-1/N`, `bg-bg-2/N`, `bg-bg-3/N`, `bg-elevated/N`, `bg-muted/N`,
`bg-line-1/N` (≈ 70 occurrences : chat, sidebar, projects, knowledge, settings, providers,
agents, folders, mcp, flux…) remplacées par leurs tokens solides (`bg-bg-1`, etc.).
Les tokens `--bg-1/--bg-2/--bg-3/--elevated/--muted` sont opaques (`rgb(var(--*-rgb))`)
dans les deux thèmes, clair et sombre.

## Occurrences restantes — justifiées

| Occurrence | Catégorie | Justification |
|---|---|---|
| Overlays `bg-black/50`, `bg-black/60`, `bg-background/80`, `.sidebar-mobile-backdrop` | C — fonctionnel | Assombrissent l'arrière-plan ; panneaux/menus au-dessus sont opaques |
| Hover/active `color-mix(fg 6-12%)` (sidebar, listes) | C — état interactif | Retour visuel standard sur surface parente opaque |
| `bg-accent/5..20`, `bg-*-500/10` (badges d'état) | A — accent | Surlignage d'icônes/badges, jamais de contenu principal |
| `text-*/60..80`, `text-muted-foreground/30..70` | A — hiérarchie | Textes secondaires/muted, contraste suffisant sur fond opaque |
| `border-*/20..60`, `border-white/5` | A — décoratif | Bordures discrètes, identité visuelle conservée |
| `bg-white/10` (login) | A — décoratif | Séparateurs 1-4px sur fond opaque `#07090d` |
| `disabled:opacity-50`, `opacity-25/75` (spinner), `opacity-0→100` (transitions) | état fonctionnel | Désactivé / animation d'apparition |
| Opacités inline 0.5–0.85 (`inbox`, `research`, `cookbook`) | A — hiérarchie | Textes secondaires (timestamps, descriptions) sur fonds opaques, aucune surface translucide |
| Bordure toast `color-mix(accent 30%)` | A — décoratif | Texte posé sur `var(--panel)` opaque ; liseré gauche solide 3px |

Aucune opacité de parent n'affecte accidentellement du contenu lisible ; aucun
`backdrop-blur` décoratif ne subsiste (vérifié par grep : 0 occurrence).

## Validation

| Contrôle | Résultat |
|---|---|
| `tsc --noEmit` | exit 0 |
| `npx jest` | 14 suites / 48 tests passés |
| `next build` | exit 0 |
| grep `backdrop-blur|backdrop-filter|mix-blend|glass` | 0 occurrence |
| grep surfaces `bg-*/N` (tokens de surface) | 0 occurrence |
| Backend | non concerné (aucun style généré côté API) |

## Thèmes clair / sombre

Les corrections utilisent les tokens existants (`--bg`, `--panel`, `bg-bg-1`, `bg-background`),
définis opaques dans `:root` et dans le thème clair. Le correctif fonctionne donc dans les
deux thèmes sans valeur codée en dur.
