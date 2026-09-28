"use client";

/**
 * MissionWorkspaceNav — navigation interne du workspace Mission.
 *
 * Structure cible de l'espace (architecture initiale — le moteur
 * d'exécution visuel n8n/Zapier n'est PAS encore implémenté) :
 *
 *   Mission
 *   ├── Overview      (missions réelles du Core, aujourd'hui)
 *   ├── Workflows     (orchestrateur visuel — à venir)
 *   ├── Templates     (workflows pré-configurés — à venir)
 *   ├── Runs          (historique d'exécution réel)
 *   ├── Connections   (services connectés ETHAN — lecture seule ici)
 *   └── Settings      (préférences du workspace — à venir)
 *
 * AGENTS.md : pure présentation. Les données viennent du Core ; cette nav
 * ne possède ni état métier ni logique d'exécution.
 */

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Workflow,
  LayoutTemplate,
  History,
  Plug,
  Settings,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";

export interface MissionWorkspaceSection {
  href: string;
  label: string;
  icon: LucideIcon;
  /** Sections marquées `planned` affichent un indicateur « à venir ». */
  planned?: boolean;
}

/** Source de vérité des sections — réutilisée par les tests. */
export const MISSION_WORKSPACE_SECTIONS: MissionWorkspaceSection[] = [
  { href: "/missions", label: "Overview", icon: LayoutDashboard },
  { href: "/missions/workflows", label: "Workflows", icon: Workflow, planned: true },
  { href: "/missions/templates", label: "Templates", icon: LayoutTemplate, planned: true },
  { href: "/missions/runs", label: "Runs", icon: History },
  { href: "/missions/connections", label: "Connections", icon: Plug },
  { href: "/missions/settings", label: "Settings", icon: Settings, planned: true },
];

export function MissionWorkspaceNav() {
  const pathname = usePathname();

  const isActive = React.useCallback(
    (href: string) =>
      href === "/missions" ? pathname === "/missions" : pathname.startsWith(href),
    [pathname],
  );

  return (
    <nav
      aria-label="Navigation du workspace Mission"
      className="flex flex-wrap items-center gap-1 border-b border-line-1 px-4 pt-2"
    >
      {MISSION_WORKSPACE_SECTIONS.map(({ href, label, icon: Icon, planned }) => {
        const active = isActive(href);
        return (
          <Link
            key={href}
            href={href}
            aria-current={active ? "page" : undefined}
            className={cn(
              "group relative flex items-center gap-1.5 rounded-t-lg px-3 py-2 text-sm transition-colors",
              active
                ? "font-medium text-accent-400"
                : "text-foreground-tertiary hover:bg-elevated hover:text-foreground",
            )}
          >
            <Icon size={15} className="shrink-0" aria-hidden="true" />
            {label}
            {planned && (
              <span className="ml-0.5 rounded-full border border-line-2 px-1.5 py-px text-[9px] uppercase tracking-wide text-foreground-tertiary">
                soon
              </span>
            )}
            {active && (
              <span
                aria-hidden="true"
                className="absolute inset-x-2 -bottom-px h-0.5 rounded-full bg-accent-500"
              />
            )}
          </Link>
        );
      })}
    </nav>
  );
}