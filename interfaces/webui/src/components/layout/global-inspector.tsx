"use client";

import * as React from "react";
import { useUIStore } from "@/store/ui.store";
import { X, Play, Pause, Square, FileJson, Activity } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

import { useMission } from "@/components/features/missions/hooks/use-missions";
import { useAgent, useUpdateAgent } from "@/components/features/agents/hooks/use-agents";
import { useGoal } from "@/components/features/goals/hooks/use-goals";
import { Spinner } from "@/components/ui/spinner";

function EntityDetails({ type, id }: { type: string; id: string }) {
  const { mission, isLoading: missionLoading } = useMission(type === "mission" ? id : null);
  const { agent, isLoading: agentLoading } = useAgent(type === "agent" ? id : null);
  const { goal, isLoading: goalLoading } = useGoal(type === "goal" ? id : null);
  const updateAgent = useUpdateAgent();
  const addToast = useUIStore((s) => s.addToast);

  const isLoading = missionLoading || agentLoading || goalLoading;
  const isAgent = type === "agent";

  if (isLoading) {
    return <div className="flex justify-center p-8"><Spinner /></div>;
  }

  const data = mission || agent || goal;

  if (!data) {
    return <p className="text-sm text-destructive">Entity not found.</p>;
  }

  const controlAgent = async (status: "running" | "paused" | "stopped") => {
    const result = await updateAgent.mutate(id, { status });
    if (result.error) {
      addToast({ type: "error", message: result.error });
    } else {
      addToast({ type: "success", message: `Agent ${status}` });
    }
  };

  return (
    <div className="space-y-6">
      {/* Overview */}
      <div>
        <h3 className="text-lg font-semibold mb-1">{(data as any).name || (data as any).title || "Unnamed Entity"}</h3>
        <p className="text-sm text-muted-foreground">{data.description || "No description provided."}</p>
        
        <div className="flex gap-2 mt-3">
          <Badge variant={data.status === "running" || data.status === "active" ? "success" : "default"}>
            {data.status || "unknown"}
          </Badge>
          <Badge variant="default" className="font-mono text-[10px] bg-transparent border-border text-foreground">{id.split("-")[0]}</Badge>
        </div>
      </div>

      <Separator />

      {/* Quick Actions */}
      <div className="space-y-3">
        <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Quick Actions</h4>
        <div className="grid grid-cols-2 gap-2">
          {isAgent ? (
            <>
              {data.status === "running" ? (
                <Button size="sm" variant="outline" className="w-full gap-2" onClick={() => controlAgent("paused")}>
                  <Pause size={14} /> Pause
                </Button>
              ) : (
                <Button size="sm" variant="outline" className="w-full gap-2" onClick={() => controlAgent("running")}>
                  <Play size={14} /> Start
                </Button>
              )}
              <Button size="sm" variant="outline" className="w-full gap-2 text-destructive hover:bg-destructive/10" onClick={() => controlAgent("stopped")}>
                <Square size={14} /> Stop
              </Button>
            </>
          ) : (
            <p className="col-span-2 text-xs text-muted-foreground">
              Le contrôle direct n&apos;est disponible que pour les agents. Les missions et objectifs sont pilotés depuis Workspace.
            </p>
          )}
        </div>
      </div>

      <Separator />

      {/* Raw Data */}
      <div className="space-y-3">
        <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
          <FileJson size={14} /> Raw Payload
        </h4>
        <pre className="text-[10px] font-mono bg-muted p-3 rounded-md overflow-x-auto text-muted-foreground">
          {JSON.stringify(data, null, 2)}
        </pre>
      </div>
    </div>
  );
}

export function GlobalInspector() {
  const { inspectorOpen, inspector, closeInspector } = useUIStore();

  return (
    <>
      {/* Backdrop for mobile (optional) */}
      {inspectorOpen && (
        <div 
          className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm md:hidden"
          onClick={closeInspector}
        />
      )}
      
      {/* Inspector Panel */}
      <aside
        className={cn(
          "fixed right-0 top-0 z-[60] h-[100dvh] w-full border-l bg-background shadow-2xl transition-transform duration-300 md:w-[400px]",
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
        
        <div className="h-[calc(100dvh-3.5rem)] overflow-y-auto p-4 custom-scrollbar">
          {!inspector.id ? (
            <div className="flex flex-col items-center justify-center h-40 text-center space-y-3">
              <Activity size={32} className="text-muted-foreground/30" />
              <p className="text-sm text-muted-foreground">Select an item (Mission, Agent, Goal) to inspect its details.</p>
            </div>
          ) : (
            <EntityDetails type={inspector.type!} id={inspector.id} />
          )}
        </div>
      </aside>
    </>
  );
}
