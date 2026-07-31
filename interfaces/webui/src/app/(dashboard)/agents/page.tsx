"use client";

import * as React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { MetricCard } from "@/components/shared/metric-card";
import { useAgents } from "@/features/agents/hooks/use-agents";
import { AgentEditorDialog } from "@/features/agents/components/agent-editor-dialog";
import { Play, Pause, Square, Plus, RefreshCw, AlertCircle, Clock, Cpu, Settings2 } from "lucide-react";

const statusConfig: Record<string, { label: string; color: "success" | "warning" | "error" | "default" | "info" | "dim" }> = {
  running: { label: "Running", color: "success" },
  paused: { label: "Paused", color: "warning" },
  error: { label: "Error", color: "error" },
  idle: { label: "Idle", color: "dim" },
  stopped: { label: "Stopped", color: "default" },
};

export default function AgentsPage() {
  const { agents, isLoading, error, refetch } = useAgents();
  const [editorOpen, setEditorOpen] = React.useState(false);
  const [editingId, setEditingId] = React.useState<string | null>(null);

  const handleOpenEditor = (id: string | null = null) => {
    setEditingId(id);
    setEditorOpen(true);
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-foreground">Agents</h1>
            <p className="text-muted-foreground mt-1">Manage and monitor your AI agents</p>
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} variant="outlined">
              <CardContent className="p-6">
                <Skeleton variant="text" lines={3} />
              </CardContent>
            </Card>
          ))}
        </div>
        <Card variant="outlined">
          <CardContent className="p-6">
            <Skeleton variant="rectangle" className="w-full" style={{ height: 300 }} />
          </CardContent>
        </Card>
      </div>
    );
  }

  const running = agents?.filter((a: any) => a.status === "running").length || 0;
  const paused = agents?.filter((a: any) => a.status === "paused").length || 0;
  const errored = agents?.filter((a: any) => a.status === "error").length || 0;
  const total = agents?.length || 0;

  return (
    <div className="space-y-8 pb-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Agents</h1>
          <p className="text-muted-foreground mt-1">Manage and monitor your AI agents</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" className="gap-2" onClick={() => refetch()}>
            <RefreshCw size={14} /> Refresh
          </Button>
          <Button size="sm" className="gap-2" onClick={() => handleOpenEditor(null)}>
            <Plus size={14} /> New Agent
          </Button>
        </div>
      </div>

      {error && (
        <Card variant="outlined" className="border-destructive/50 bg-destructive/5">
          <CardContent className="p-4 flex items-center gap-3">
            <AlertCircle size={18} className="text-destructive shrink-0" />
            <p className="text-sm text-destructive">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* KPI Strip */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard title="Total Agents" value={total} unit="agents" status="normal" href="/agents" />
        <MetricCard title="Running" value={running} unit={`/ ${total} total`} status="normal" href="/agents?status=running" />
        <MetricCard title="Paused" value={paused} unit={`/ ${total} total`} status="warning" href="/agents?status=paused" />
        <MetricCard title="Errors" value={errored} unit={`/ ${total} total`} status="error" href="/agents?status=error" />
      </div>

      {/* Agents List */}
      <Card variant="outlined">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle>All Agents</CardTitle>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">{total} total</span>
          </div>
        </CardHeader>
        <CardContent>
          {agents?.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Cpu size={48} className="text-muted-foreground/30 mb-4" />
              <p className="text-muted-foreground mb-2">No agents yet</p>
              <p className="text-sm text-muted-foreground/60 mb-4">Create your first agent to get started</p>
              <Button size="sm" className="gap-2" onClick={() => handleOpenEditor(null)}>
                <Plus size={14} /> Create Agent
              </Button>
            </div>
          ) : (
            <div className="space-y-3">
              {agents?.map((agent: any) => {
                const status = statusConfig[agent.status] || statusConfig.stopped;
                return (
                  <div key={agent.id} className="rounded-lg border bg-card p-4 transition-all hover:bg-accent/5">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`h-2.5 w-2.5 rounded-full ${
                          agent.status === "running" ? "bg-green animate-pulse" :
                          agent.status === "error" ? "bg-red" :
                          agent.status === "paused" ? "bg-amber" :
                          "bg-muted-foreground/30"
                        }`} />
                        <div>
                          <div className="font-medium">{agent.name}</div>
                          <div className="text-sm text-muted-foreground">
                            {agent.capabilities?.slice(0, 3).join(", ")}
                            {agent.capabilities?.length > 3 && ` +${agent.capabilities.length - 3} more`}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-xs text-muted-foreground">{status.label}</span>
                        <div className="flex items-center gap-1">
                          <Button size="sm" variant="ghost" className="h-8 w-8 p-0" onClick={() => handleOpenEditor(agent.id)}>
                            <Settings2 size={14} />
                          </Button>
                          {agent.status === "running" ? (
                            <>
                              <Button size="sm" variant="ghost" className="h-8 w-8 p-0"><Pause size={14} /></Button>
                              <Button size="sm" variant="ghost" className="h-8 w-8 p-0 text-destructive"><Square size={14} /></Button>
                            </>
                          ) : agent.status === "paused" ? (
                            <Button size="sm" variant="ghost" className="h-8 w-8 p-0"><Play size={14} /></Button>
                          ) : (
                            <Button size="sm" variant="ghost" className="h-8 w-8 p-0"><Play size={14} /></Button>
                          )}
                        </div>
                      </div>
                    </div>
                    {agent.lastActive && (
                      <div className="mt-2 flex items-center gap-1.5 text-xs text-muted-foreground">
                        <Clock size={12} />
                        Last active: {new Date(agent.lastActive).toLocaleString()}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      <AgentEditorDialog 
        open={editorOpen} 
        onOpenChange={setEditorOpen} 
        agentId={editingId} 
      />
    </div>
  );
}