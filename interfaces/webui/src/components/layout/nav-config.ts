"use client";

/**
 * nav-config — taxinomie de navigation UNIQUE du shell ETHAN (v5, Open-WebUI).
 *
 * Stratégie « conversation-centric » :
 *  - NAV_SECTIONS_PRIMARY : la sidebar principale, orientée conversations et
 *    navigation quotidienne (Assistants · Pilotage) — plus les sections
 *    techniques ou d'administration comme des listes d'icônes.
 *  - NAV_SECTIONS_ADMIN   : Administration (réellement fonctionnelle) — rendue
 *    en section compacte EN BAS de la sidebar déployée.
 *  - NAV_SECTIONS         : taxinomie COMPLÈTE (primary + system + préférences
 *    + admin), utilisée pour la résolution du label du header (AppHeader) et
 *    la palette de commandes (Ctrl+K). Les entrées techniques (Providers,
 *    Knowledge, Tools, Skills, MCP, Models…) vivent dans la navigation
 *    secondaire : la page Settings (sections + WorkspaceLink) et Ctrl+K.
 *
 * Règle anti-fantôme : seules des fonctionnalités réellement existantes sont
 * référencées — Projects, Knowledge, Skills, Tools, MCP sont servis par le
 * Core (core/projects, core/knowledge, core/skills, core/tools, core/mcp).
 * Règle AGENTS.md : aucun logic métier ici — labels, routes, icônes.
 */

import type { ComponentType } from "react";
import {
  Bot, Cpu, Database, Wrench, Sparkles, Network, Palette, ScrollText,
  Target, Calendar, StickyNote, Inbox, Telescope, BookOpen, Library,
    Layers, BrainCircuit, Settings, FolderTree, Shapes, FolderKanban,
  Activity, ShieldCheck, Gauge,
  GalleryVerticalEnd, UsersRound, Puzzle, BarChart3, ScanSearch, LifeBuoy,
} from "lucide-react";

/** Monitoring externe réel : Grafana (osiris-grafana, cf. port_registry.json). */
export const GRAFANA_URL = "http://localhost:3002";

export interface NavItem {
  href: string;
  label: string;
  icon: ComponentType<{ size?: number | string; className?: string }>;
  /** Lien externe (système d'observabilité) — s'ouvre dans un nouvel onglet. */
  external?: boolean;
}

export interface NavSection {
  id: string;
  label: string;
  /** Courte description du rôle de la section (tooltip sur l'en-tête). */
  description?: string;
  items: NavItem[];
  collapsible?: boolean;
  /**
   * Section repliée au premier rendu (sidebar) — l'utilisateur reste
   * conversation-first : l'administration technique ne s'ouvre pas d'office.
   * Le groupe se déplie automatiquement dès qu'on navigue vers une de ses
   * routes. Ignoré si `collapsible` est absent.
   */
  defaultCollapsed?: boolean;
}

/**
 * Navigation PRINCIPALE de la sidebar (conversation-centric).
 * Agents reste ici (sélecteur de personnalité, lié au chat) ; le reste des
 * capacités techniques est délégué à la navigation secondaire (Settings).
 */
export const NAV_SECTIONS_PRIMARY: NavSection[] = [
  {
    id: "assistants",
    label: "Assistants",
    description: "Vos agents ETHAN",
    collapsible: false,
    items: [
      { href: "/agents", label: "Agents", icon: Bot },
      { href: "/projects", label: "Projects", icon: FolderKanban },
    ],
  },
  {
    id: "operate",
    label: "Pilotage",
    description: "Missions, agenda et outils de suivi au quotidien",
    collapsible: true,
    items: [
      { href: "/missions", label: "Missions", icon: Target },
      { href: "/calendar", label: "Calendar", icon: Calendar },
      { href: "/notes", label: "Notes", icon: StickyNote },
      { href: "/inbox", label: "Inbox", icon: Inbox },
      { href: "/research", label: "Deep Research", icon: Telescope },
      { href: "/cookbook", label: "Cookbook", icon: BookOpen },
    ],
  },
];

/**
 * Administration — compacte, en bas de la sidebar déployée.
 * Réellement fonctionnelle (audit webui-ux-polish-audit : option A) :
 * Diagnostics = /health/detailed ; Logs/Monitoring = Grafana externe.
 */
export const NAV_SECTIONS_ADMIN: NavSection[] = [
  {
    id: "admin",
    label: "Administration",
    description: "Outils système et diagnostic — réservé à la supervision",
    collapsible: true,
    // Repliée au premier rendu : la sidebar reste « assistant-first ».
    defaultCollapsed: true,
        items: [
      { href: "/diagnostics", label: "Diagnostics", icon: Activity },
      { href: "/logs", label: "Logs", icon: ScrollText },
      { href: "/analytics", label: "Analytics", icon: BarChart3 },
      { href: "/groups", label: "Groups", icon: UsersRound },
      { href: "/plugins", label: "Plugins", icon: Puzzle },
      { href: "/connections", label: "Connexions", icon: LifeBuoy },
      { href: "/monitoring", label: "Monitoring", icon: Gauge },
      { href: "/security", label: "Security", icon: ShieldCheck },
    ],
  },
];

