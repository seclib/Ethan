"use client";

import { MetricCard } from "../metric-card";

interface ProviderStatus {
  name: string;
  connected: boolean;
  latencyMs: number;
}

interface ProvidersCardProps {
  data: ProviderStatus[] | null;
  loading?: boolean;
  sparkline?: number[];
}

export function ProvidersCard({ data, loading, sparkline }: ProvidersCardProps) {
  if (loading || !data) {
    return <MetricCard title="Providers" value="—" status="loading" />;
  }

  const connected = data.filter(p => p.connected).length;
  const total = data.length;
  const avgLatency = data.filter(p => p.connected).reduce((sum, p) => sum + p.latencyMs, 0) / (connected || 1);
  
  const getStatus = (pct: number): "normal" | "warning" | "critical" => {
    if (pct === 0) return "critical";
    if (pct < 100) return "warning";
    return "normal";
  };

  return (
    <MetricCard
      title="Providers"
      value={`${connected}/${total}`}
      unit={`${avgLatency.toFixed(0)}ms avg`}
      status={getStatus(connected)}
      icon="🔌"
      sparkline={sparkline}
      href="/providers"
    />
  );
}