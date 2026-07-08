"use client";

import * as React from "react";
import { Card } from "@/components/ui/card";
import { KpiCard } from "@/components/widgets/kpi-card";
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
  const { agents } = useAgents();
  const { goals } = useGoals();
  const { facts } = useFacts();
  const { events } = useFlux();
  const { missions } = useMissions();
  const { skills } = useSkills();

  const activeAgents = agents.filter((a) => a.status === "running").length;
  const activeGoals = goals.filter((g) => g.status === "active").length;
  const completedGoals = goals.filter((g) => g.status === "completed").length;
  const activeMissions = missions.filter((m) => m.status === "running" || m.status === "planning").length;
  const activeSkills = skills.filter((s) => s.status === "active").length;

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
    { name: "Error", value: agents.filter((a) => a.status === "error").length },
  ].filter((d) => d.value > 0);

  const goalStatusData = [
    { name: "Active", value: activeGoals },
    { name: "Completed", value: completedGoals },
    { name: "Pending", value: goals.filter((g) => g.status === "pending").length },
    { name: "Failed", value: goals.filter((g) => g.status === "failed").length },
  ].filter((d) => d.value > 0);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground mt-2">
          Welcome to ETHAN Cognitive Runtime
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          title="Active Agents"
          value={activeAgents}
          unit={`/${agents.length} total`}
          trend="up"
          trendValue="+2/hr"
          icon="⚡"
          sparklineData={[5, 8, 6, 9, 7, 10, 12]}
          onClick={() => {}}
        />
        <KpiCard
          title="Active Goals"
          value={activeGoals}
          unit={`${completedGoals} completed`}
          trend="up"
          trendValue="+3 today"
          icon="🏆"
          sparklineData={[3, 5, 4, 7, 5, 8, 8]}
          onClick={() => {}}
        />
        <KpiCard
          title="Memory Facts"
          value={facts.length}
          unit="active entries"
          trend="neutral"
          trendValue="94% confidence"
          icon="💾"
          sparklineData={[100, 150, 200, 180, 250, 300, 320]}
          onClick={() => {}}
        />
        <KpiCard
          title="Events Today"
          value={events.length}
          unit="in this session"
          trend="up"
          trendValue="12/min avg"
          icon="📊"
          sparklineData={[10, 15, 12, 18, 20, 16, 22]}
          onClick={() => {}}
        />
      </div>

      {/* Charts Row */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Weekly Activity</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={activityData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="name" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    background: "hsl(var(--background))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "8px",
                  }}
                />
                <Bar dataKey="events" fill="#60a5fa" radius={[4, 4, 0, 0]} name="Events" />
                <Bar dataKey="goals" fill="#34d399" radius={[4, 4, 0, 0]} name="Goals" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Agent Status</h2>
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
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {statusData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Second Row */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Goal Status</h2>
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
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {goalStatusData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Quick Stats</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Active Missions</span>
              <span className="text-lg font-bold">{activeMissions}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Installed Skills</span>
              <span className="text-lg font-bold">{activeSkills}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Total Goals</span>
              <span className="text-lg font-bold">{goals.length}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Total Missions</span>
              <span className="text-lg font-bold">{missions.length}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Skills Candidates</span>
              <span className="text-lg font-bold">{skills.filter((s) => s.status === "candidate").length}</span>
            </div>
          </div>
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