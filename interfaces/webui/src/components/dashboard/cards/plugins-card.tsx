"use client";

import { MetricCard } from "../metric-card";

interface PluginStatus {
  name: string;
  active: boolean;
  version: string;
}

interface PluginsCardProps {
  data: PluginStatus[] | null;
  loading?: boolean;
}

export function PluginsCard({ data, loading }: PluginsCardProps) {
  if (loading || !data) {
    return <MetricCard title="Plugins" value="—" status="loading" />;
  }

  const active = data.filter(p => p.active).length;
  const total = data.length;
  const errors = data.filter(p => !p.active).length;
  
  const getStatus = (activeCount: number, errorCount: number): "normal" | "warning" | "critical" => {
    if (errorCount > 0) return "warning";
    if (activeCount === 0) return "critical";
    return "normal";
  };

  return (
    <MetricCard
      title="Plugins"
      value={`${active}/${total}`}
      unit={errors > 0 ? `${errors} inactive` : "loaded"}
      status={getStatus(active, errors)}
      icon="🧩"
      onClick={() => {}}
    />
  );
}