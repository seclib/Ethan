/**
 * settings-nav — arborescence Settings d'ETHAN (taxinomie de présentation).
 *
 * Regroupe les sections EXISTANTES du SettingsWorkspace sous l'arborescence
 * cible validée (Lead Product Architect) :
 *
 *     Settings
 *     ├── General      (general, chat, reminders, shortcuts, library)
 *     ├── AI           (providers, models, routers, speech, ai→"Advanced")
 *     ├── Knowledge    (knowledge, rag, embedding, vector-db, chunking,
 *     │                 reranking, search)
 *     ├── Skills       (skills)
 *     ├── Integrations (integrations)
 *     ├── Security     (security)
 *     ├── Appearance   (appearance)
 *     └── Advanced     (system, capabilities, advanced)
 *
 * Règles :
 *  - **aucune section supprimée** : chaque id apparaît exactement une fois
 *    (couvert par tests/unit/settings/settings-nav.test.ts) ;
 *  - **aucune logique métier ici** (AGENTS.md) : ids + libellés uniquement —
 *    le rendu reste dans `settings-workspace.tsx`, la vérité reste dans Core ;
 *  - les groupes à section unique sont rendus sans en-tête (pas de doublon
 *    « Skills › Skills ») — c'est le consommateur (workspace) qui décide.
 */

export const SETTINGS_SECTION_IDS = [
  // General
  "general",
  "chat",
  "reminders",
  "shortcuts",
  "library",
  // AI
  "providers",
  "models",
  "routers",
  "speech",
  "ai",
  // Knowledge
  "knowledge",
  "rag",
  "embedding",
  "vector-db",
  "chunking",
  "reranking",
  "search",
  // Skills
  "skills",
  // Integrations
  "integrations",
  // Security
  "security",
  // Appearance
  "appearance",
  // Advanced
  "system",
  "capabilities",
  "advanced",
] as const;

export type SettingsSectionId = (typeof SETTINGS_SECTION_IDS)[number];

export interface SettingsGroup {
  /** Identifiant stable du groupe (raccourcis, tests, analytics). */
  id: string;
  /** Libellé affiché (en-tête de groupe dans la sidebar Settings). */
  label: string;
  /** Sections du groupe, dans l'ordre d'affichage. */
  items: readonly SettingsSectionId[];
}

/** Ordre exact de l'arborescence cible (cible à valider → validée). */
export const SETTINGS_GROUPS: readonly SettingsGroup[] = [
  {
    id: "general",
    label: "General",
    items: ["general", "chat", "reminders", "shortcuts", "library"],
  },
  {
    id: "ai",
    label: "AI",
    items: ["providers", "models", "routers", "speech", "ai"],
  },
  {
    id: "knowledge",
    label: "Knowledge",
    items: ["knowledge", "rag", "embedding", "vector-db", "chunking", "reranking", "search"],
  },
  { id: "skills", label: "Skills", items: ["skills"] },
  { id: "integrations", label: "Integrations", items: ["integrations"] },
  { id: "security", label: "Security", items: ["security"] },
  { id: "appearance", label: "Appearance", items: ["appearance"] },
  { id: "advanced", label: "Advanced", items: ["system", "capabilities", "advanced"] },
];

/** True si `value` est une section Settings connue (pilotage par hash URL). */
export function isSettingsSectionId(value: string): value is SettingsSectionId {
  return (SETTINGS_SECTION_IDS as readonly string[]).includes(value);
}
