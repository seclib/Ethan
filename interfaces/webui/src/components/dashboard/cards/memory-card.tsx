"use client";

import { MetricCard } from "../metric-card";

interface MemoryData {
  entries: number;
  redisKeys: number;
  postgresEvents: number;
  sizeMb: number;
  hitRate: number;
}

interface MemoryCardProps {
  data: MemoryData | null;
  loading?: boolean;
}

export function MemoryCard({ data, loading }: MemoryCardProps) {
  if (loading || !data) {
    return <MetricCard title="Memory" value="—" status="loading" />;
  }

  const getStatus = (hitRate: number): "normal" | "warning" | "critical" => {
    if (hitRate < 70) return "critical";
    if (hitRate < 85) return "warning";
    return "normal";
  };

  return (
    <MetricCard
      title="Memory"
      value={data.entries.toLocaleString()}
      unit={`${data.sizeMb} MB`}
      status={getStatus(data.hitRate)}
      icon="💾"
      progress={data.hitRate}
      onClick={() => {}}
    />
  );
}