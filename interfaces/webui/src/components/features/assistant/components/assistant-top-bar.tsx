"use client";

import * as React from "react";
import type { SessionMetrics } from "@/types/assistant";
import { ModelSelector } from "@/components/shared/model-selector";

interface AssistantTopBarProps {
  title: string;
  metrics: SessionMetrics;
}

/**
 * Header minimaliste pour le mode chat.
 * - Gauche : titre de la conversation courante
 * - Droite : sélecteur de modèle compact
 */
export function AssistantTopBar({ title, metrics }: AssistantTopBarProps) {
  return (
    <div className="flex shrink-0 items-center justify-between gap-4 border-b border-line-1/60 bg-background/60 px-4 py-2 backdrop-blur supports-[backdrop-filter]:bg-background/40">
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
        <ModelSelector variant="compact" />
      </div>
    </div>
  );
}