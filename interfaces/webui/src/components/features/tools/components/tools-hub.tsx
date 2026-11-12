"use client";

/**
 * ToolsHub — surface unique des OUTILS d'ETHAN.
 *
 * Deux onglets, une seule ressource Core derrière :
 *   - « Outils » : catalogue des outils (builtin / custom / découverts MCP) ;
 *   - « Applications » : catalogue des applications pilotables.
 *
 * MCP : la gestion des SERVEURS MCP (infrastructure) vit dans la section
 * Workspaces — route dédiée `/workspaces/mcp`, réutilisant `McpServersWorkspace`
 * (même ressource Core `/v1/tools/servers`, même registre `ToolServerManager`).
 * `/tools` n'expose donc plus d'onglet MCP : l'ancien onglet « Serveurs MCP »
 * et le lien profond `?view=mcp` ont été retirés au profit de la route Workspaces
 * (`/tools?view=mcp` redirige vers `/workspaces/mcp`).
 *
 * L'infrastructure ne disparaît pas du tout : elle est déléguée à la surface
 * Workspaces dédiée. Aucune logique métier ici — les panneaux transmettent des
 * intentions au Core et affichent son état.
 */

import * as React from "react";
import { Wrench, Layers } from "lucide-react";
import { ToolsWorkspace } from "@/components/features/tools/components/tools-workspace";
import { ApplicationCatalog } from "@/components/features/tools/components/application-catalog";

type ToolsTab = "tools" | "applications";

const TABS: Array<{ id: ToolsTab; label: string; icon: React.ComponentType<{ size?: number | string; className?: string }> }> = [
  { id: "tools", label: "Outils", icon: Wrench },
  { id: "applications", label: "Applications", icon: Layers },
];

export function ToolsHub() {
  const [tab, setTab] = React.useState<ToolsTab>("tools");

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="mb-2 flex items-center gap-1 border-b border-line-1 pb-2">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            type="button"
            aria-current={tab === id ? "page" : undefined}
            className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm transition-colors ${
              tab === id
                ? "bg-primary/10 text-primary font-medium"
                : "text-foreground-secondary hover:bg-muted"
            }`}
            onClick={() => setTab(id)}
          >
            <Icon size={14} className={tab === id ? "text-primary" : "text-muted-foreground"} />
            {label}
          </button>
        ))}
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto">
        {tab === "tools" && <ToolsWorkspace />}
        {tab === "applications" && <ApplicationCatalog />}
      </div>
    </div>
  );
}
