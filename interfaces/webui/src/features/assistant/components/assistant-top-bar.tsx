"use client";

import type { SessionMetrics } from "@/types/assistant";

interface AssistantTopBarProps {
  metrics: SessionMetrics;
}

export function AssistantTopBar({ metrics }: AssistantTopBarProps) {
  const statusColor = metrics.agentStatus === "run" ? "text-green-400" : metrics.agentStatus === "error" ? "text-red-400" : "text-gray-400";

  return (
    <div className="flex items-center gap-4 px-4 py-2 border-b border-line-2 bg-background/80 text-xs">
      <div className="flex items-center gap-2">
        <span className={`${statusColor}`}>●</span>
        <span className="text-foreground font-medium">{metrics.agentName}</span>
      </div>
      <span className="text-muted-foreground/70">|</span>
      <span className="text-muted-foreground">🤖 {metrics.model}</span>
      <span className="text-muted-foreground/70">|</span>
      <span className="text-muted-foreground">🔌 {metrics.provider}</span>
      <span className="text-muted-foreground/70">|</span>
      <span className="text-muted-foreground">💰 ${metrics.cost.toFixed(4)}</span>
      <span className="text-muted-foreground/70">|</span>
      <span className="text-muted-foreground">⏱ {Math.floor(metrics.duration / 60)}m {metrics.duration % 60}s</span>
      <span className="text-muted-foreground/70">|</span>
      <span className="text-muted-foreground">🔤 {metrics.tokensUsed.toLocaleString()} / {metrics.tokensTotal.toLocaleString()}</span>
    </div>
  );
}