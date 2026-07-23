"use client";

import * as React from "react";
import { Dialog } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { useCreateMission } from "@/features/missions/hooks/use-missions";
import { useUIStore } from "@/core/store/ui.store";
import type { Step } from "@/types";

import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { GripVertical, X, Plus, DollarSign } from "lucide-react";

interface MissionCreatorDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

type SortableStepItem = Partial<Step> & { id: string };

function SortableStep({
  step,
  index,
  updateStep,
  removeStep,
  canRemove,
}: {
  step: SortableStepItem;
  index: number;
  updateStep: (id: string, field: keyof Step, value: any) => void;
  removeStep: (id: string) => void;
  canRemove: boolean;
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: step.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    zIndex: isDragging ? 50 : "auto",
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`border border-line-2 bg-elevated/80 backdrop-blur-sm rounded-lg p-4 space-y-3 relative group transition-colors ${
        isDragging ? "shadow-2xl opacity-90 border-accent/50" : "hover:border-line-3"
      }`}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div
            {...attributes}
            {...listeners}
            className="cursor-grab active:cursor-grabbing text-foreground-tertiary hover:text-foreground p-1 -ml-2 rounded-md hover:bg-accent/10 transition-colors"
          >
            <GripVertical size={16} />
          </div>
          <Badge variant="info" className="bg-accent/10 text-accent border-accent/20">Step {index + 1}</Badge>
        </div>
        {canRemove && (
          <button
            type="button"
            onClick={() => removeStep(step.id)}
            className="text-foreground-tertiary hover:text-destructive transition-colors p-1"
          >
            <X size={16} />
          </button>
        )}
      </div>

      <Input
        placeholder="Operation Directive..."
        value={step.title}
        onChange={(e) => updateStep(step.id, "title", e.target.value)}
        className="bg-background border-line-2 text-sm font-mono"
        required
      />

      <Textarea
        placeholder="Detailed execution context..."
        value={step.description}
        onChange={(e) => updateStep(step.id, "description", e.target.value)}
        className="bg-background border-line-2 resize-none text-sm"
        rows={2}
      />
    </div>
  );
}

export function MissionCreatorDialog({ open, onOpenChange }: MissionCreatorDialogProps) {
  const { mutate: createMission, isLoading: isCreating } = useCreateMission();
  const { addToast } = useUIStore();
  
  const [title, setTitle] = React.useState("");
  const [description, setDescription] = React.useState("");
  const [budget, setBudget] = React.useState<number>(5); // $5 par defaut
  const [steps, setSteps] = React.useState<SortableStepItem[]>([
    { id: "step-1", title: "", description: "", status: "pending" as const }
  ]);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      setSteps((items) => {
        const oldIndex = items.findIndex((i) => i.id === active.id);
        const newIndex = items.findIndex((i) => i.id === over.id);
        return arrayMove(items, oldIndex, newIndex);
      });
    }
  };

  const addStep = () => {
    setSteps([...steps, { id: `step-${Date.now()}`, title: "", description: "", status: "pending" as const }]);
  };

  const removeStep = (id: string) => {
    setSteps(steps.filter((s) => s.id !== id));
  };

  const updateStep = (id: string, field: keyof Step, value: any) => {
    setSteps(steps.map((step) => step.id === id ? { ...step, [field]: value } : step));
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (budget > 100) {
      addToast({
        type: "error",
        message: "Budget exceeds maximum threshold ($100). Approval required.",
      });
      return;
    }

    try {
      // In a real app we'd pass steps & budget to the API as well
      await createMission({ title, description });
      
      addToast({
        type: "success",
        message: "Mission initialized in kernel.",
      });
      
      onOpenChange(false);
      
      // Reset form
      setTitle("");
      setDescription("");
      setBudget(5);
      setSteps([{ id: `step-${Date.now()}`, title: "", description: "", status: "pending" as const }]);
    } catch (error) {
      addToast({
        type: "error",
        message: "Failed to initialize mission.",
      });
      console.error("Failed to create mission:", error);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange} size="lg" title="Initialize Mission">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Core Mission Params */}
        <div className="space-y-4">
          <div>
            <label htmlFor="title" className="block text-xs font-semibold text-foreground-tertiary uppercase tracking-wider mb-2">
              Mission Title *
            </label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Scrape and analyze competitor pricing"
              className="bg-elevated border-line-2 font-mono"
              autoFocus
              required
            />
          </div>

          <div className="grid grid-cols-4 gap-4">
            <div className="col-span-3">
              <label htmlFor="description" className="block text-xs font-semibold text-foreground-tertiary uppercase tracking-wider mb-2">
                Operational Context
              </label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe the mission objective and constraints..."
                className="bg-elevated border-line-2 resize-none"
                rows={2}
              />
            </div>
            
            <div className="col-span-1">
              <label htmlFor="budget" className="block text-xs font-semibold text-foreground-tertiary uppercase tracking-wider mb-2">
                Max Budget
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <DollarSign size={14} className="text-muted-foreground" />
                </div>
                <Input
                  id="budget"
                  type="number"
                  min={1}
                  max={500}
                  value={budget}
                  onChange={(e) => setBudget(Number(e.target.value))}
                  className="bg-elevated border-line-2 pl-8 font-mono"
                  required
                />
              </div>
            </div>
          </div>
        </div>

        {/* Drag and Drop Steps */}
        <div className="space-y-3 pt-4 border-t border-line-1">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold text-foreground-tertiary uppercase tracking-wider">
              Execution Pipeline
            </label>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={addStep}
              className="h-7 text-xs px-2 gap-1 border-dashed"
            >
              <Plus size={14} /> Add Step
            </Button>
          </div>

          <div className="max-h-[350px] overflow-y-auto custom-scrollbar pr-2 py-2">
            <DndContext
              sensors={sensors}
              collisionDetection={closestCenter}
              onDragEnd={handleDragEnd}
            >
              <SortableContext
                items={steps.map(s => s.id)}
                strategy={verticalListSortingStrategy}
              >
                <div className="space-y-3">
                  {steps.map((step, index) => (
                    <SortableStep
                      key={step.id}
                      step={step}
                      index={index}
                      updateStep={updateStep}
                      removeStep={removeStep}
                      canRemove={steps.length > 1}
                    />
                  ))}
                </div>
              </SortableContext>
            </DndContext>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-line-1 mt-6">
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Abort
          </Button>
          <Button type="submit" variant="primary" disabled={isCreating || !title.trim()}>
            {isCreating ? "Initializing..." : "Launch Mission"}
          </Button>
        </div>
      </form>
    </Dialog>
  );
}