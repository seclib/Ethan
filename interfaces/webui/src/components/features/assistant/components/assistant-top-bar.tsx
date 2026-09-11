"use client";

import * as React from "react";
import type { SessionMetrics } from "@/types/assistant";
import { ModelSelector } from "@/components/shared/model-selector";
import { AgentSelector } from "./agent-selector";
import { ProviderSelector } from "./provider-selector";
import { ProjectSelector } from "@/components/features/projects/project-selector";
import type { Agent } from "@/types";

interface AssistantTopBarProps {
  title: string;
  metrics: SessionMetrics;
  /** Sélecteur d'agent — données et état possédés par la page (useActiveAgent). */
  agents?: Agent[];
  agentsLoading?: boolean;
  agentsError?: string | null;
  selectedAgentId?: string | null;
  recentAgentIds?: string[];
  onSelectAgent?: (id: string | null) => void;
  /**
   * Ouverture contrôlée du sélecteur de modèle (optionnelle) — pilotée par la
   * ChatContextBar : cliquer « Modèle » dans la barre de contexte déroule ce
   * menu sans dupliquer de popover.
   */
  modelSelectorOpen?: boolean;
  onModelSelectorOpenChange?: (open: boolean) => void;
}

/**
 * Header du mode chat.
 * - Gauche : titre de la conversation courante + statut agent
 * - Droite : [Agent ▼] [Model ▼] [Provider ▼] — changement d'agent/de LLM/
 *   de provider = interactions de premier niveau, sans quitter le chat.
 * (Le mode Act|Plan|Agent vit dans le composer — jamais dupliqué ici.)
 */
export function AssistantTopBar({
  title,
  metrics,
  agents,
  agentsLoading,
  agentsError,
  selectedAgentId,
  recentAgentIds,
  onSelectAgent,
  modelSelectorOpen,
  onModelSelectorOpenChange,
}: AssistantTopBarProps) {
  return (
    <div className="flex shrink-0 items-center justify-between gap-4 border-b border-line-1/60 bg-background px-4 py-2">
      <div className="flex min-w-0 items-center gap-3">
        <span className="truncate text-sm font-semibold text-foreground">
          {title}
        </span>
        <span
          className={
            metrics.agentStatus === "run"
              ? "h-2 w-2 shrink-0 rounded-full bg-green-500"
              : "h-2 w-2 shrink-0 rounded-full bg-muted-foreground/40"
          }
          title={`Agent status: ${metrics.agentStatus}`}
        />
      </div>
      <div className="flex shrink-0 items-center gap-2">
        {onSelectAgent && (
          <>
            <ProjectSelector />
            <AgentSelector
              agents={agents ?? []}
              loading={agentsLoading}
              error={agentsError}
              selectedAgentId={selectedAgentId ?? null}
              recentAgentIds={recentAgentIds}
              onSelect={onSelectAgent}
            />
          </>
        )}
        <ModelSelector
          variant="compact"
          open={modelSelectorOpen}
          onOpenChange={onModelSelectorOpenChange}
        />
        <ProviderSelector />
      </div>
    </div>
  );
}
