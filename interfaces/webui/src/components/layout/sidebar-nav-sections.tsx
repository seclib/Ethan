"use client";

/**
 * ETHAN WebUI — Sections de navigation de la sidebar.
 *
 * Composant client dédié : c'est le SEUL point du shell qui lit les
 * paramètres d'URL (`useSearchParams`). Cette lecture provoque un CSR bailout
 * de Next.js : toute route prérendue statiquement échoue au build si le hook
 * n'est pas placé sous une frontière `<Suspense>` (cf. `sidebar.tsx`, qui
 * enveloppe ce composant). `/404` et `/_not-found` étant des routes statiques
 * rendues avec le layout racine, le hook doit rester isolé ici — jamais dans
 * le shell lui-même.
 *
 * Le rendu est PARTAGÉ entre la version réelle et le fallback squelette :
 * les deux produisent exactement la même structure DOM (mêmes sections, même
 * état replié/déplié, mêmes hauteurs), seuls les icônes et les libellés
 * diffèrent. Le fallback ne provoque donc aucun saut de mise en page entre
 * le HTML prérendu et l'hydratation.
 */

import * as React from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { cn } from "@/lib/utils";
import { useI18n } from "@/lib/i18n";
import { toggleGroupState } from "./nav-config";
import type { NavItem, NavSection } from "./nav-config";
import { useExternalServiceHealth } from "./use-external-service";
import { ExternalLink, ChevronDown } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

/**
 * Détermine si un item de navigation est actif.
 *
 * Le chemin prime (correspondance exacte ou sous-route) ; les paramètres
 * d'URL restent acceptés pour permettre un affinage futur sans casser le
 * contrat de rendu.
 */
function isNavItemActive(
  item: NavItem,
  pathname: string | null,
  _searchParams: URLSearchParams | null,
): boolean {
  if (!pathname) return false;
  return pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href + "/"));
}

function ItemIcon({ icon }: { icon: NavItem["icon"] }) {
  const Icon = icon;
  return Icon ? <Icon size={15} className="sidebar-nav-icon" /> : <span className="w-4" />;
}

/**
 * Lien externe (Grafana) avec health-check léger : si le service est
 * injoignable, l'item est estompé, un ⚠ remplace l'icône externe et le
 * tooltip l'indique — au lieu de mener l'utilisateur à une page d'erreur
 * navigateur. Correctif audit UX (P2-2).
 */
function ExternalNavItem({ item }: { item: NavItem }) {
  const { t } = useI18n();
  const origin = React.useMemo(() => {
    try {
      return new URL(item.href).origin;
    } catch {
      return item.href;
    }
  }, [item.href]);
  const reachable = useExternalServiceHealth(origin);
  const down = reachable === false;

  return (
    <a
      href={item.href}
      target="_blank"
      rel="noreferrer"
      className={cn("sidebar-nav-item", down && "opacity-60")}
      title={down ? `${t(item.label)} — service injoignable (${origin})` : t(item.label)}
    >
      <ItemIcon icon={item.icon} />
      <span>{t(item.label)}</span>
      {down ? (
        <span className="ml-auto text-warning text-[11px]" aria-label="Service injoignable">
          ⚠
        </span>
      ) : (
        <ExternalLink size={11} className="ml-auto opacity-40" />
      )}
    </a>
  );
}

/** Icône d'un item : réelle, ou squelette de même gabarit en mode fallback. */
function NavItemIcon({ icon, skeleton }: { icon: NavItem["icon"]; skeleton: boolean }) {
  if (skeleton) {
    return <Skeleton variant="circle" className="h-[15px] w-[15px] shrink-0" />;
  }
  return <ItemIcon icon={icon} />;
}

/** Libellé d'un item : réel, ou squelette de même gabarit en mode fallback. */
function NavItemLabel({ label, skeleton }: { label: string; skeleton: boolean }) {
  if (skeleton) {
    return <Skeleton variant="text" className="h-3 w-24" />;
  }
  return <span>{label}</span>;
}

