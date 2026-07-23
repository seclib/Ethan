"use client";

import * as React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useGoals } from "@/features/goals/hooks/use-goals";
import type { Goal, Task } from "@/types";
import { getStatusColor, getPriorityColor } from "@/lib/utils";

export default function GoalsPage() {
  const { goals, isLoading, error } = useGoals();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Goals</h1>
          <p className="text-foreground-secondary mt-2">Loading goals...</p>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          {[1, 2, 3].map((i) => (
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
          <h1 className="text-3xl font-bold text-foreground">Goals</h1>
          <p className="text-error-600 mt-2">Error: {error}</p>
        </div>
      </div>
    );
  }

  const activeGoals = goals.filter((g: Goal) => g.status === "active").length;
  const pendingTasks = goals.reduce((sum: number, g: Goal) => sum + g.tasks.filter((t: Task) => t.status === "pending").length, 0);
  const completedGoals = goals.filter((g: Goal) => g.status === "completed").length;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Goals</h1>
        <p className="text-foreground-secondary mt-2">
          Active goals and task decomposition
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card variant="elevated">
          <CardHeader>
            <CardTitle>Active Goals</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-foreground">{activeGoals}</p>
            <p className="text-sm text-foreground-tertiary mt-1">Currently pursuing</p>
          </CardContent>
        </Card>
        <Card variant="elevated">
          <CardHeader>
            <CardTitle>Pending Tasks</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-foreground">{pendingTasks}</p>
            <p className="text-sm text-foreground-tertiary mt-1">Across all goals</p>
          </CardContent>
        </Card>
        <Card variant="elevated">
          <CardHeader>
            <CardTitle>Completed</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-foreground">{completedGoals}</p>
            <p className="text-sm text-foreground-tertiary mt-1">Goals achieved</p>
          </CardContent>
        </Card>
      </div>

      <Card variant="outlined">
        <CardHeader>
          <CardTitle>Goal List</CardTitle>
        </CardHeader>
        <CardContent>
          {goals.length === 0 ? (
            <p className="text-sm text-foreground-tertiary">No goals yet</p>
          ) : (
            <div className="space-y-3">
              {goals.map((goal: Goal) => (
                <div
                  key={goal.id}
                  className="flex items-start justify-between p-3 rounded-lg border border-line-1 hover:border-line-2 transition-colors duration-100"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-medium text-foreground">{goal.title}</h4>
                      <Badge variant={getPriorityColor(goal.priority)}>
                        {goal.priority}
                      </Badge>
                    </div>
                    <p className="text-sm text-foreground-tertiary line-clamp-1">
                      {goal.description}
                    </p>
                    <div className="flex gap-2 mt-1 text-xs text-foreground-tertiary">
                      <span>Tasks: {goal.tasks.length}</span>
                      <span>•</span>
                      <span>Created: {new Date(goal.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <Badge variant={getStatusColor(goal.status)} dot>
                    {goal.status}
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