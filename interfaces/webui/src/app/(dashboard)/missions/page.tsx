"use client";

import * as React from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useMissions } from "@/hooks/use-missions";
import { getStatusColor } from "@/lib/utils";

export default function MissionsPage() {
  const { missions, isLoading, error } = useMissions();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Missions</h1>
          <p className="text-muted-foreground mt-2">Loading missions...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Missions</h1>
          <p className="text-destructive mt-2">Error: {error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Missions</h1>
        <p className="text-muted-foreground mt-2">
          Active and completed missions with step verification
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card className="p-6">
          <h3 className="font-semibold mb-2">Active Missions</h3>
          <p className="text-2xl font-bold">
            {missions.filter((m) => m.status === "running" || m.status === "planning").length}
          </p>
          <p className="text-sm text-muted-foreground">Currently executing</p>
        </Card>
        <Card className="p-6">
          <h3 className="font-semibold mb-2">Total Missions</h3>
          <p className="text-2xl font-bold">{missions.length}</p>
          <p className="text-sm text-muted-foreground">All time</p>
        </Card>
      </div>

      <Card>
        <div className="p-6">
          <h3 className="font-semibold mb-4">Mission List</h3>
          {missions.length === 0 ? (
            <p className="text-sm text-muted-foreground">No missions yet</p>
          ) : (
            <div className="space-y-3">
              {missions.map((mission) => (
                <div
                  key={mission.id}
                  className="flex items-center justify-between p-3 rounded-lg border"
                >
                  <div className="flex-1">
                    <h4 className="font-medium">{mission.title}</h4>
                    <p className="text-sm text-muted-foreground line-clamp-1">
                      {mission.description}
                    </p>
                  </div>
                  <Badge variant={getStatusColor(mission.status)}>
                    {mission.status}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}