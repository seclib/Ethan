"use client";

import { useStore } from "@/lib/store";

const SIDEBAR_CONTENT: Record<string, { title: string; items: { label: string; action: string }[] }> = {
  "mission-control": {
    title: "System",
    items: [
      { label: "Kernel Status", action: "kernel" },
      { label: "Active Projects", action: "projects" },
      { label: "Recent Events", action: "events" },
    ],
  },
  goals: {
    title: "Goals",
    items: [
      { label: "All Goals", action: "all" },
      { label: "Active", action: "active" },
      { label: "Pending", action: "pending" },
      { label: "Failed", action: "failed" },
    ],
  },
  memory: {
    title: "Memory",
    items: [
      { label: "Search Facts", action: "search" },
      { label: "Categories", action: "categories" },
      { label: "Graph View", action: "graph" },
      { label: "Timeline", action: "timeline" },
    ],
  },
  skills: {
    title: "Skills",
    items: [
      { label: "Installed", action: "installed" },
      { label: "Lab (New)", action: "lab" },
      { label: "Presets", action: "presets" },
      { label: "Sandbox Test", action: "sandbox" },
    ],
  },
  monitor: {
    title: "Monitor",
    items: [
      { label: "Kernel", action: "kernel" },
      { label: "Modules", action: "modules" },
      { label: "Event Bus", action: "bus" },
      { label: "Logs", action: "logs" },
    ],
  },
  approvals: {
    title: "Governance",
    items: [
      { label: "Pending", action: "pending" },
      { label: "History", action: "history" },
      { label: "Configuration", action: "config" },
    ],
  },
  chat: {
    title: "Chat",
    items: [
      { label: "New Session", action: "new" },
      { label: "History", action: "history" },
      { label: "Settings", action: "settings" },
    ],
  },
};

export function SidebarContext() {
  const { currentPage, sidebarOpen } = useStore();
  const content = SIDEBAR_CONTENT[currentPage];

  if (!sidebarOpen || !content) return null;

  return (
    <aside className="sidebar-context">
      <div className="sidebar-context-title">{content.title}</div>
      <nav className="sidebar-context-nav">
        {content.items.map((item) => (
          <button key={item.action} className="sidebar-context-item">
            {item.label}
          </button>
        ))}
      </nav>
    </aside>
  );
}