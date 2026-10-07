"use client";

/**
 * TerminalClient — point d'entrée client du terminal.
 *
 * xterm manipule `self` et le canvas : il ne peut pas être évalué pendant le
 * prerendering Next.js. Ce wrapper isole ce détail — la page reste un Server
 * Component (et garde son `metadata`), le terminal s'hydrate côté client.
 */

import dynamic from "next/dynamic";
import { Spinner } from "@/components/ui/spinner";

const TerminalWorkspace = dynamic(
  () =>
    import("@/components/features/terminal/terminal-workspace").then(
      (module) => module.TerminalWorkspace,
    ),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-full items-center justify-center gap-2 py-12">
        <Spinner />
        <span className="text-sm" style={{ color: "var(--fg-2)" }}>
          Ouverture du terminal…
        </span>
      </div>
    ),
  },
);

export function TerminalClient() {
  return <TerminalWorkspace />;
}