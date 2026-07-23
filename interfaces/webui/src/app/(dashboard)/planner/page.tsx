"use client";

import * as React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Play, Pause, Plus } from "lucide-react";
import { GoalCreatorDialog } from "@/features/goals/components/goal-creator-dialog";

interface Task {
  id: string;
  name: string;
  status: "pending" | "running" | "done" | "failed";
  progress: number;
}

export default function PlannerPage() {
  const [tasks] = React.useState<Task[]>([
    { id: "1", name: "Analyze requirements", status: "done", progress: 100 },
    { id: "2", name: "Design solution", status: "running", progress: 60 },
    { id: "3", name: "Implement", status: "pending", progress: 0 },
    { id: "4", name: "Test", status: "pending", progress: 0 },
  ]);

  const [creatorOpen, setCreatorOpen] = React.useState(false);

  const statusColor = { pending: "dim", running: "info", done: "success", failed: "error" } as const;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Planner</h1>
          <p className="text-foreground-secondary mt-2">Task orchestration DAG</p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" icon={<Pause className="w-4 h-4" />}>Pause</Button>
          <Button variant="secondary" icon={<Play className="w-4 h-4" />}>Run</Button>
          <Button variant="primary" icon={<Plus className="w-4 h-4" />} onClick={() => setCreatorOpen(true)}>New Goal</Button>
        </div>
      </div>

      <div className="space-y-3">
        {tasks.map((task) => (
          <Card key={task.id}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm">{task.name}</CardTitle>
                <Badge variant={statusColor[task.status]} size="sm" dot>{task.status}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <Progress value={task.progress} size="sm" variant={task.status === "failed" ? "error" : "default"} />
            </CardContent>
          </Card>
        ))}
      </div>

      <GoalCreatorDialog open={creatorOpen} onOpenChange={setCreatorOpen} />
    </div>
  );
}