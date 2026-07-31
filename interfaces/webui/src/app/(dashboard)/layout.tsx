"use client";

import * as React from "react";
import { AnimatePresence, motion } from "framer-motion";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { WebSocketProvider } from "@/core/providers/websocket-provider";
import { Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";
import { GlobalShortcuts } from "@/components/layout/global-shortcuts";
import { GlobalCommandPalette } from "@/components/layout/global-command-palette";
import { GlobalInspector } from "@/components/layout/global-inspector";
import { MissionControlOverlay } from "@/components/layout/mission-control-overlay";
import { AtmosphereLayer } from "@/components/layout/atmosphere-layer";
import { useUIStore } from "@/core/store/ui.store";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { sidebarExpanded } = useUIStore();
  const pathname = usePathname();
  const isAssistantRoute = pathname === "/assistant";

  return (
    <WebSocketProvider>
      <div className="flex h-[100dvh] min-h-0 overflow-hidden">
        <GlobalShortcuts />
        <GlobalCommandPalette />
        <GlobalInspector />
        <MissionControlOverlay />
        <AtmosphereLayer />
        <Sidebar />
        <div
          className={cn(
            "relative z-10 flex min-w-0 flex-1 flex-col overflow-hidden transition-[padding] duration-300",
            sidebarExpanded ? "pl-16 md:pl-64" : "pl-16"
          )}
          style={{ paddingTop: "env(safe-area-inset-top)" }}
        >
          <Topbar />
          <main
            className={cn(
              "relative min-h-0 flex-1",
              isAssistantRoute ? "overflow-hidden p-0" : "overflow-y-auto p-6"
            )}
          >
            <AnimatePresence mode="wait" initial={false}>
              <motion.div
                key={pathname}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.25, ease: [0.2, 0.8, 0.25, 1] }}
                className={isAssistantRoute ? "h-full min-h-0" : "min-h-[60vh]"}
              >
                {children}
              </motion.div>
            </AnimatePresence>
          </main>
        </div>
      </div>
    </WebSocketProvider>
  );
}
