"use client";

import { useState } from "react";
import type { MemoryRef } from "@/types/assistant";

interface MemorySectionProps {
  entries: MemoryRef[];
}

export function MemorySection({ entries }: MemorySectionProps) {
  const [expanded, setExpanded] = useState(false);
  if (!entries || entries.length === 0) return null;

  return (
    <div className="mt-2 border border-warning rounded-lg overflow-hidden">
      <button className="flex items-center gap-2 w-full px-3 py-2 text-xs text-warning hover:bg-warning-soft transition-colors" onClick={() => setExpanded(!expanded)}>
        <span className="transition-transform duration-200" style={{ transform: expanded ? "rotate(90deg)" : "rotate(0deg)" }}>▶</span>
        <span>🧠 Mémoire ({entries.length})</span>
      </button>
      {expanded && (
        <div className="px-3 pb-2 space-y-1">
          {entries.map((entry, i) => (
            <div key={i} className="text-xs text-muted-foreground/70">
              <div className="flex items-center justify-between">
                <span className="text-foreground/70">{entry.key}</span>
                <span className="text-muted-foreground">{Math.round(entry.relevance * 100)}%</span>
              </div>
              <p className="text-muted-foreground truncate">{entry.snippet}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
