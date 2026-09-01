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
 * référencées — aucun « New Project » (pas de module projets dans ETHAN).
 * Règle AGENTS.md : aucun logic métier ici — labels, routes, icônes.
 */

import type { ComponentType } from "react";
import {
  Bot, Cpu, Database, Wrench, Sparkles, Network, Palette, ScrollText,
  Target, Calendar, StickyNote, Inbox, Telescope, BookOpen,
  Layers, BrainCircuit, Settings,
    Activity, ShieldCheck, Gauge,
  GalleryVerticalEnd, UsersRound, Puzzle, BarChart3,
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
    items: [
      { href: "/diagnostics", label: "Diagnostics", icon: Activity },
      { href: "/analytics", label: "Analytics", icon: BarChart3 },
      { href: "/groups", label: "Groups", icon: UsersRound },
      { href: "/plugins", label: "Plugins", icon: Puzzle },
      { href: `${GRAFANA_URL}/explore`, label: "Logs", icon: ScrollText, external: true },
      { href: GRAFANA_URL, label: "Monitoring", icon: Gauge, external: true },
      { href: "/security", label: "Security", icon: ShieldCheck },
    ],
  },
];

/**
 * Navigation SECONDAIRE (accès via Settings + palette Ctrl+K + routes) —
 * les entrées techniques de l'écosystème ETHAN (cf. page Settings sections).
 */
export const NAV_SECTIONS_SECONDARY: NavSection[] = [
  {
    id: "system",
    label: "Système",
    description: "Connexions aux fournisseurs de modèles et mémoire d'ETHAN",
    collapsible: true,
    items: [
      { href: "/providers", label: "Providers", icon: Layers },
      { href: "/workspace", label: "Memory", icon: BrainCircuit },
            { href: "/gallery", label: "Gallery", icon: GalleryVerticalEnd },
    ],
  },
  {
    id: "models",
    label: "Modèles",
    description: "Catalogue de modèles découverts et personnalisés",
    collapsible: true,
    items: [
      { href: "/models", label: "Models", icon: Cpu },
      { href: "/knowledge", label: "Knowledge", icon: Database },
      { href: "/skills", label: "Skills", icon: Sparkles },
      { href: "/tools", label: "Tools", icon: Wrench },
      // Onglet MCP réel de la page Tools (hash URL supporté).
      { href: "/tools#mcp", label: "MCP", icon: Network },
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
