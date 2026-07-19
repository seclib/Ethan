"use client";

import * as React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import { MetricCard } from "@/components/shared/metric-card";
import { useMissions } from "@/features/missions/hooks/use-missions";
import { Play, Pause, Square, Plus, RefreshCw, AlertCircle, Target, Clock, ListChecks } from "lucide-react";

const statusConfig: Record<string, { label: string; color: "success" | "warning" | "error" | "default" | "info" | "dim" }> = {
  running: { label: "Running", color: "info" },
  completed: { label: "Completed", color: "success" },
  failed: { label: "Failed", color: "error" },
  paused: { label: "Paused", color: "warning" },
  pending: { label: "Pending", color: "dim" },
};

export default function MissionsPage() {
  const { missions, isLoading, error, refetch } = useMissions();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-foreground">Missions</h1>
            <p className="text-muted-foreground mt-1">Plan and execute multi-step operations</p>
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

  const running = missions?.filter((m: any) => m.status === "running").length || 0;
  const completed = missions?.filter((m: any) => m.status === "completed").length || 0;
  const failed = missions?.filter((m: any) => m.status === "failed").length || 0;
  const total = missions?.length || 0;

  return (
    <div className="space-y-8 animate-fade-in pb-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Missions</h1>
          <p className="text-muted-foreground mt-1">Plan and execute multi-step operations</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" className="gap-2" onClick={() => refetch()}>
            <RefreshCw size={14} /> Refresh
          </Button>
          <Button size="sm" className="gap-2">
            <Plus size={14} /> New Mission
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
        <MetricCard title="Total Missions" value={total} unit="missions" status="normal" href="/missions" />
        <MetricCard title="Running" value={running} unit="active" status={running > 0 ? "normal" : "na"} href="/missions?status=running" />
        <MetricCard title="Completed" value={completed} unit="done" status={completed > 0 ? "normal" : "na"} href="/missions?status=completed" />
        <MetricCard title="Failed" value={failed} unit="errors" status="error" href="/missions?status=failed" />
      </div>

      {/* Missions List */}
      <Card variant="outlined">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle>All Missions</CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="default" className="text-xs">{total} total</Badge>
          </div>
        </CardHeader>
        <CardContent>
          {missions?.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Target size={48} className="text-muted-foreground/30 mb-4" />
              <p className="text-muted-foreground mb-2">No missions yet</p>
              <p className="text-sm text-muted-foreground/60 mb-4">Create your first mission to get started</p>
              <Button size="sm" className="gap-2">
                <Plus size={14} /> Create Mission
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              {missions?.map((mission: any) => {
                const status = statusConfig[mission.status] || statusConfig.pending;
                const progress = mission.steps_total > 0
                  ? Math.round((mission.steps_completed / mission.steps_total) * 100)
                  : 0;

                return (
                  <div key={mission.id} className="rounded-lg border bg-card p-4 transition-all hover:bg-accent/5">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <Target size={16} className="text-muted-foreground" />
                        <div className="font-medium">{mission.title}</div>
                      </div>
                      <div className="flex items-center gap-3">
                        <Badge variant={status.color}>{status.label}</Badge>
                        <div className="flex items-center gap-1">
                          {mission.status === "running" ? (
                            <>
                              <Button size="sm" variant="ghost" className="h-8 w-8 p-0"><Pause size={14} /></Button>
                              <Button size="sm" variant="ghost" className="h-8 w-8 p-0 text-destructive"><Square size={14} /></Button>
                            </>
                          ) : mission.status === "paused" ? (
                            <Button size="sm" variant="ghost" className="h-8 w-8 p-0"><Play size={14} /></Button>
                          ) : null}
                        </div>
                      </div>
                    </div>
                    {mission.description && (
                      <p className="text-sm text-muted-foreground mb-3 ml-7">{mission.description}</p>
                    )}
                    <div className="ml-7">
                      <div className="flex items-center justify-between mb-1">
                        <div className="text-sm font-mono text-muted-foreground">{progress}%</div>
                        {mission.steps_total > 0 && (
                          <div className="text-sm text-muted-foreground flex items-center gap-1.5">
                            <ListChecks size={14} />
                            {mission.steps_completed}/{mission.steps_total} steps
                          </div>
                        )}
                      </div>
                      <Progress value={progress} className="h-2" />
                    </div>
                    {mission.created_at && (
                      <div className="mt-2 ml-7 flex items-center gap-1.5 text-xs text-muted-foreground">
                        <Clock size={12} />
                        Created: {new Date(mission.created_at).toLocaleString()}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}