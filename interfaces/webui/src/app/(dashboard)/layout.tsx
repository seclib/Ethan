"use client";

import * as React from "react";
import { AnimatePresence, motion } from "framer-motion";
import { usePathname } from "next/navigation";
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

  return (
    <div className="flex h-screen overflow-hidden">
      <GlobalShortcuts />
      <GlobalCommandPalette />
      <GlobalInspector />
      <MissionControlOverlay />
      <AtmosphereLayer />
      <Sidebar />
      <div
        className="flex flex-1 flex-col overflow-hidden transition-all duration-300"
        style={{
          paddingLeft: sidebarExpanded ? '16rem' : '4rem',
          paddingTop: 'env(safe-area-inset-top)',
          position: 'relative',
          zIndex: 10,
        }}
      >
        <Topbar />
        <main className="flex-1 overflow-y-auto p-6 relative">
          <AnimatePresence mode="wait">
            <motion.div
              key={pathname}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.25, ease: [0.2, 0.8, 0.25, 1] }}
              className="min-h-[60vh]"
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}