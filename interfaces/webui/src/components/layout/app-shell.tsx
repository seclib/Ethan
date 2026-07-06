"use client";

import { usePageTransition } from "@/hooks/usePageTransition";
import { TopBar } from "./top-bar";
import { SidebarContext } from "./sidebar-context";
import { Inspector } from "./inspector";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pageRef = usePageTransition();

  return (
    <div className="app-layout">
      <TopBar />
      <div className="app-layout-body">
        <SidebarContext />
        <main className="app-main" ref={pageRef}>
          {children}
        </main>
        <Inspector />
      </div>
    </div>
  );
}