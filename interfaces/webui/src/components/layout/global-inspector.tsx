"use client";

import * as React from "react";
import { useUIStore } from "@/core/store/ui.store";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

export function GlobalInspector() {
  const { inspectorOpen, inspector, closeInspector } = useUIStore();

  return (
    <>
      {/* Inspector Panel */}
      <aside
        className={cn(
          "fixed right-0 top-0 z-40 h-screen w-80 border-l bg-background shadow-2xl transition-transform duration-300",
          inspectorOpen ? "translate-x-0" : "translate-x-full"
        )}
      >
        <div className="flex h-14 items-center justify-between border-b px-4">
          <span className="font-semibold text-sm">
            {inspector.type ? inspector.type.charAt(0).toUpperCase() + inspector.type.slice(1) : "Inspector"}
          </span>
          <button
            onClick={closeInspector}
            className="rounded-md p-1.5 hover:bg-accent/10 text-muted-foreground hover:text-foreground transition-colors"
          >
            <X size={16} />
          </button>
        </div>
        
        <div className="p-4 overflow-y-auto h-[calc(100vh-3.5rem)] custom-scrollbar">
          {!inspector.id ? (
            <p className="text-sm text-foreground-tertiary">Select an item to inspect its details.</p>
          ) : (
            <div className="space-y-4">
              <div className="space-y-1">
                <span className="text-[10px] font-semibold text-foreground-tertiary uppercase">ID</span>
                <p className="text-sm font-mono break-all bg-elevated px-2 py-1 rounded">{inspector.id}</p>
              </div>
              <div className="space-y-1">
                <span className="text-[10px] font-semibold text-foreground-tertiary uppercase">Type</span>
                <p className="text-sm font-mono break-all bg-elevated px-2 py-1 rounded">{inspector.type}</p>
              </div>
              <p className="text-xs text-muted-foreground italic mt-4">
                Detailed contextual data will appear here based on the selected {inspector.type}.
              </p>
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
