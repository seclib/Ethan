"use client";

import * as React from "react";
import { KnowledgeHub } from "@/components/features/knowledge/components/knowledge-hub";

export default function KnowledgePage() {
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <KnowledgeHub />
    </div>
  );
}