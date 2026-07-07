"use client";

import { MetricCard } from "../metric-card";

interface NetworkData {
  latency: number;
  bandwidth: number;
  packetsIn: number;
  packetsOut: number;
  errors: number;
}

interface NetworkCardProps {
  data: NetworkData | null;
  loading?: boolean;
  sparkline?: number[];
}

export function NetworkCard({ data, loading, sparkline }: NetworkCardProps) {
  if (loading || !data) {
    return <MetricCard title="Network" value="—" status="loading" />;
  }

  const getStatus = (errors: number, latency: number): "normal" | "warning" | "critical" => {
    if (errors > 0) return "critical";
    if (latency > 200) return "warning";
    return "normal";
  };

  return (
    <MetricCard
      title="Network"
      value={`${data.latency}ms`}
      unit={`${data.bandwidth} Mbps`}
      status={getStatus(data.errors, data.latency)}
      icon="🌐"
      sparkline={sparkline}
      href="/system?tab=network"
    />
  );
}