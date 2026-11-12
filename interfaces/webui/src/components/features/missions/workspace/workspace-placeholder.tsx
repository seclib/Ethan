"use client";

/**
 * WorkspacePlaceholder — état honnête « section planifiée ».
 *
 * Règle du projet : ne JAMAIS simuler des données ou un moteur d'exécution
 * fictif. Ce composant affiche explicitement ce qui est prévu (roadmap
 * d'architecture) et ce qui ne l'est pas encore, sans fake data.
 */

import * as React from "react";
import { Construction } from "lucide-react";

export interface WorkspacePlaceholderProps {
  title: string;
  description: string;
  /** Capacités prévues — affichées comme roadmap, jamais comme fonctionnalités actives. */
  planned: string[];
}

export function WorkspacePlaceholder({ title, description, planned }: WorkspacePlaceholderProps) {
  return (
    <div className="mx-auto max-w-3xl space-y-6 p-6">
      <div className="rounded-2xl border border-line-1 bg-bg-2 p-6">
        <div className="flex items-start gap-3">
          <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-accent/10 text-accent-400">
            <Construction size={18} aria-hidden="true" />
          </span>
          <div>
            <h2 className="text-base font-semibold text-foreground">{title}</h2>
            <p className="mt-1 text-sm text-muted-foreground">{description}</p>
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-line-1 bg-bg-2 p-6">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-foreground-secondary">
          Architecture prévue
        </h3>
        <ul className="mt-3 space-y-2">
          {planned.map((item) => (
            <li key={item} className="flex items-start gap-2 text-sm text-muted-foreground">
              <span
                aria-hidden="true"
                className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-line-3"
              />
              {item}
            </li>
          ))}
        </ul>
        <p className="mt-4 border-t border-line-1 pt-3 text-xs text-foreground-tertiary">
          Cette section n&apos;expose volontairement aucune donnée ni contrôle fictif :
          elle sera activée lorsque la capacité correspondante existera dans ETHAN
          Core/Runtime.
        </p>
      </div>
    </div>
  );
}