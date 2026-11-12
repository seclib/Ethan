"use client";

import { Suspense, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ToolsHub } from "@/components/features/tools/components/tools-hub";

function ToolsPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const isMcpRedirect = searchParams.get("view") === "mcp";

  useEffect(() => {
    // L'ancienne surface MCP de /tools a migré vers Workspaces : on conserve
    // les liens historiques (`/tools?view=mcp`) en les redirigeant côté client.
    if (isMcpRedirect) {
      router.replace("/workspaces/mcp");
    }
  }, [isMcpRedirect, router]);

  if (isMcpRedirect) {
    return null;
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <ToolsHub />
    </div>
  );
}

export default function ToolsPage() {
  // Next 16 exige une frontière Suspense autour de `useSearchParams`, sinon
  // le prérendu statique de la route échoue au build.
  return (
    <Suspense fallback={null}>
      <ToolsPageContent />
    </Suspense>
  );
}
