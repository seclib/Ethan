"use client";

import * as React from "react";
import { DedupWorkspace } from "@/components/features/dedup/dedup-workspace";

export default function DedupPage() {
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <DedupWorkspace />
    </div>
  );
}
