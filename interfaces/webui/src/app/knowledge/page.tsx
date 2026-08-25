"use client";

import * as React from "react";
import { KnowledgeWorkspace } from "@/components/features/knowledge/components/knowledge-workspace";

export default function KnowledgePage() {
  return (
    <div className="flex h-full min-h-0 flex-col">
      <KnowledgeWorkspace />
    </div>
  );
}