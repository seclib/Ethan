"use client";

import { MetricCard } from "../metric-card";

interface McpData {
  toolsAvailable: number;
  toolsCalled: number;
  successRate: number;
  avgLatency: number;
  errors: number;
}

interface McpCardProps {
  data: McpData | null;
  loading?: boolean;
}

export function McpCard({ data, loading }: McpCardProps) {
  if (loading || !data) {
    return <MetricCard title="MCP" value="—" status="loading" />;
  }

  const getStatus = (successRate: number): "normal" | "warning" | "critical" => {
    if (successRate < 80) return "critical";
    if (successRate < 95) return "warning";
    return "normal";
  };

  return (
    <MetricCard
      title="MCP"
      value={data.toolsAvailable.toString()}
      unit={`${data.toolsCalled} calls`}
      status={getStatus(data.successRate)}
      icon="🔧"
      progress={data.successRate}
      onClick={() => {}}
    />
  );
}