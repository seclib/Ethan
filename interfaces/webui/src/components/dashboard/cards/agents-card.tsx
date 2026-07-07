"use client";

import { MetricCard } from "../metric-card";

interface AgentStatus {
  name: string;
  status: "run" | "idle" | "sleep" | "error";
}

interface AgentsCardProps {
  data: AgentStatus[] | null;
  loading?: boolean;
  sparkline?: number[];
}

export function AgentsCard({ data, loading, sparkline }: AgentsCardProps) {
  if (loading || !data) {
    return <MetricCard title="Agents" value="—" status="loading" />;
  }

  const active = data.filter(a => a.status === "run").length;
  const total = data.length;
  const errors = data.filter(a => a.status === "error").length;
  
  const getStatus = (activeCount: number, errorCount: number): "normal" | "warning" | "critical" => {
    if (errorCount > 0) return "critical";
    if (activeCount === 0) return "warning";
    return "normal";
  };

  return (
    <MetricCard
      title="Agents"
      value={`${active}/${total}`}
      unit={errors > 0 ? `${errors} error(s)` : "active"}
      status={getStatus(active, errors)}
      icon="🤖"
      sparkline={sparkline}
      href="/agents"
    />
  );
}