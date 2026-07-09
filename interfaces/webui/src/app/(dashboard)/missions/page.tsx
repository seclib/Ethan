"use client";

import * as React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useMissions } from "@/hooks/use-missions";
import { getStatusColor } from "@/lib/utils";

export default function MissionsPage() {
  const { missions, isLoading, error } = useMissions();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Missions</h1>
          <p className="text-foreground-secondary mt-2">Loading missions...</p>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          {[1, 2].map((i) => (
            <Card key={i} variant="outlined">
              <CardContent>
                <Skeleton variant="text" lines={3} />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Missions</h1>
          <p className="text-error-600 mt-2">Error: {error}</p>
        </div>
      </div>
    );
  }

  const activeMissions = missions.filter(
    (m: any) => m.status === "running" || m.status === "planning"
  ).length;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Missions</h1>
        <p className="text-foreground-secondary mt-2">
          Active and completed missions with step verification
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card variant="elevated">
          <CardHeader>
            <CardTitle>Active Missions</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-foreground">{activeMissions}</p>
            <p className="text-sm text-foreground-tertiary mt-1">Currently executing</p>
          </CardContent>
        </Card>
        <Card variant="elevated">
          <CardHeader>
            <CardTitle>Total Missions</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-foreground">{missions.length}</p>
            <p className="text-sm text-foreground-tertiary mt-1">All time</p>
          </CardContent>
        </Card>
      </div>

      <Card variant="outlined">
        <CardHeader>
          <CardTitle>Mission List</CardTitle>
        </CardHeader>
        <CardContent>
          {missions.length === 0 ? (
            <p className="text-sm text-foreground-tertiary">No missions yet</p>
          ) : (
            <div className="space-y-3">
              {missions.map((mission: any) => (
                <div
                  key={mission.id}
                  className="flex items-center justify-between p-3 rounded-lg border border-line-1 hover:border-line-2 transition-colors duration-100"
                >
                  <div className="flex-1">
                    <h4 className="font-medium text-foreground">{mission.title}</h4>
                    <p className="text-sm text-foreground-tertiary line-clamp-1">
                      {mission.description}
                    </p>
                  </div>
                  <Badge variant={getStatusColor(mission.status)} dot>
                    {mission.status}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}