function NavigationSection({
  sections,
  pathname,
  searchParams,
  openGroups,
  setOpenGroups,
  skeleton,
}: {
  sections: NavSection[];
  pathname: string;
  searchParams: URLSearchParams | null;
  openGroups: Record<string, boolean>;
  setOpenGroups: React.Dispatch<React.SetStateAction<Record<string, boolean>>>;
  skeleton: boolean;
}) {
  const { t } = useI18n();
  return (
    <div className="sidebar-nav-group">
      {sections.map((section) => {
        const isOpen = openGroups[section.id] ?? true;
        if (!section.collapsible && section.items.length <= 1) {
          const item = section.items[0];
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "sidebar-nav-item",
                isNavItemActive(item, pathname, searchParams) && "active",
              )}
              title={t(item.label)}
              aria-hidden={skeleton ? true : undefined}
              tabIndex={skeleton ? -1 : undefined}
            >
              <NavItemIcon icon={item.icon} skeleton={skeleton} />
              <NavItemLabel label={t(item.label)} skeleton={skeleton} />
            </Link>
          );
        }
        return (
          <div key={section.id}>
            <button
              className={cn(
                "sidebar-nav-section-header",
                section.items.some((it) => isNavItemActive(it, pathname, searchParams)) &&
                  "active",
              )}
              onClick={() => setOpenGroups((g) => toggleGroupState(g, section.id))}
              aria-expanded={isOpen}
              title={section.description ? t(section.description) : t(section.label)}
              aria-hidden={skeleton ? true : undefined}
              tabIndex={skeleton ? -1 : undefined}
            >
              <span className="sidebar-nav-item-outer">
                {skeleton ? (
                  <Skeleton variant="text" className="h-3 w-28" />
                ) : (
                  <span>{t(section.label)}</span>
                )}
              </span>
              <ChevronDown
                size={14}
                className={cn("sidebar-nav-chevron", !isOpen && "rotate-[-90deg]")}
              />
            </button>
            {isOpen && (
              <div className="sidebar-nav-sub">
                {section.items.map((item) =>
                  item.external ? (
                    <ExternalNavItem key={item.href} item={item} />
                  ) : (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={cn(
                        "sidebar-nav-item",
                        isNavItemActive(item, pathname, searchParams) && "active",
                      )}
                      aria-hidden={skeleton ? true : undefined}
                      tabIndex={skeleton ? -1 : undefined}
                    >
                      <NavItemIcon icon={item.icon} skeleton={skeleton} />
                      <NavItemLabel label={t(item.label)} skeleton={skeleton} />
                    </Link>
                  ),
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

/**
 * Sections de navigation — wrapper client qui lit les paramètres d'URL.
 *
 * Point d'entrée public du module : `AppSidebar` l'enveloppe dans une
 * frontière `<Suspense>` pour que le CSR bailout de `useSearchParams()`
 * reste confiné à ce sous-arbre (les pages statiques restent prérendues).
 */
export function SidebarNavSections({
  sections,
  pathname,
  openGroups,
  setOpenGroups,
}: {
  sections: NavSection[];
  pathname: string;
  openGroups: Record<string, boolean>;
  setOpenGroups: React.Dispatch<React.SetStateAction<Record<string, boolean>>>;
}) {
  const searchParams = useSearchParams();
  return (
    <NavigationSection
      sections={sections}
      pathname={pathname}
      searchParams={searchParams}
      openGroups={openGroups}
      setOpenGroups={setOpenGroups}
      skeleton={false}
    />
  );
}

/**
 * Fallback de la frontière Suspense — squelette de navigation.
 *
 * Reprend la structure exacte des sections (mêmes en-têtes, mêmes items,
 * même état replié/déplié) pour que la transition fallback → contenu réel
 * se fasse sans saut de mise en page. Les liens sont neutralisés
 * (`aria-hidden` + `tabIndex=-1`) : le squelette n'est pas navigable.
 */
export function SidebarNavSectionsFallback({
  sections,
  pathname,
  openGroups,
  setOpenGroups,
}: {
  sections: NavSection[];
  pathname: string;
  openGroups: Record<string, boolean>;
  setOpenGroups: React.Dispatch<React.SetStateAction<Record<string, boolean>>>;
}) {
  return (
    <NavigationSection
      sections={sections}
      pathname={pathname}
      searchParams={null}
      openGroups={openGroups}
      setOpenGroups={setOpenGroups}
      skeleton
    />
  );
}
