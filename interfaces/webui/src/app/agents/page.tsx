"use client";

import * as React from "react";
import { AgentsWorkspace } from "@/components/features/agents/components/agents-workspace";

export default function AgentsPage() {
  return (
    <div className="flex h-full min-h-0 flex-col">
      <AgentsWorkspace />
    </div>
  );
}