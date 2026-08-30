import type * as React from "react";

interface PageHeaderProps {
  title: string;
  description?: string;
  icon?: React.ReactNode;
  /** Badge compteur à droite du titre (ex: nombre d'éléments). */
  count?: number;
  /** Contenu à droite (actions principales : boutons, filtres…). */
  actions?: React.ReactNode;
}

/**
 * Header de page Open-WebUI-like : titre + description + compteur + actions.
 * Utilisé par les workspaces (Agents, Models, Skills, Providers…) pour
 * uniformiser la structure « Header / Description / Search / Actions ».
 */
export function PageHeader({ title, description, icon, count, actions }: PageHeaderProps) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line-1 px-4 py-3">
      <div className="flex min-w-0 items-center gap-3">
        {icon && <span className="shrink-0 text-foreground-tertiary">{icon}</span>}
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h1 className="truncate text-lg font-semibold text-foreground">{title}</h1>
            {typeof count === "number" && (
              <span className="shrink-0 rounded-full bg-bg-3 px-2 py-0.5 text-xs font-medium text-foreground-tertiary">
                {count}
              </span>
            )}
          </div>
          {description && (
            <p className="truncate text-xs text-foreground-tertiary">{description}</p>
          )}
        </div>
      </div>
      {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
    </div>
  );
}