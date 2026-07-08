"use client";

import * as React from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useGoals } from "@/hooks/use-goals";
import { getStatusColor, getPriorityColor } from "@/lib/utils";

export default function GoalsPage() {
  const { goals, isLoading, error } = useGoals();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Goals</h1>
          <p className="text-muted-foreground mt-2">Loading goals...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Goals</h1>
          <p className="text-destructive mt-2">Error: {error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Goals</h1>
        <p className="text-muted-foreground mt-2">
          Active goals and task decomposition
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="p-6">
          <h3 className="font-semibold">Active Goals</h3>
          <p className="text-2xl font-bold mt-2">
            {goals.filter((g) => g.status === "active").length}
          </p>
          <p className="text-sm text-muted-foreground">Currently pursuing</p>
        </Card>
        <Card className="p-6">
          <h3 className="font-semibold">Pending Tasks</h3>
          <p className="text-2xl font-bold mt-2">
            {goals.reduce((sum, g) => sum + g.tasks.filter((t) => t.status === "pending").length, 0)}
          </p>
          <p className="text-sm text-muted-foreground">Across all goals</p>
        </Card>
        <Card className="p-6">
          <h3 className="font-semibold">Completed</h3>
          <p className="text-2xl font-bold mt-2">
            {goals.filter((g) => g.status === "completed").length}
          </p>
          <p className="text-sm text-muted-foreground">Goals achieved</p>
        </Card>
      </div>

      <Card>
        <div className="p-6">
          <h3 className="font-semibold mb-4">Goal List</h3>
          {goals.length === 0 ? (
            <p className="text-sm text-muted-foreground">No goals yet</p>
          ) : (
            <div className="space-y-3">
              {goals.map((goal) => (
                <div
                  key={goal.id}
                  className="flex items-start justify-between p-3 rounded-lg border"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-medium">{goal.title}</h4>
                      <Badge variant={getPriorityColor(goal.priority) as any}>
                        {goal.priority}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground line-clamp-1">
                      {goal.description}
                    </p>
                    <div className="flex gap-2 mt-1 text-xs text-muted-foreground">
                      <span>Tasks: {goal.tasks.length}</span>
                      <span>•</span>
                      <span>Created: {new Date(goal.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <Badge variant={getStatusColor(goal.status)}>
                    {goal.status}
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