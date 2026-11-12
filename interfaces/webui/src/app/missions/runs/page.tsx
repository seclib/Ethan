"use client";

/**
 * Mission → Runs — historique d'exécution.
 *
 * Aujourd'hui, l'historique d'exécution réel d'ETHAN = les missions du Core
 * (/v1/missions) avec leurs statuts et progression. Cette page les présente
 * comme des runs. Lorsque le moteur de workflows existera dans Runtime,
 * les runs de workflows s'ajouteront ici — la page ne fabrique aucune donnée.
 */

import * as React from "react";
import Link from "next/link";
import { useMissions } from "@/components/features/missions/hooks/use-missions";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { History, Target } from "lucide-react";
import type { Mission } from "@/types";

const statusBadge: Record<string, "success" | "warning" | "error" | "info" | "dim" | "default"> = {
  running: "success",
  planning: "info",
  paused: "warning",
  failed: "error",
  pending: "default",
  completed: "success",
  killed: "error",
};

function formatDate(value?: string): string {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

export default function MissionRunsPage() {
  const { missions = [], isLoading, error } = useMissions();

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="flex items-center gap-2 text-lg font-semibold text-foreground">
            <History size={17} className="text-accent" aria-hidden="true" /> Runs
          </h2>
          <p className="mt-0.5 text-sm text-muted-foreground">
            Historique d&apos;exécution — missions remontées par ETHAN Core.
          </p>
        </div>
      </div>

      {error && (
        <Card variant="outlined">
          <CardContent className="text-sm text-destructive">
            Impossible de récupérer les runs depuis le Core : {error}
          </CardContent>
        </Card>
      )}

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} variant="rectangle" className="h-16 w-full" />
          ))}
        </div>
      ) : missions.length === 0 ? (
        <Card variant="outlined">
          <CardContent className="flex flex-col items-center justify-center gap-2 py-12 text-center text-muted-foreground">
            <History size={40} className="opacity-30" aria-hidden="true" />
            <p className="text-sm">Aucun run. Les exécutions de missions apparaîtront ici.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {(missions as Mission[]).map((mission: Mission) => {
            const stepsTotal = mission.steps_total || 0;
            const stepsCompleted = mission.steps_completed || 0;
            const progress = stepsTotal > 0 ? Math.round((stepsCompleted / stepsTotal) * 100) : 0;
            const done = mission.status === "completed" || mission.status === "failed" || mission.status === "killed";
            return (
              <Card key={mission.id} variant="outlined" className="transition-colors hover:border-line-3">
                <CardContent className="space-y-2">
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex min-w-0 items-center gap-2">
                      <Target size={15} className="shrink-0 text-accent" aria-hidden="true" />
                      <span className="truncate font-medium text-foreground">{mission.title}</span>
                    </div>
                    <Badge variant={statusBadge[mission.status] || "default"} dot className="shrink-0">
                      {mission.status}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-3">
                    <Progress value={progress} className="h-1.5 flex-1" />
                    <span className="shrink-0 font-mono text-xs text-muted-foreground">
                      {stepsCompleted}/{stepsTotal} étapes
                    </span>
                  </div>
                  <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
                    <span>
                      Démarré : {formatDate(mission.created_at)}
                      {mission.completed_at ? ` · Terminé : ${formatDate(mission.completed_at)}` : ""}
                    </span>
                    <Link
                      href="/missions"
                      className="text-accent-400 underline-offset-2 hover:underline"
                    >
                      {done ? "Voir la mission" : "Suivre dans Overview"}
                    </Link>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}