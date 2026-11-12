"use client";

import { CanvasWorkspace } from "@/components/features/observatory/canvas/canvas-workspace";

export default function ObservatoryCanvasPage() {
  return (
    <div className="flex h-full min-h-0 flex-col">
      <CanvasWorkspace />
    </div>
  );
}
