"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/stores/ui.store";
import { useAgentsStore } from "@/stores/agents.store";
import { useGoalsStore } from "@/stores/goals.store";
import { useMissionsStore } from "@/stores/missions.store";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getStatusColor } from "@/lib/utils";

export function Inspector() {
  const { inspectorOpen, closeInspector, inspector } = useUIStore();
  const { agents } = useAgentsStore();
  const { goals } = useGoalsStore();
  const { missions } = useMissionsStore();

  if (!inspectorOpen) return null;

  // Find the selected item
  let item: any = null;
  let itemType: string | null = null;

  if (inspector.type === "agent" && inspector.id) {
    item = agents.find((a) => a.id === inspector.id);
    itemType = "Agent";
  } else if (inspector.type === "goal" && inspector.id) {
    item = goals.find((g) => g.id === inspector.id);
    itemType = "Goal";
  } else if (inspector.type === "mission" && inspector.id) {
    item = missions.find((m) => m.id === inspector.id);
    itemType = "Mission";
  }

  return (
    <aside
      className={cn(
        "fixed right-0 top-0 z-40 h-screen w-80 border-l bg-background",
        "transform transition-transform duration-300",
        inspectorOpen ? "translate-x-0" : "translate-x-full"
      )}
    >
      <div className="flex h-full flex-col">
        {/* Header */}
        <div className="flex h-14 items-center justify-between border-b px-4">
          <h2 className="text-sm font-semibold">Inspector</h2>
          <button
            onClick={closeInspector}
            className="rounded-md p-1.5 hover:bg-accent/10 transition-colors"
            aria-label="Close inspector"
          >
            <span className="text-lg">✕</span>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {!item ? (
            <div className="text-center text-sm text-muted-foreground mt-8">
              <p>No item selected</p>
              <p className="text-xs mt-2">Right-click on an agent, goal, or mission to inspect it</p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Type badge */}
              <div>
                <Badge variant="info" className="text-xs">
                  {itemType}
                </Badge>
              </div>

              {/* Title */}
              <div>
                <h3 className="text-lg font-semibold">{item.name || item.title}</h3>
                {item.description && (
                  <p className="text-sm text-muted-foreground mt-1">{item.description}</p>
                )}
              </div>

              {/* Status */}
              {item.status && (
                <div>
                  <h4 className="text-xs font-medium text-muted-foreground mb-2">Status</h4>
                  <Badge variant={getStatusColor(item.status)}>{item.status}</Badge>
                </div>
              )}

              {/* Metadata */}
              <div>
                <h4 className="text-xs font-medium text-muted-foreground mb-2">Details</h4>
                <div className="space-y-2 text-sm">
                  {item.id && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">ID</span>
                      <span className="font-mono text-xs">{item.id}</span>
                    </div>
                  )}
                  {item.created_at && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Created</span>
                      <span>{new Date(item.created_at).toLocaleDateString()}</span>
                    </div>
                  )}
                  {item.updated_at && (
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Updated</span>
                      <span>{new Date(item.updated_at).toLocaleDateString()}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Agent-specific */}
              {itemType === "Agent" && (
                <>
                  <div>
                    <h4 className="text-xs font-medium text-muted-foreground mb-2">Capabilities</h4>
                    <div className="flex flex-wrap gap-1">
                      {item.capabilities?.map((cap: string) => (
                        <span key={cap} className="text-xs bg-muted px-2 py-1 rounded">
                          {cap}
                        </span>
                      ))}
                    </div>
                  </div>
                </>
              )}

              {/* Goal-specific */}
              {itemType === "Goal" && (
                <>
                  <div>
                    <h4 className="text-xs font-medium text-muted-foreground mb-2">Priority</h4>
                    <Badge variant={item.priority === "critical" ? "error" : item.priority === "high" ? "warning" : "default"}>
                      {item.priority}
                    </Badge>
                  </div>
                  <div>
                    <h4 className="text-xs font-medium text-muted-foreground mb-2">Tasks</h4>
                    <p className="text-sm">{item.tasks?.length || 0} tasks</p>
                  </div>
                </>
              )}

              {/* Mission-specific */}
              {itemType === "Mission" && (
                <>
                  <div>
                    <h4 className="text-xs font-medium text-muted-foreground mb-2">Steps</h4>
                    <p className="text-sm">{item.steps?.length || 0} steps</p>
                  </div>
                  <div>
                    <h4 className="text-xs font-medium text-muted-foreground mb-2">Progress</h4>
                    <div className="w-full bg-muted rounded-full h-2">
                      <div
                        className="bg-primary h-2 rounded-full"
                        style={{
                          width: `${((item.steps?.filter((s: any) => s.status === "completed").length || 0) / (item.steps?.length || 1)) * 100}%`,
                        }}
                      />
                    </div>
                  </div>
                </>
              )}

              {/* Actions */}
              <div>
                <h4 className="text-xs font-medium text-muted-foreground mb-2">Actions</h4>
                <div className="space-y-2">
                  <button className="w-full rounded-md border px-3 py-2 text-sm hover:bg-accent/10 transition-colors">
                    Edit
                  </button>
                  <button className="w-full rounded-md border px-3 py-2 text-sm hover:bg-accent/10 transition-colors text-destructive">
                    Delete
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
}