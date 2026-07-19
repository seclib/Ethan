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
    <div className="mt-2 border border-yellow-500/20 rounded-lg overflow-hidden">
      <button className="flex items-center gap-2 w-full px-3 py-2 text-xs text-yellow-400 hover:bg-yellow-500/5 transition-colors" onClick={() => setExpanded(!expanded)}>
        <span className="transition-transform duration-200" style={{ transform: expanded ? "rotate(90deg)" : "rotate(0deg)" }}>▶</span>
        <span>🧠 Mémoire ({entries.length})</span>
      </button>
      {expanded && (
        <div className="px-3 pb-2 space-y-1">
          {entries.map((entry, i) => (
            <div key={i} className="text-xs text-gray-400">
              <div className="flex items-center justify-between">
                <span className="text-gray-300">{entry.key}</span>
                <span className="text-gray-500">{Math.round(entry.relevance * 100)}%</span>
              </div>
              <p className="text-gray-500 truncate">{entry.snippet}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}