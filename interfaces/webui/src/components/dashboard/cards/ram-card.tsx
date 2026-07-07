"use client";

import { MetricCard } from "../metric-card";

interface RamData {
  used: number;
  total: number;
  available: number;
  cached?: number;
  swapUsed?: number;
  swapTotal?: number;
}

interface RamCardProps {
  data: RamData | null;
  loading?: boolean;
  sparkline?: number[];
}

export function RamCard({ data, loading, sparkline }: RamCardProps) {
  if (loading || !data) {
    return <MetricCard title="RAM" value="—" status="loading" />;
  }

  const usedPercent = Math.round((data.used / data.total) * 100);
  const getStatus = (pct: number): "normal" | "warning" | "critical" => {
    if (pct > 90) return "critical";
    if (pct > 70) return "warning";
    return "normal";
  };

  return (
    <MetricCard
      title="RAM"
      value={`${data.used} GB`}
      unit={`/ ${data.total} GB`}
      status={getStatus(usedPercent)}
      icon="💾"
      progress={usedPercent}
      sparkline={sparkline}
      href="/system?tab=ram"
    />
  );
}