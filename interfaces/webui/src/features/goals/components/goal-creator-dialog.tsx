"use client";

import * as React from "react";
import { Dialog } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { useCreateGoal } from "@/features/goals/hooks/use-goals";
import { X, Plus, AlertCircle } from "lucide-react";

interface GoalCreatorDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function GoalCreatorDialog({ open, onOpenChange }: GoalCreatorDialogProps) {
  const { mutate: createGoal, isLoading: isCreating } = useCreateGoal();
  const [title, setTitle] = React.useState("");
  const [description, setDescription] = React.useState("");
  const [priority, setPriority] = React.useState<"low" | "medium" | "high" | "critical">("medium");
  
  // Tasks list
  const [tasks, setTasks] = React.useState([{ id: 1, title: "" }]);

  const handleAddTask = () => {
    setTasks([...tasks, { id: Date.now(), title: "" }]);
  };

  const handleRemoveTask = (id: number) => {
    setTasks(tasks.filter((t) => t.id !== id));
  };

  const handleTaskChange = (id: number, val: string) => {
    setTasks(tasks.map((t) => (t.id === id ? { ...t, title: val } : t)));
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!title.trim()) return;

    try {
      const validTasks = tasks.map(t => t.title.trim()).filter(Boolean);
      await createGoal({
        title,
        description,
        priority,
        // API could be adapted to accept tasks array if needed
        // tasks: validTasks 
      });
      onOpenChange(false);
      setTitle("");
      setDescription("");
      setPriority("medium");
      setTasks([{ id: 1, title: "" }]);
    } catch (error) {
      console.error("Failed to create goal", error);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange} size="lg" title="Create New Goal">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Core details */}
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-foreground-tertiary uppercase tracking-wider mb-2">
              Goal Title <span className="text-destructive">*</span>
            </label>
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Optimize CI/CD Pipeline"
              className="bg-elevated border-line-2"
              autoFocus
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-foreground-tertiary uppercase tracking-wider mb-2">
              Description
            </label>
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Detailed explanation of the goal..."
              className="bg-elevated border-line-2 resize-none"
              rows={3}
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-foreground-tertiary uppercase tracking-wider mb-2">
              Priority
            </label>
            <div className="flex gap-2">
              {(["low", "medium", "high", "critical"] as const).map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => setPriority(p)}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium capitalize transition-colors border ${
                    priority === p 
                      ? "border-accent bg-accent/10 text-accent" 
                      : "border-line-2 bg-background hover:bg-accent/5 text-foreground-secondary"
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Tasks breakdown */}
        <div className="space-y-3 pt-4 border-t border-line-1">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold text-foreground-tertiary uppercase tracking-wider">
              Sub-tasks Breakdown
            </label>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleAddTask}
              className="h-7 text-xs px-2 gap-1"
            >
              <Plus size={14} /> Add Task
            </Button>
          </div>

          <div className="space-y-2 max-h-[150px] overflow-y-auto custom-scrollbar pr-2">
            {tasks.map((task, index) => (
              <div key={task.id} className="flex items-center gap-2">
                <Badge variant="dim" className="w-6 h-6 flex items-center justify-center p-0 shrink-0">
                  {index + 1}
                </Badge>
                <Input
                  value={task.title}
                  onChange={(e) => handleTaskChange(task.id, e.target.value)}
                  placeholder="Task description..."
                  className="bg-elevated border-line-2 h-8 text-sm"
                />
                <button
                  type="button"
                  onClick={() => handleRemoveTask(task.id)}
                  className="p-1.5 text-foreground-tertiary hover:text-destructive transition-colors shrink-0"
                >
                  <X size={14} />
                </button>
              </div>
            ))}
            {tasks.length === 0 && (
              <div className="text-center p-4 border border-dashed border-line-2 rounded-lg text-foreground-tertiary text-xs flex items-center justify-center gap-2">
                <AlertCircle size={14} /> No sub-tasks defined.
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 pt-4 border-t border-line-1">
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" disabled={isCreating || !title.trim()}>
            {isCreating ? "Creating..." : "Create Goal"}
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
