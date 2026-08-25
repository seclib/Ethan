"use client";

import * as React from "react";
import { useMissions, useCreateMission } from "@/components/features/missions/hooks/use-missions";
import { useGoals } from "@/components/features/goals/hooks/use-goals";
import { useUIStore } from "@/store/ui.store";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Target, Plus, RefreshCw, CheckSquare } from "lucide-react";
import type { Mission, Goal } from "@/types";

const statusBadge: Record<string, "success" | "warning" | "error" | "info" | "dim" | "default"> = {
  running: "success",
  planning: "info",
  paused: "warning",
  failed: "error",
  pending: "default",
  completed: "success",
  killed: "error",
};

export default function MissionsPage() {
  const { missions = [], isLoading, refetch } = useMissions();
  const { goals = [], isLoading: goalsLoading } = useGoals();
  const createMission = useCreateMission();
  const addToast = useUIStore((s) => s.addToast);

  const [newTitle, setNewTitle] = React.useState("");
  const [newDesc, setNewDesc] = React.useState("");

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;
    const result = await createMission.mutate({
      title: newTitle.trim(),
      description: newDesc.trim() || undefined,
    });
    if (result.error) {
      addToast({ type: "error", message: result.error });
    } else {
      addToast({ type: "success", message: "Mission created" });
      setNewTitle("");
      setNewDesc("");
      refetch();
    }
  };

  return (
    <div className="h-full min-h-0 overflow-y-auto">
      <div className="mx-auto max-w-5xl space-y-6 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight text-foreground">
              <Target className="text-accent" size={22} /> Missions
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Workflow missions autonomes exécutées par ETHAN Core.
            </p>
          </div>
          <Button variant="outline" size="sm" className="gap-2" onClick={() => refetch()}>
            <RefreshCw size={14} /> Rafraîchir
          </Button>
        </div>

        <Card variant="outlined">
          <CardHeader>
            <CardTitle className="text-sm font-semibold uppercase tracking-wider text-foreground-secondary">
              Nouvelle mission
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="flex flex-wrap gap-3">
              <Input
                placeholder="Titre de la mission"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                className="min-w-[200px] flex-1"
                aria-label="Titre de la mission"
              />
              <Input
                placeholder="Description (optionnel)"
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
                className="min-w-[240px] flex-[2]"
                aria-label="Description de la mission"
              />
              <Button type="submit" size="md" className="gap-2" disabled={!newTitle.trim() || createMission.isLoading}>
                <Plus size={15} /> Créer
              </Button>
            </form>
          </CardContent>
        </Card>

        {isLoading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} variant="rectangle" className="h-20 w-full" />
            ))}
          </div>
        ) : (missions as Mission[]).length > 0 ? (
          <div className="space-y-3">
            {(missions as Mission[]).map((mission: Mission) => {
              const stepsTotal = mission.steps_total || 0;
              const stepsCompleted = mission.steps_completed || 0;
              const progress = stepsTotal > 0 ? Math.round((stepsCompleted / stepsTotal) * 100) : 0;
              return (
                <Card key={mission.id} variant="outlined" className="transition-colors hover:border-line-3">
                  <CardContent className="space-y-3">
                    <div className="flex items-center justify-between gap-3">
                      <div className="min-w-0">
                        <h3 className="truncate font-medium text-foreground">{mission.title}</h3>
                        {mission.description && (
                          <p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">{mission.description}</p>
                        )}
                      </div>
                      <Badge variant={statusBadge[mission.status] || "default"} dot className="shrink-0">
                        {mission.status}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-3">
                      <Progress value={progress} className="h-1.5 flex-1" />
                      <span className="shrink-0 font-mono text-xs text-muted-foreground">
                        {progress}% · {stepsCompleted}/{stepsTotal} étapes
                      </span>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        ) : (
          <Card variant="outlined">
            <CardContent className="flex flex-col items-center justify-center gap-2 py-12 text-center text-muted-foreground">
              <Target size={40} className="opacity-30" />
              <p className="text-sm">Aucune mission. Créez-en une ci-dessus.</p>
            </CardContent>
          </Card>
        )}

        <div className="pt-2">
          <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-foreground-secondary">
            <CheckSquare size={15} /> Objectifs stratégiques
          </h2>
          {goalsLoading ? (
            <Skeleton variant="rectangle" className="h-16 w-full" />
          ) : (goals as Goal[]).length > 0 ? (
            <div className="grid gap-3 md:grid-cols-2">
              {(goals as Goal[]).map((goal: Goal) => (
                <Card key={goal.id} variant="outlined" className="p-4">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="truncate text-sm font-medium text-foreground">{goal.title}</div>
                      {goal.description && (
                        <p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">{goal.description}</p>
                      )}
                    </div>
                    <span
                      className={`inline-flex shrink-0 items-center rounded-full px-2 py-0.5 text-[10px] font-medium capitalize ${
                        goal.status === "active" ? "bg-green-soft text-green" : "bg-line-1 text-foreground-tertiary"
                      }`}
                    >
                      {goal.status}
                    </span>
                  </div>
                </Card>
              ))}
            </div>
          ) : (
            <p className="text-xs text-muted-foreground">Aucun objectif stratégique défini.</p>
          )}
        </div>
      </div>
    </div>
  );
}
