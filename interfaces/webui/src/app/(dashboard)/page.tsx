"use client";

import * as React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import { Spinner } from "@/components/ui/spinner";
import { MetricCard } from "@/components/shared/metric-card";
import { EventStream } from "@/components/shared/event-stream";
import { useAgents } from "@/features/agents/hooks/use-agents";
import { useGoals } from "@/features/goals/hooks/use-goals";
import { useFacts } from "@/features/memory/hooks/use-memory";
import { useFlux } from "@/features/flux/hooks/use-flux";
import { useMissions } from "@/features/missions/hooks/use-missions";
import { Play, Pause, Square, Plus, Search, Terminal, Activity } from "lucide-react";
import type { Agent, Goal, Mission } from "@/types";

export default function DashboardPage() {
  const { agents, isLoading: agentsLoading } = useAgents();
  const { goals, isLoading: goalsLoading } = useGoals();
  const { facts, isLoading: factsLoading } = useFacts();
  const { events, isLoading: eventsLoading } = useFlux();
  const { missions, isLoading: missionsLoading } = useMissions();

  const isLoading = agentsLoading || goalsLoading || factsLoading || eventsLoading || missionsLoading;

  const activeAgents = agents?.filter((a: Agent) => a.status === "running").length || 0;
  const activeGoals = goals?.filter((g: Goal) => g.status === "active").length || 0;
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
            <Card key={i}>
              <CardContent className="p-6">
                <Skeleton variant="text" lines={3} />
              </CardContent>
            </Card>
          ))}
        </div>
        <Card>
          <CardContent className="p-6">
            <Skeleton variant="rectangle" className="w-full" style={{ height: 200 }} />
          </CardContent>
        </Card>
      </div>
    );
  }

  const hasLiveData = activeAgents > 0 || activeGoals > 0 || totalFacts > 0 || eventsCount > 0;

  return (
    <div className="space-y-8 pb-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-foreground">Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            System status and active operations
          </p>
        </div>
        {hasLiveData && <Badge>Live</Badge>}
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
          sparkline={[31, 47, 63, 56, 78, 94, 100]}
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
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle>Recent Missions</CardTitle>
          <Button size="sm" variant="outline" className="gap-2" aria-label="New Mission">
            <Plus size={14} /> New Mission
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          {(missions as Mission[])?.length > 0 ? (
            (missions as Mission[])?.slice(0, 5).map((mission) => {
              const stepsTotal = mission.steps_total || 0;
              const stepsCompleted = mission.steps_completed || 0;
              const progress = stepsTotal > 0 ? Math.round((stepsCompleted / stepsTotal) * 100) : 0;
              return (
                <div key={mission.id} className="rounded-lg border border-line-2 bg-card p-4 transition-all hover:bg-accent/5">
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-medium">{mission.title}</div>
                    <div className="text-sm font-mono text-muted-foreground">{progress}%</div>
                  </div>
                  <Progress value={progress} className="h-2 mb-3" />
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-4 text-muted-foreground">
                      <span>Steps: {stepsCompleted}/{stepsTotal}</span>
                      <span className="flex items-center gap-1.5">
                          <div className="h-2 w-2 rounded-full bg-accent animate-pulse" />
                        {mission.status}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button size="sm" variant="ghost" className="h-8 px-2" aria-label="Pause mission"><Pause size={14} className="mr-1" /> Pause</Button>
                      <Button size="sm" variant="ghost" className="h-8 px-2 text-destructive" aria-label="Kill mission"><Square size={14} className="mr-1" /> Kill</Button>
                      <Button size="sm" variant="ghost" className="h-8 px-2" aria-label="View mission details">View</Button>
                    </div>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="flex flex-col items-center justify-center py-8 text-center text-muted-foreground">
              <Activity size={24} className="mb-2 opacity-50" />
              <p className="text-sm">No missions yet</p>
              <p className="text-xs mt-1">Create a mission to get started</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="space-y-3">
        <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Quick Actions</h3>
        <div className="flex flex-wrap gap-3">
          <Button variant="secondary" className="gap-2" aria-label="Create new mission">
            <Plus size={16} /> New Mission
          </Button>
          <Button variant="secondary" className="gap-2" aria-label="Start a new agent">
            <Play size={16} /> Start Agent
          </Button>
          <Button variant="secondary" className="gap-2" aria-label="Search memory facts">
            <Search size={16} /> Search Memory
          </Button>
          <Button variant="secondary" className="gap-2" aria-label="Open terminal">
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

      {!hasLiveData && (
        <div className="flex items-center justify-center gap-2 py-6 text-xs text-muted-foreground">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-60"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-accent/80"></span>
          </span>
          Awaiting live data...
        </div>
      )}
    </div>
  );
}