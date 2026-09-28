"use client";

/**
 * ETHAN WebUI — ChatSecondaryBar
 *
 * Barre secondaire compacte située au-dessus de la zone de conversation.
 * Remplace l'ancienne AssistantTopBar pleine largeur : le titre est affiché
 * en primier plan, puis model/provider/agent en indicateurs compacts à droite.
 * Volontairement sobre (bordure fine, pas de transparence ni overlay) pour
 * laisser la priorité au contenu conversationnel — inspiration Claude Code.
 *
 * Règle AGENTS.md : aucune logique métier — délègue aux hooks Core
 * (useActiveModel / useActiveAgent) et rend les sélecteurs existants.
 */

import * as React from "react";
import type { SessionMetrics } from "@/types/assistant";
import type { Agent } from "@/types";
import { ModelSelector } from "@/components/shared/model-selector";
import { AgentSelector } from "./agent-selector";
import { ProviderSelector } from "./provider-selector";
import { ProjectSelector } from "@/components/features/projects/project-selector";
import { cn } from "@/lib/utils";

export interface ChatSecondaryBarProps {
  title: string;
  metrics: SessionMetrics;
  /** Catalogue agent — données/état possédés par la page (useActiveAgent). */
  agents?: Agent[];
  agentsLoading?: boolean;
  agentsError?: string | null;
  selectedAgentId?: string | null;
  recentAgentIds?: string[];
  onSelectAgent?: (id: string | null) => void;
}

export function ChatSecondaryBar({
  title,
  metrics,
  agents,
  agentsLoading,
  agentsError,
  selectedAgentId,
  recentAgentIds,
  onSelectAgent,
}: ChatSecondaryBarProps) {
  return (
    <div
      className={cn(
        "flex shrink-0 items-center justify-between gap-3 border-b border-line-1/50 bg-background px-4 py-1.5",
      )}
    >
      {/* Titre conversation + statut agent */}
      <div className="flex min-w-0 items-center gap-2">
        <span className="truncate text-sm font-medium text-foreground">{title}</span>
        <span
          className={
            metrics.agentStatus === "run"
              ? "h-1.5 w-1.5 shrink-0 rounded-full bg-green-500"
              : "h-1.5 w-1.5 shrink-0 rounded-full bg-muted-foreground/40"
          }
          title={`Agent status: ${metrics.agentStatus}`}
        />
      </div>

      {/* Sélecteurs compacts : projet / agent / provider / model.
          Parité avec l'ancienne AssistantTopBar (qui rendait <ProjectSelector />) :
          le scope projet ne doit pas disparaître de la refonte. */}
      <div className="flex shrink-0 items-center gap-1.5">
        <ProjectSelector />
        {onSelectAgent && (
          <AgentSelector
            agents={agents ?? []}
            loading={agentsLoading}
            error={agentsError}
            selectedAgentId={selectedAgentId ?? null}
            recentAgentIds={recentAgentIds}
            onSelect={onSelectAgent}
          />
        )}
        <ProviderSelector />
        <ModelSelector variant="compact" />
      </div>
    </div>
  );
}
