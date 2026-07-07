"use client";

import { MetricCard } from "../metric-card";

interface TokensData {
  used: number;
  total: number;
  rate: number;
  cost: number;
  model: string;
}

interface TokensCardProps {
  data: TokensData | null;
  loading?: boolean;
}

export function TokensCard({ data, loading }: TokensCardProps) {
  if (loading || !data) {
    return <MetricCard title="Tokens" value="—" status="loading" />;
  }

  const usedPercent = Math.round((data.used / data.total) * 100);
  const getStatus = (pct: number): "normal" | "warning" | "critical" => {
    if (pct > 90) return "critical";
    if (pct > 70) return "warning";
    return "normal";
  };

  return (
    <MetricCard
      title="Tokens"
      value={data.used.toLocaleString()}
      unit={`/ ${data.total.toLocaleString()}`}
      status={getStatus(usedPercent)}
      icon="🔤"
      progress={usedPercent}
      onClick={() => {}}
    />
  );
}