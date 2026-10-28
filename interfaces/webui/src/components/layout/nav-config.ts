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
  Bot, Cpu, Database, Wrench, Sparkles, ScrollText,
  Target, Calendar, StickyNote, Inbox, Telescope, BookOpen,
  Layers, Settings, FolderTree, Shapes, FolderKanban,
  Activity, ShieldCheck, Gauge, Globe,
  UsersRound, BarChart3, ScanSearch, LifeBuoy,
  Workflow, FlaskConical, MessagesSquare, SquareTerminal as TerminalIcon,
  Puzzle,
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
    label: "navigation.assistants",
    description: "Vos agents ETHAN",
    collapsible: false,
    items: [
      { href: "/agents", label: "navigation.agents", icon: Bot },
      { href: "/projects", label: "navigation.projects", icon: FolderKanban },
    ],
  },
  {
    id: "operate",
    label: "navigation.pilotage",
    description: "Missions, agenda et outils de suivi au quotidien",
    collapsible: true,
    items: [
      { href: "/missions", label: "navigation.missions", icon: Target },
      { href: "/calendar", label: "navigation.calendar", icon: Calendar },
      { href: "/notes", label: "navigation.notes", icon: StickyNote },
      { href: "/inbox", label: "navigation.inbox", icon: Inbox },
      { href: "/research", label: "navigation.research", icon: Telescope },
      // Automations = règles réellement servies par le Core (/v1/automations).
      { href: "/automations", label: "navigation.automations", icon: Workflow },
      { href: "/cookbook", label: "navigation.cookbook", icon: BookOpen },
    ],
  },
  {
    id: "tools",
    label: "navigation.tools",
    description: "Outils et services applicatifs pilotables",
    collapsible: true,
    items: [
      { href: "/odin", label: "navigation.odin", icon: Globe },
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
    label: "navigation.administration",
    description: "Outils système et diagnostic — réservé à la supervision",
    collapsible: true,
    // Repliée au premier rendu : la sidebar reste « assistant-first ».
    defaultCollapsed: true,
        items: [
      { href: "/diagnostics", label: "navigation.diagnostics", icon: Activity },
      { href: "/terminal", label: "navigation.terminal", icon: TerminalIcon },
      { href: "/logs", label: "navigation.logs", icon: ScrollText },
      { href: "/analytics", label: "navigation.analytics", icon: BarChart3 },
      { href: "/groups", label: "navigation.groups", icon: UsersRound },
      { href: "/connections", label: "navigation.connections", icon: LifeBuoy },
      { href: "/monitoring", label: "navigation.monitoring", icon: Gauge },
      { href: "/security", label: "navigation.security", icon: ShieldCheck },
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
    label: "navigation.ai",
    description: "Providers et catalogue de modèles ETHAN",
    collapsible: true,
    items: [
      { href: "/providers", label: "navigation.providers", icon: Layers },
      { href: "/models", label: "navigation.models", icon: Cpu },
      // Pas d'entrée « Gallery » : la page n'existe qu'en état vide honnête
      // (Core n'expose aucun /v1/gallery). Une entrée de menu annonce une
      // capacité réelle — voir R5, docs/design/2026-09-30-ux-refonte-cartographie.md.
    ],
  },
  {
    id: "knowledge",
    label: "navigation.knowledge",
    description: "Documents, organisation et mémoire d'ETHAN",
    collapsible: true,
    items: [
      // Gestion directe des dossiers de connaissances (interface principale).
      // Les vues RAG Collections, Knowledge, Library et Web Import sont
      // accessibles depuis l'onglet correspondant de /knowledge (hub).
      { href: "/folders", label: "navigation.folders", icon: FolderTree },
      { href: "/domains", label: "navigation.domains", icon: Shapes },
      { href: "/dedup", label: "navigation.dedup", icon: ScanSearch },
    ],
  },
  {
    id: "capabilities",
    label: "Skills & Integrations",
    description: "Skills, outils et serveurs MCP",
    collapsible: true,
    items: [
      { href: "/skills", label: "navigation.skills", icon: Sparkles },
      // Skills Lab = sandbox Docker du Core (/v1/skills/lab/test|results).
      { href: "/skills/lab", label: "navigation.skills_lab", icon: FlaskConical },
      { href: "/tools", label: "navigation.tools", icon: Wrench },
      // Serveurs MCP = onglet de /tools (ToolsHub), plus une page : la
      // ressource Core `/v1/tools/servers` est unique — un seul menu.
      { href: "/prompts", label: "navigation.prompts", icon: ScrollText },
    ],
  },
  {
    id: "plugins",
    label: "navigation.plugins",
    description: "Gestionnaire de plugins — catalogue, état, installation",
    collapsible: true,
    items: [
      { href: "/plugins", label: "navigation.plugins", icon: Puzzle },
    ],
  },
  {
    id: "collaboration",
    label: "Collaboration",
    description: "Canaux de discussion persistés par ETHAN Core",
    collapsible: true,
    items: [
      // Channels = canaux + messages du ChannelStore Core (/v1/channels).
      { href: "/channels", label: "navigation.channels", icon: MessagesSquare },
    ],
  },
  {
    id: "preferences",
    label: "navigation.settings",
    description: "Personnalisez le comportement et l'apparence de l'interface",
    collapsible: true,
    items: [
      { href: "/settings", label: "navigation.settings", icon: Settings },
      // Pas d'entrée « Interface » en doublon : /settings#appearance EST la
      // même page que Settings (section Appearance). Une entrée de menu =
      // une destination ; le hash reste supporté comme lien profond.
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