/**
 * Navigation SECONDAIRE (taxinomie pour la palette Ctrl+K et le titre du
 * header) — regroupée sur l'arborescence Settings cible pour qu'un même
 * vocabulaire soit utilisé partout (AI / Knowledge / Skills & Integrations /
 * Préférences). Les workspaces dédiés restent des routes à part entière ;
 * la sidebar quotidienne reste conversation-first (PRIMARY + ADMIN).
 */
export const NAV_SECTIONS_SECONDARY: NavSection[] = [
  {
    id: "ai",
    label: "AI",
    description: "Providers, catalogue de modèles et galerie d'assistants",
    collapsible: true,
    items: [
      { href: "/providers", label: "Providers", icon: Layers },
      { href: "/models", label: "Models", icon: Cpu },
      { href: "/gallery", label: "Gallery", icon: GalleryVerticalEnd },
    ],
  },
  {
    id: "knowledge",
    label: "Knowledge",
    description: "Documents, organisation et mémoire d'ETHAN",
    collapsible: true,
    items: [
      { href: "/knowledge", label: "Knowledge", icon: Database },
      // Library = vue unifiée (documents RAG, knowledge, collections, images)
      // servie par les APIs Core existantes ; aucun stockage parallèle.
      { href: "/library", label: "Library", icon: Library },
      { href: "/workspace", label: "Memory", icon: BrainCircuit },
      { href: "/folders", label: "Folders", icon: FolderTree },
      { href: "/domains", label: "Domains", icon: Shapes },
      { href: "/dedup", label: "Duplicates", icon: ScanSearch },
    ],
  },
  {
    id: "capabilities",
    label: "Skills & Integrations",
    description: "Skills, outils et serveurs MCP",
    collapsible: true,
    items: [
      { href: "/skills", label: "Skills", icon: Sparkles },
      { href: "/tools", label: "Tools", icon: Wrench },
      // Serveurs MCP : page dédiée (séparation capacités / infrastructure).
      { href: "/mcp", label: "MCP", icon: Network },
    ],
  },
  {
    id: "preferences",
    label: "Préférences",
    description: "Personnalisez le comportement et l'apparence de l'interface",
    collapsible: true,
    items: [
      { href: "/settings", label: "Settings", icon: Settings },
      // Interface = section Appearance réelle de /settings (thème, accents).
      { href: "/settings#appearance", label: "Interface", icon: Palette },
    ],
  },
];

/** Taxinomie complète (header + palette Ctrl+K). */
export const NAV_SECTIONS: NavSection[] = [
  ...NAV_SECTIONS_PRIMARY,
  ...NAV_SECTIONS_SECONDARY,
  ...NAV_SECTIONS_ADMIN,
];

/** Flat list utile à la palette de commandes / tests. */
export const NAV_ITEMS_FLAT: NavItem[] = NAV_SECTIONS.flatMap((s) => s.items);

/**
 * État initial du repli des groupes sidebar — dérivé de la taxinomie :
 * une section `collapsible` + `defaultCollapsed` démarre repliée
 * (`{ id: false }`). Les autres n'apparaissent pas : le composant les
 * considère ouvertes (valeur implicite `?? true`).
 */
export function initialCollapsedGroups(sections: NavSection[]): Record<string, boolean> {
  return Object.fromEntries(
    sections.filter((s) => s.collapsible && s.defaultCollapsed).map((s) => [s.id, false]),
  );
}

/**
 * Transition de repli/dépli d'un groupe. Le défaut implicite d'une section
 * non listée est « ouvert » : le PREMIER clic replie donc le groupe (l'ancien
 * `!groups[id]` laissait un premier clic inerte — undefined → true).
 */
export function toggleGroupState(
  groups: Record<string, boolean>,
  id: string,
): Record<string, boolean> {
  return { ...groups, [id]: !(groups[id] ?? true) };
}

/**
 * Séquences clavier « g puis x » — SOURCE UNIQUE de vérité.
 *
 * Consommée par :
 *  - `global-shortcuts.tsx` : résolution de la touche (handler) ET rendu de
 *    l'indicateur de séquence — aucune dérive possible entre les deux ;
 *  - `global-command-palette.tsx` : libellé annoncé (`formatGSequence`).
 *
 * Invariant (couvert par tests + garde-fou anti-fantôme) : chaque `route`
 * correspond à une route réelle de l'App Router.
 */
export const G_SEQUENCE_ROUTES: Record<string, { route: string; label: string }> = {
  a: { route: "/", label: "Assistant" },
  d: { route: "/workspace", label: "Workspace" },
  m: { route: "/missions", label: "Missions" },
  k: { route: "/knowledge", label: "Knowledge" },
  e: { route: "/agents", label: "Agents" },
  t: { route: "/tools", label: "Tools" },
  p: { route: "/providers", label: "Providers" },
  n: { route: "/models", label: "Models" },
  l: { route: "/library", label: "Library" },
  s: { route: "/settings", label: "Settings" },
};

/** Libellé affiché d'une séquence (ex. "l" → "G L"). */
export function formatGSequence(key: string): string {
  return `G ${key.toUpperCase()}`;
}
