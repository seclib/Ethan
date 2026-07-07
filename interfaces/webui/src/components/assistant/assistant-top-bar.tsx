"use client";

import type { SessionMetrics } from "@/types/assistant";

interface AssistantTopBarProps {
  metrics: SessionMetrics;
}

export function AssistantTopBar({ metrics }: AssistantTopBarProps) {
  const statusColor = metrics.agentStatus === "run" ? "text-green-400" : metrics.agentStatus === "error" ? "text-red-400" : "text-gray-400";

  return (
    <div className="flex items-center gap-4 px-4 py-2 border-b border-gray-800 bg-gray-900/50 text-xs">
      <div className="flex items-center gap-2">
        <span className={`${statusColor}`}>●</span>
        <span className="text-gray-300 font-medium">{metrics.agentName}</span>
      </div>
      <span className="text-gray-600">|</span>
      <span className="text-gray-400">🤖 {metrics.model}</span>
      <span className="text-gray-600">|</span>
      <span className="text-gray-400">🔌 {metrics.provider}</span>
      <span className="text-gray-600">|</span>
      <span className="text-gray-400">💰 ${metrics.cost.toFixed(4)}</span>
      <span className="text-gray-600">|</span>
      <span className="text-gray-400">⏱ {Math.floor(metrics.duration / 60)}m {metrics.duration % 60}s</span>
      <span className="text-gray-600">|</span>
      <span className="text-gray-400">🔤 {metrics.tokensUsed.toLocaleString()} / {metrics.tokensTotal.toLocaleString()}</span>
    </div>
  );
}