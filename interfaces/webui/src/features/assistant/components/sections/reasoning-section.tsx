"use client";

import { useState } from "react";

interface ReasoningSectionProps {
  steps: string[];
}

export function ReasoningSection({ steps }: ReasoningSectionProps) {
  const [expanded, setExpanded] = useState(false);

  if (!steps || steps.length === 0) return null;

  return (
    <div className="mt-2 border border-purple-500/20 rounded-lg overflow-hidden">
      <button
        className="flex items-center gap-2 w-full px-3 py-2 text-xs text-purple-400 hover:bg-purple-500/5 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <span className="transition-transform duration-200" style={{ transform: expanded ? "rotate(90deg)" : "rotate(0deg)" }}>
          ▶
        </span>
        <span>Raisonnement ({steps.length} étapes)</span>
      </button>
      {expanded && (
        <div className="px-3 pb-2 space-y-1">
          {steps.map((step, i) => (
            <div key={i} className="flex items-start gap-2 text-xs text-gray-400">
              <span className="text-purple-400 mt-0.5">{i + 1}.</span>
              <span>{step}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}