"use client";

/**
 * ToolsHub — surface unique des OUTILS d'ETHAN.
 *
 * Deux onglets, une seule ressource Core derrière :
 *   - « Outils » : catalogue des outils (builtin / custom / découverts MCP) ;
 *   - « Serveurs MCP » : la source — les serveurs et leur synchronisation.
 *
 * CONSOLIDATION (30/09/2026) : `ToolsWorkspace` et `McpServersWorkspace`
 * interrogeaient les MÊMES endpoints Core (`/v1/tools/servers` et
 * `/v1/tools/servers/{id}` — cf. docs/design/2026-10-01-cartographie-webui-ux.md
 * §5.2). Deux écrans pour une seule ressource. La route /mcp reste valide en
 * lien profond : elle redirige ici avec ?view=mcp.
 *
 * L'infrastructure ne disparaît pas du tout : elle passe sous l'onglet qui
 * expose sa source de vérité. Aucune logique métier ici — les deux panneaux
 * transmettent des intentions au Core et affichent son état.
 */

import * as React from "react";
import { Wrench, Network } from "lucide-react";
import { ToolsWorkspace } from "@/components/features/tools/components/tools-workspace";
import { McpServersWorkspace } from "@/components/features/mcp/components/mcp-servers-workspace";

type ToolsTab = "tools" | "mcp";

const TABS: Array<{ id: ToolsTab; label: string; icon: React.ComponentType<{ size?: number | string; className?: string }> }> = [
  { id: "tools", label: "Outils", icon: Wrench },
  { id: "mcp", label: "Serveurs MCP", icon: Network },
];

/** `?view=mcp` : lien profond vers un onglet précis (ancienne route /mcp). */
function isToolsTab(value: string | null): value is ToolsTab {
  return value !== null && TABS.some((t) => t.id === value);
}

export function ToolsHub() {
  const [tab, setTab] = React.useState<ToolsTab>("tools");

  // Lien profond : query (`/tools?view=mcp`) ET ancien hash (`/tools#mcp`,
  // qui vivait dans ToolsWorkspace). Les deux ouvrent l'onglet MCP sans
  // détour par /mcp — évite un aller-retour de redirection.
  React.useEffect(() => {
    const view = new URLSearchParams(window.location.search).get("view");
    if (isToolsTab(view)) {
      setTab(view);
    } else if (window.location.hash === "#mcp") {
      setTab("mcp");
    }
  }, []);

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
        {tab === "mcp" && <McpServersWorkspace />}
      </div>
    </div>
  );
}