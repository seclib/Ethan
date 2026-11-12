"use client";

/**
 * DAËNA — mise en page interne (route layout).
 *
 * Rail vertical dédié avec les huit sections ; le contenu de la section est
 * rendu dans <main>. La vérité métier reste dans ETHAN Core : ce layout ne
 * contient que de la navigation d'interface.
 */

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { MotionConfig, motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { DURATION, EASING } from "@/lib/motion";
import {
  LayoutDashboard,
  BookOpen,
  GitBranch,
  Layout,
  Clock,
  Search,
  Boxes,
  Sparkles,
  ChevronRight,
} from "lucide-react";

export const OBSERVATORY_NAV = [
  { href: "/workspaces/observatory", label: "Overview", description: "Vue générale de la mémoire", icon: LayoutDashboard },
  { href: "/workspaces/observatory/vault", label: "Vault", description: "Explorateur et éditeur Markdown", icon: BookOpen },
  { href: "/workspaces/observatory/graph", label: "Graph", description: "Graphe de connaissances", icon: GitBranch },
  { href: "/workspaces/observatory/canvas", label: "Canvas", description: "Espace de travail visuel", icon: Layout },
  { href: "/workspaces/observatory/timeline", label: "Timeline", description: "Chronologie technique", icon: Clock },
  { href: "/workspaces/observatory/search", label: "Search", description: "Recherche unifiée", icon: Search },
  { href: "/workspaces/observatory/engineering", label: "Engineering", description: "ADR · ESR · composants · incidents", icon: Boxes },
  { href: "/workspaces/observatory/ai-insights", label: "AI Insights", description: "Synthèses et rapports d'agents", icon: Sparkles },
] as const;

export default function DAËNALayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <MotionConfig reducedMotion="user">
      <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
        <div className="flex min-h-0 flex-1 flex-col lg:flex-row">
          {/* Rail de navigation interne */}
          <nav
            aria-label="DAËNA"
            className="flex shrink-0 gap-1 overflow-x-auto border-b border-line-1 bg-bg-1 p-2 lg:w-56 lg:flex-col lg:overflow-visible lg:border-b-0 lg:border-r lg:p-2.5"
          >
          <div className="hidden px-2 pb-2 pt-1 lg:block">
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-foreground-tertiary">
              ETHAN
            </p>
            <h1 className="mt-0.5 text-base font-bold tracking-tight text-foreground">
              DAËNA
            </h1>
          </div>
            <div className="hidden px-2 pb-2 pt-1 lg:block">
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-foreground-tertiary">
                ETHAN
              </p>
              <h1 className="mt-0.5 text-base font-bold tracking-tight text-foreground">
                DAËNA
              </h1>
            </div>
            {OBSERVATORY_NAV.map(({ href, label, icon: Icon }) => {
              const isActive =
                pathname === href ||
                (href !== "/workspaces/observatory" && (pathname ?? "").startsWith(href + "/"));
              return (
                <Link
                  key={href}
                  href={href}
                  aria-current={isActive ? "page" : undefined}
                  title={OBSERVATORY_NAV.find((n) => n.href === href)?.description}
                  className={cn(
                    "group relative flex min-w-[3.25rem] flex-col items-center gap-1 rounded-lg px-2 py-1.5 text-[10px] font-medium transition-colors",
                    "lg:min-w-0 lg:flex-row lg:gap-2.5 lg:px-2.5 lg:py-2 lg:text-[13px] lg:font-normal",
                    isActive
                      ? "text-primary"
                      : "text-foreground-secondary hover:bg-bg-2 hover:text-foreground",
                  )}
                >
                  {/* Indicateur partagé : glisse d'une section à l'autre au lieu
                      de clignoter. Décoratif, donc masqué aux technologies
                      d'assistance. */}
                  {isActive && (
                    <motion.span
                      layoutId="daena-nav-active"
                      aria-hidden
                      className="absolute inset-0 rounded-lg bg-primary/10"
                      transition={{ duration: DURATION.fast, ease: EASING.standard }}
                    />
                  )}
                  <Icon className={cn("relative z-10 h-4 w-4 shrink-0", isActive ? "text-primary" : "text-foreground-tertiary group-hover:text-foreground")} />
                  <span className="relative z-10 truncate">{label}</span>
                  <ChevronRight
                    className={cn(
                      "relative z-10 ml-auto hidden h-3.5 w-3.5 lg:block",
                      isActive ? "text-primary opacity-100" : "opacity-0 group-hover:opacity-40",
                    )}
                  />
                </Link>
              );
            })}
            <div className="mt-auto hidden px-2 pb-1 pt-4 lg:block">
              <p className="text-[10px] leading-relaxed text-foreground-tertiary">
                Mémoire d&apos;ingénierie ETHAN — sources immutables, vues dérivées reconstruisibles.
              </p>
            </div>
          </nav>

          {/* Contenu de la section */}
          <main className="min-h-0 min-w-0 flex-1 overflow-y-auto">{children}</main>
        </div>
      </div>
    </MotionConfig>
  );
}
