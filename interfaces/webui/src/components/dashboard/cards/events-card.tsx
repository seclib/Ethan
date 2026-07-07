"use client";

import { MetricCard } from "../metric-card";

interface EventsData {
  total: number;
  rate: number;
  errors: number;
  warnings: number;
}

interface EventsCardProps {
  data: EventsData | null;
  loading?: boolean;
  sparkline?: number[];
}

export function EventsCard({ data, loading, sparkline }: EventsCardProps) {
  if (loading || !data) {
    return <MetricCard title="Events" value="—" status="loading" />;
  }

  const getStatus = (errors: number, warnings: number): "normal" | "warning" | "critical" => {
    if (errors > 0) return "critical";
    if (warnings > 0) return "warning";
    return "normal";
  };

  return (
    <MetricCard
      title="Events"
      value={data.total.toLocaleString()}
      unit={`${data.rate}/s`}
      status={getStatus(data.errors, data.warnings)}
      icon="📡"
      sparkline={sparkline}
      href="/logs?filter=events"
    />
  );
}