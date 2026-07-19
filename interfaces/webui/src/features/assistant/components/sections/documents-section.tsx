"use client";

import { useState } from "react";
import type { DocumentRef } from "@/types/assistant";

interface DocumentsSectionProps {
  documents: DocumentRef[];
}

export function DocumentsSection({ documents }: DocumentsSectionProps) {
  const [expanded, setExpanded] = useState(false);
  if (!documents || documents.length === 0) return null;

  return (
    <div className="mt-2 border border-green-500/20 rounded-lg overflow-hidden">
      <button className="flex items-center gap-2 w-full px-3 py-2 text-xs text-green-400 hover:bg-green-500/5 transition-colors" onClick={() => setExpanded(!expanded)}>
        <span className="transition-transform duration-200" style={{ transform: expanded ? "rotate(90deg)" : "rotate(0deg)" }}>▶</span>
        <span>📄 Documents ({documents.length})</span>
      </button>
      {expanded && (
        <div className="px-3 pb-2 space-y-1">
          {documents.map((doc, i) => (
            <div key={i} className="flex items-center justify-between text-xs text-gray-400">
              <span>{doc.name}</span>
              <span className="text-gray-500">{(doc.size / 1024).toFixed(0)} KB</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}