"use client";

import * as React from "react";
import { Dialog } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { useCreateMission } from "@/features/missions/hooks/use-missions";
import type { Mission, Step } from "@/types";

interface MissionCreatorDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function MissionCreatorDialog({ open, onOpenChange }: MissionCreatorDialogProps) {
  const { mutate: createMission, isLoading: isCreating } = useCreateMission();
  const [title, setTitle] = React.useState("");
  const [description, setDescription] = React.useState("");
  const [steps, setSteps] = React.useState<Partial<Step>[]>([
    { title: "", description: "", status: "pending" as const }
  ]);
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  const addStep = () => {
    setSteps([...steps, { title: "", description: "", status: "pending" as const }]);
  };

  const removeStep = (index: number) => {
    setSteps(steps.filter((_, i) => i !== index));
  };

  const updateStep = (index: number, field: keyof Step, value: any) => {
    setSteps(steps.map((step, i) => i === index ? { ...step, [field]: value } : step));
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      // In a real app we'd pass steps to the API as well
      await createMission({ title, description });
      onOpenChange(false);
      
      // Reset form
      setTitle("");
      setDescription("");
      setSteps([{ title: "", description: "", status: "pending" as const }]);
    } catch (error) {
      console.error("Failed to create mission:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
        <div className="bg-background border rounded-lg shadow-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold">Create New Mission</h2>
            <Button variant="ghost" size="sm" onClick={() => onOpenChange(false)}>
              ✕
            </Button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Mission Details */}
            <div className="space-y-4">
              <div>
                <label htmlFor="title" className="block text-sm font-medium mb-2">
                  Mission Title *
                </label>
                <Input
                  id="title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Enter mission title..."
                  required
                />
              </div>

              <div>
                <label htmlFor="description" className="block text-sm font-medium mb-2">
                  Description
                </label>
                <Textarea
                  id="description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe the mission objective..."
                  rows={3}
                />
              </div>
            </div>

            {/* Steps */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <label className="block text-sm font-medium">Steps</label>
                <Button type="button" variant="outline" size="sm" onClick={addStep}>
                  + Add Step
                </Button>
              </div>

              <div className="space-y-3">
                {steps.map((step, index) => (
                  <div key={index} className="border rounded-lg p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <Badge variant="info">Step {index + 1}</Badge>
                      {steps.length > 1 && (
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => removeStep(index)}
                          className="text-destructive"
                        >
                          Remove
                        </Button>
                      )}
                    </div>

                    <Input
                      placeholder="Step title..."
                      value={step.title}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => updateStep(index, "title", e.target.value)}
                      required
                    />

                    <Textarea
                      placeholder="Step description..."
                      value={step.description}
                      onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => updateStep(index, "description", e.target.value)}
                      rows={2}
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-end gap-3 pt-4 border-t">
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting || !title}>
                {isSubmitting ? "Creating..." : "Create Mission"}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </Dialog>
  );
}