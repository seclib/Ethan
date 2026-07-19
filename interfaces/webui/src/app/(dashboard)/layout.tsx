import * as React from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";
import { GlobalShortcuts } from "@/components/layout/global-shortcuts";
import { GlobalCommandPalette } from "@/components/layout/global-command-palette";
import { GlobalInspector } from "@/components/layout/global-inspector";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen overflow-hidden">
      <GlobalShortcuts />
      <GlobalCommandPalette />
      <GlobalInspector />
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Topbar />
        <main className="flex-1 overflow-y-auto p-6 relative">
          {children}
        </main>
      </div>
    </div>
  );
}