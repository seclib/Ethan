"use client";

import { MetricCard } from "../metric-card";

interface CpuData {
  usage: number;
  cores: number;
  frequency: number;
  temperature?: number;
  load1: number;
  load5: number;
  load15: number;
}

interface CpuCardProps {
  data: CpuData | null;
  loading?: boolean;
}

export function CpuCard({ data, loading }: CpuCardProps) {
  if (loading || !data) {
    return <MetricCard title="CPU" value="—" status="loading" />;
  }

  const getStatus = (usage: number): "normal" | "warning" | "critical" => {
    if (usage > 80) return "critical";
    if (usage > 50) return "warning";
    return "normal";
  };

  return (
    <MetricCard
      title="CPU"
      value={`${data.usage}%`}
      status={getStatus(data.usage)}
      icon="⚡"
      sparkline={[data.usage, data.usage * 0.9, data.usage * 1.1, data.usage * 0.95, data.usage]}
      onClick={() => {}}
    />
  );
}