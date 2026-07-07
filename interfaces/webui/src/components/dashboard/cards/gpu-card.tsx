"use client";

import { MetricCard } from "../metric-card";

interface GpuData {
  name: string;
  utilization: number;
  vramUsed: number;
  vramTotal: number;
  temperature?: number;
  power?: number;
  frequency?: number;
}

interface GpuCardProps {
  data: GpuData | null;
  loading?: boolean;
  sparkline?: number[];
}

export function GpuCard({ data, loading, sparkline }: GpuCardProps) {
  if (loading || !data) {
    return <MetricCard title="GPU" value="—" status="loading" />;
  }

  const vramPercent = Math.round((data.vramUsed / data.vramTotal) * 100);
  const getStatus = (util: number): "normal" | "warning" | "critical" => {
    if (util > 90) return "critical";
    if (util > 70) return "warning";
    return "normal";
  };

  return (
    <MetricCard
      title="GPU"
      value={`${data.utilization}%`}
      unit={`${data.vramUsed}/${data.vramTotal} GB`}
      status={getStatus(data.utilization)}
      icon="🎮"
      progress={data.utilization}
      sparkline={sparkline}
      href="/system?tab=gpu"
    />
  );
}