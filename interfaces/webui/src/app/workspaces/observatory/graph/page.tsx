"use client";

import { GraphView } from "@/components/features/observatory/graph/graph-view";

export default function ObservatoryGraphPage() {
  return (
    <div className="flex h-full min-h-0 flex-col">
      <GraphView />
    </div>
  );
}
