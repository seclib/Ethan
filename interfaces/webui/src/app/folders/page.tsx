"use client";

import * as React from "react";
import { FoldersWorkspace } from "@/components/features/folders/components/folders-workspace";

export default function FoldersPage() {
  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <FoldersWorkspace />
    </div>
  );
}