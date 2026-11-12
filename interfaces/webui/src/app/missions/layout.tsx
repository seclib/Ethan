"use client";

/**
 * Layout du workspace Mission — /missions/*.
 *
 * Mission devient un espace applicatif dédié (plus un panneau par-dessus le
 * Chat) : en-tête propre + navigation interne par sections. Le Chat reste
 * totalement indépendant de ce workspace.
 *
 * AGENTS.md : pure interface. Toute capacité Mission (moteur, workflows,
 * runs) appartient à Core/Runtime — ce layout ne fait qu'orchestrer l'affichage.
 */

import * as React from "react";
import { Target } from "lucide-react";
import { MissionWorkspaceNav } from "@/components/features/missions/workspace/mission-workspace-nav";

export default function MissionsWorkspaceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-full min-h-0 flex-col">
      <header className="border-b border-line-1 bg-bg-2 px-6 pb-2 pt-5">
        <h1 className="flex items-center gap-2 text-xl font-bold tracking-tight text-foreground">
          <Target size={20} className="text-accent" aria-hidden="true" />
          Mission
        </h1>
        <p className="mt-0.5 text-xs text-muted-foreground">
          Workspace d&apos;orchestration — missions, workflows et services connectés.
        </p>
        <div className="mt-3">
          <MissionWorkspaceNav />
        </div>
      </header>
      <div className="min-h-0 flex-1 overflow-y-auto">{children}</div>
    </div>
  );
}