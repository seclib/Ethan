"use client";

import * as React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { MetricCard } from "@/components/dashboard/metric-card";
import { EventStream } from "@/components/widgets/event-stream";
import { useAgents } from "@/hooks/use-agents";
import { useGoals } from "@/hooks/use-goals";
import { useFacts } from "@/hooks/use-memory";
import { useFlux } from "@/hooks/use-flux";
import { useMissions } from "@/hooks/use-missions";
import { useSkills } from "@/hooks/use-skills";
import {
  ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell,
  CartesianGrid, XAxis, YAxis, Tooltip,
} from "recharts";

const COLORS = ["#60a5fa", "#34d399", "#fbbf24", "#f87171", "#a78bfa", "#fb923c"];

function DashboardPage() {
  const { agents, isLoading: agentsLoading } = useAgents();
  const { goals, isLoading: goalsLoading } = useGoals();
  const { facts, isLoading: factsLoading } = useFacts();
  const { events, isLoading: eventsLoading } = useFlux();
  const { missions, isLoading: missionsLoading } = useMissions();
  const { skills, isLoading: skillsLoading } = useSkills();

  const isLoading = agentsLoading || goalsLoading || factsLoading || eventsLoading || missionsLoading || skillsLoading;

  const activeAgents = agents.filter((a: any) => a.status === "running").length;
  const activeGoals = goals.filter((g: any) => g.status === "active").length;
  const completedGoals = goals.filter((g: any) => g.status === "completed").length;
  const activeMissions = missions.filter((m: any) => m.status === "running" || m.status === "planning").length;
  const activeSkills = skills.filter((s: any) => s.status === "active").length;

  // Mock chart data (replace with real data from API)
  const activityData = [
    { name: "Mon", events: 12, goals: 3 },
    { name: "Tue", events: 19, goals: 5 },
    { name: "Wed", events: 8, goals: 2 },
    { name: "Thu", events: 15, goals: 7 },
    { name: "Fri", events: 22, goals: 4 },
    { name: "Sat", events: 10, goals: 1 },
    { name: "Sun", events: 14, goals: 6 },
  ];

  const statusData = [
    { name: "Running", value: activeAgents },
    { name: "Idle", value: agents.length - activeAgents },
    { name: "Error", value: agents.filter((a: any) => a.status === "error").length },
  ].filter((d) => d.value > 0);

  const goalStatusData = [
    { name: "Active", value: activeGoals },
    { name: "Completed", value: completedGoals },
    { name: "Pending", value: goals.filter((g: any) => g.status === "pending").length },
    { name: "Failed", value: goals.filter((g: any) => g.status === "failed").length },
  ].filter((d) => d.value > 0);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
          <p className="text-foreground-secondary mt-2">Loading...</p>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} variant="outlined">
              <CardContent>
                <Skeleton variant="text" lines={4} />
              </CardContent>
            </Card>
          ))}
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          {[1, 2].map((i) => (
            <Card key={i} variant="outlined">
              <CardContent>
                <Skeleton variant="rectangle" className="w-full" style={{ height: 256 }} />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
        <p className="text-foreground-secondary mt-2">
          Welcome to ETHAN Cognitive Runtime
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Active Agents"
          value={activeAgents}
          unit={`/${agents.length} total`}
          status="normal"
          sparkline={[5, 8, 6, 9, 7, 10, 12]}
          href="/agents"
        />
        <MetricCard
          title="Active Goals"
          value={activeGoals}
          unit={`${completedGoals} completed`}
          status="normal"
          sparkline={[3, 5, 4, 7, 5, 8, 8]}
          href="/goals"
        />
        <MetricCard
          title="Memory Facts"
          value={facts.length}
          unit="active entries"
          status="normal"
          sparkline={[100, 150, 200, 180, 250, 300, 320]}
          href="/memory/facts"
        />
        <MetricCard
          title="Events Today"
          value={events.length}
          unit="in this session"
          status="normal"
          sparkline={[10, 15, 12, 18, 20, 16, 22]}
          href="/flux"
        />
      </div>

      {/* Charts Row */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card variant="outlined">
          <CardHeader>
            <CardTitle>Weekly Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={activityData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--line-2)" />
                  <XAxis dataKey="name" stroke="var(--fg-2)" fontSize={12} />
                  <YAxis stroke="var(--fg-2)" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      background: "var(--bg-1)",
                      border: "1px solid var(--line-2)",
                      borderRadius: "8px",
                      color: "var(--fg-0)",
                    }}
                  />
                  <Bar dataKey="events" fill="var(--accent-400)" radius={[4, 4, 0, 0]} name="Events" />
                  <Bar dataKey="goals" fill="var(--success)" radius={[4, 4, 0, 0]} name="Goals" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card variant="outlined">
          <CardHeader>
            <CardTitle>Agent Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={statusData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    paddingAngle={5}
                    dataKey="value"
                    label={({ name, percent }: any) => `${name} ${(percent * 100).toFixed(0)}%`}
                  >
                    {statusData.map((_: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      background: "var(--bg-1)",
                      border: "1px solid var(--line-2)",
                      borderRadius: "8px",
                      color: "var(--fg-0)",
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Second Row */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card variant="outlined">
          <CardHeader>
            <CardTitle>Goal Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={goalStatusData}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                    label={({ name, percent }: any) => `${name} ${(percent * 100).toFixed(0)}%`}
                  >
                    {goalStatusData.map((_: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      background: "var(--bg-1)",
                      border: "1px solid var(--line-2)",
                      borderRadius: "8px",
                      color: "var(--fg-0)",
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card variant="outlined">
          <CardHeader>
            <CardTitle>Quick Stats</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-foreground-tertiary">Active Missions</span>
                <span className="text-lg font-bold text-foreground">{activeMissions}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-foreground-tertiary">Installed Skills</span>
                <span className="text-lg font-bold text-foreground">{activeSkills}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-foreground-tertiary">Total Goals</span>
                <span className="text-lg font-bold text-foreground">{goals.length}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-foreground-tertiary">Total Missions</span>
                <span className="text-lg font-bold text-foreground">{missions.length}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-foreground-tertiary">Skills Candidates</span>
                <span className="text-lg font-bold text-foreground">
                  {skills.filter((s: any) => s.status === "candidate").length}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Event Stream */}
      <EventStream
        events={events}
        maxHeight={400}
        showFilters={true}
        onPause={() => console.log("Paused")}
        onResume={() => console.log("Resumed")}
        onExport={() => {
          const blob = new Blob([JSON.stringify(events, null, 2)], { type: "application/json" });
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = "events.json";
          a.click();
        }}
      />
    </div>
  );
}

export default DashboardPage;