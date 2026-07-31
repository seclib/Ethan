"use client";

import { useState } from "react";
import type { ToolCall } from "@/types/assistant";

interface ToolsSectionProps {
  tools: ToolCall[];
}

export function ToolsSection({ tools }: ToolsSectionProps) {
  const [expanded, setExpanded] = useState(false);

  if (!tools || tools.length === 0) return null;

  return (
    <div className="mt-2 border border-accent-line/20 rounded-lg overflow-hidden">
      <button
        className="flex items-center gap-2 w-full px-3 py-2 text-xs text-accent hover:bg-accent/5 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <span className="transition-transform duration-200" style={{ transform: expanded ? "rotate(90deg)" : "rotate(0deg)" }}>▶</span>
        <span>🔧 Outils ({tools.length})</span>
      </button>
      {expanded && (
        <div className="px-3 pb-2 space-y-1">
          {tools.map((tool, i) => (
            <div key={i} className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <span className={tool.status === "success" ? "text-green-400" : "text-red-400"}>
                  {tool.status === "success" ? "✓" : "✗"}
                </span>
                <span className="text-foreground/70">{tool.name}</span>
              </div>
              <span className="text-muted-foreground">{(tool.durationMs / 1000).toFixed(1)}s</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
