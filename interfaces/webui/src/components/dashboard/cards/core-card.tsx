"use client";

import { MetricCard } from "../metric-card";

interface CoreData {
  status: "online" | "degraded" | "offline";
  uptime: string;
  version: string;
  pid: number;
}

interface CoreCardProps {
  data: CoreData | null;
  loading?: boolean;
}

export function CoreCard({ data, loading }: CoreCardProps) {
  if (loading || !data) {
    return <MetricCard title="Core" value="—" status="loading" />;
  }

  const getStatus = (status: string): "normal" | "warning" | "critical" => {
    if (status === "online") return "normal";
    if (status === "degraded") return "warning";
    return "critical";
  };

  return (
    <MetricCard
      title="Core"
      value={data.status.toUpperCase()}
      unit={`v${data.version}`}
      status={getStatus(data.status)}
      icon="⚙️"
      onClick={() => {}}
    />
  );
}