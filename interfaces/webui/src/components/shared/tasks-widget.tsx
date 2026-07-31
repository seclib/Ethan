"use client";

import * as React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { CheckCircle2, Circle, Clock, AlertTriangle, Play } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Task } from "@/types";

interface TasksWidgetProps {
  tasks: Task[];
  title?: string;
  maxItems?: number;
  onTaskClick?: (task: Task) => void;
}

const statusConfig: Record<string, { icon: React.ElementType; color: "success" | "warning" | "error" | "default" | "info" | "dim"; label: string }> = {
  pending: { icon: Circle, color: "dim", label: "Pending" },
  running: { icon: Clock, color: "info", label: "Running" },
  completed: { icon: CheckCircle2, color: "success", label: "Completed" },
  failed: { icon: AlertTriangle, color: "error", label: "Failed" },
  cancelled: { icon: Circle, color: "default", label: "Cancelled" },
  skipped: { icon: Circle, color: "default", label: "Skipped" },
};

export function TasksWidget({ tasks, title = "Tasks", maxItems = 5, onTaskClick }: TasksWidgetProps) {
  const visibleTasks = tasks.slice(0, maxItems);
  const completedCount = tasks.filter((t) => t.status === "completed").length;
  const progress = tasks.length > 0 ? Math.round((completedCount / tasks.length) * 100) : 0;

  return (
    <Card variant="outlined">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-base">{title}</CardTitle>
        <div className="flex items-center gap-2">
          <Badge variant="default" className="text-xs">
            {completedCount}/{tasks.length}
          </Badge>
          <Button size="sm" variant="ghost" className="h-7 w-7 p-0">
            <Play size={14} />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <Progress value={progress} className="h-2" />
        
        <div className="space-y-2">
          {visibleTasks.map((task) => {
            const config = statusConfig[task.status] || statusConfig.pending;
            const Icon = config.icon;
            
            return (
              <div
                key={task.id}
                className="flex items-center gap-3 rounded-md border bg-card p-3 transition-all hover:bg-accent/5 cursor-pointer"
                onClick={() => onTaskClick?.(task)}
              >
                <Icon size={16} className={cn(
                  "shrink-0",
                  task.status === "completed" && "text-green-500",
                  task.status === "failed" && "text-red-500",
                  task.status === "running" && "text-blue-500 animate-pulse",
                  task.status === "pending" && "text-muted-foreground"
                )} />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate">{task.title}</div>
                  {task.description && (
                    <div className="text-xs text-muted-foreground truncate">{task.description}</div>
                  )}
                </div>
                <Badge variant={config.color} className="text-[10px] shrink-0">
                  {config.label}
                </Badge>
              </div>
            );
          })}
        </div>

        {tasks.length > maxItems && (
          <div className="text-center">
            <Button variant="ghost" size="sm" className="text-xs">
              View all {tasks.length} tasks
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

