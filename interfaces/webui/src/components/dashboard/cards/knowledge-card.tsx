"use client";

import { MetricCard } from "../metric-card";

interface KnowledgeData {
  entries: number;
  skills: number;
  contextUsed: number;
  contextTotal: number;
  embeddings: number;
}

interface KnowledgeCardProps {
  data: KnowledgeData | null;
  loading?: boolean;
  sparkline?: number[];
}

export function KnowledgeCard({ data, loading, sparkline }: KnowledgeCardProps) {
  if (loading || !data) {
    return <MetricCard title="Knowledge" value="—" status="loading" />;
  }

  const contextPercent = Math.round((data.contextUsed / data.contextTotal) * 100);
  const getStatus = (pct: number): "normal" | "warning" | "critical" => {
    if (pct > 90) return "critical";
    if (pct > 70) return "warning";
    return "normal";
  };

  return (
    <MetricCard
      title="Knowledge"
      value={data.entries.toLocaleString()}
      unit={`${data.skills} skills`}
      status={getStatus(contextPercent)}
      icon="🧠"
      progress={contextPercent}
      sparkline={sparkline}
      href="/knowledge"
    />
  );
}