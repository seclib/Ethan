"use client";

import { MetricCard } from "../metric-card";

interface PlannerData {
  objective: string;
  tasksDone: number;
  tasksTotal: number;
  nextStep?: string;
}

interface PlannerCardProps {
  data: PlannerData | null;
  loading?: boolean;
}

export function PlannerCard({ data, loading }: PlannerCardProps) {
  if (loading || !data) {
    return <MetricCard title="Planner" value="—" status="loading" />;
  }

  const progress = data.tasksTotal > 0 ? Math.round((data.tasksDone / data.tasksTotal) * 100) : 0;
  const getStatus = (pct: number): "normal" | "warning" | "critical" => {
    if (pct === 100) return "normal";
    if (pct > 50) return "normal";
    if (pct > 0) return "warning";
    return "critical";
  };

  return (
    <MetricCard
      title="Planner"
      value={`${data.tasksDone}/${data.tasksTotal}`}
      unit="tasks"
      status={getStatus(progress)}
      icon="📋"
      progress={progress}
      onClick={() => {}}
    />
  );
}