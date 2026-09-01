"use client";

import * as React from "react";
import { AgentsWorkspace } from "@/components/features/agents/components/agents-workspace";

export default function AgentsPage() {
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <AgentsWorkspace />
    </div>
  );
}