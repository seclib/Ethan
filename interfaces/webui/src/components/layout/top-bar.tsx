"use client";

import { useStore, getBreadcrumbs, PAGE_TITLES, type AppPage } from "@/lib/store";

const STATUS_LABELS: Record<string, string> = {
  open: "ONLINE",
  connecting: "CONNECTING",
  closed: "OFFLINE",
};

export function TopBar() {
  const { sidebarOpen, toggleSidebar, currentPage, setPage, theme, toggleTheme } = useStore();
  const title = PAGE_TITLES[currentPage];

  return (
    <header className="top-bar">
      <div className="top-bar-left">
        <button className="top-bar-btn" onClick={toggleSidebar} title="Toggle sidebar (⌘B)">
          {sidebarOpen ? "←" : "→"}
        </button>
        <span className="top-bar-brand">◆ ETHAN</span>
        <span className="top-bar-status open">
          <span className="status-dot" />
          ONLINE
        </span>
      </div>

      {/* Breadcrumb simple */}
      <nav className="top-bar-breadcrumbs">
        <span className="bc-current">{title}</span>
      </nav>

      <div className="top-bar-right">
        <span className="top-bar-uptime">⏱ 14h22</span>
        <button className="top-bar-btn" onClick={toggleTheme} title="Toggle theme">
          {theme === "dark" ? "☀" : "☾"}
        </button>
      </div>
    </header>
  );
}
