"use client";

import * as React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { Spinner } from "@/components/ui/spinner";
import { MetricCard } from "@/components/shared/metric-card";
import { EventStream } from "@/components/shared/event-stream";
import { useAgents } from "@/features/agents/hooks/use-agents";
import { useGoals } from "@/features/goals/hooks/use-goals";
import { useFacts } from "@/features/memory/hooks/use-memory";
import { useFlux } from "@/features/flux/hooks/use-flux";
import { useMissions } from "@/features/missions/hooks/use-missions";
import { Play, Pause, Square, Plus, Search, Terminal } from "lucide-react";

export default function DashboardPage() {
  const { agents, isLoading: agentsLoading } = useAgents();
  const { goals, isLoading: goalsLoading } = useGoals();
  const { facts, isLoading: factsLoading } = useFacts();
  const { events, isLoading: eventsLoading } = useFlux();
  const { missions, isLoading: missionsLoading } = useMissions();

  const isLoading = agentsLoading || goalsLoading || factsLoading || eventsLoading || missionsLoading;

  const activeAgents = agents?.filter((a: any) => a.status === "running").length || 0;
  const activeGoals = goals?.filter((g: any) => g.status === "active").length || 0;
  const totalFacts = facts?.length || 0;
  const eventsCount = events?.length || 0;

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Dashboard</h1>
          <Spinner />
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
            <Skeleton variant="rectangle" className="w-full" style={{ height: 200 }} />
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in pb-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            System status and active operations
          </p>
        </div>
        <Badge>Live</Badge>
      </div>

      {/* KPI Strip */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Active Agents"
          value={activeAgents}
          unit={`/ ${agents?.length || 0} total`}
          status="normal"
          sparkline={[5, 8, 6, 9, 7, 10, 12]}
          href="/agents"
        />
        <MetricCard
          title="Active Goals"
          value={activeGoals}
          unit={`/ ${goals?.length || 0} total`}
          status="normal"
          sparkline={[3, 5, 4, 7, 5, 8, 8]}
          href="/planner"
        />
        <MetricCard
          title="Memory Facts"
          value={totalFacts}
          unit="entries"
          status="normal"
          sparkline={[100, 150, 200, 180, 250, 300, 320]}
          href="/memory"
        />
        <MetricCard
          title="Events Today"
          value={eventsCount}
          unit="total"
          status="normal"
          sparkline={[10, 15, 12, 18, 20, 16, 22]}
          href="/logs"
        />
      </div>

      {/* Recent Missions */}
      <Card variant="outlined">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle>Recent Missions</CardTitle>
          <Button size="sm" variant="outline" className="gap-2">
            <Plus size={14} /> New Mission
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          {missions?.slice(0, 5).map((mission: any) => {
            const stepsTotal = mission.steps_total || 1;
            const stepsCompleted = mission.steps_completed || 0;
            const progress = Math.round((stepsCompleted / stepsTotal) * 100);
            return (
              <div key={mission.id} className="rounded-lg border bg-card p-4 transition-all hover:bg-accent/5">
                <div className="flex items-center justify-between mb-2">
                  <div className="font-medium">{mission.title}</div>
                  <div className="text-sm font-mono text-muted-foreground">{progress}%</div>
                </div>
                <Progress value={progress} className="h-2 mb-3" />
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-4 text-muted-foreground">
                    <span>Steps: {stepsCompleted}/{stepsTotal}</span>
                    <span className="flex items-center gap-1.5">
                      <div className="h-2 w-2 rounded-full bg-blue-500 animate-pulse" />
                      {mission.status}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button size="sm" variant="ghost" className="h-8 px-2"><Pause size={14} className="mr-1" /> Pause</Button>
                    <Button size="sm" variant="ghost" className="h-8 px-2 text-destructive"><Square size={14} className="mr-1" /> Kill</Button>
                    <Button size="sm" variant="outline" className="h-8 px-2">View</Button>
                  </div>
                </div>
              </div>
            );
          })}
        </CardContent>
      </Card>

      <Separator />

      {/* Quick Actions */}
      <div className="space-y-3">
        <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Quick Actions</h3>
        <div className="flex flex-wrap gap-3">
          <Button variant="secondary" className="gap-2">
            <Plus size={16} /> New Mission
          </Button>
          <Button variant="secondary" className="gap-2">
            <Play size={16} /> Start Agent
          </Button>
          <Button variant="secondary" className="gap-2">
            <Search size={16} /> Search Memory
          </Button>
          <Button variant="secondary" className="gap-2">
            <Terminal size={16} /> Open Terminal
          </Button>
        </div>
      </div>

      {/* Event Stream */}
      <div className="space-y-3">
        <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Event Stream</h3>
        <EventStream
          events={events?.slice(0, 50) || []}
          maxHeight={350}
          showFilters={false}
          onPause={() => {}}
          onResume={() => {}}
        />
      </div>
    </div>
  );
}