"use client";

import { useEffect } from "react";
import { useStore } from "@/lib/store";
import { statusColor } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Target } from "lucide-react";

export function GoalsPage() {
  const { goals, goalsLoading, fetchGoals } = useStore();

  useEffect(() => {
    fetchGoals();
    const interval = setInterval(fetchGoals, 10000);
    return () => clearInterval(interval);
  }, [fetchGoals]);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-bold text-text">Goal Tracker</h1>
        <p className="text-text-dim text-sm mt-1">{goals.length} goals actifs</p>
      </div>

      {goalsLoading && goals.length === 0 && (
        <div className="animate-pulse text-text-dim text-center py-8">Chargement...</div>
      )}

      <div className="space-y-3">
        {goals.map((goal) => (
          <div
            key={goal.id}
            className="rounded-lg border border-border bg-surface-2 p-4"
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center gap-2">
                <Target size={16} className="text-ethan-400 shrink-0" />
                <span className="text-sm font-mono text-text-dim">
                  {goal.id.slice(0, 8)}
                </span>
              </div>
              <div className="flex gap-2">
                <Badge variant={statusColor(goal.status)}>{goal.status}</Badge>
                <Badge variant="default">{goal.priority}</Badge>
              </div>
            </div>

            <p className="text-text mb-3">{goal.description}</p>

            <div className="flex items-center gap-3">
              <div className="flex-1 h-2 bg-surface-3 rounded-full overflow-hidden">
                <div
                  className="h-full bg-ethan-500 rounded-full transition-all duration-500"
                  style={{ width: `${goal.progress || 0}%` }}
                />
              </div>
              <span className="text-xs text-text-dim">{goal.progress || 0}%</span>
            </div>
          </div>
        ))}
        {!goalsLoading && goals.length === 0 && (
          <p className="text-text-dim text-center py-8">Aucun goal trouvé</p>
        )}
      </div>
    </div>
  );
}