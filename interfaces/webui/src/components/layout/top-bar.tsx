"use client";

import { useStore } from "@/lib/store";
import { useWebSocket } from "@/hooks/useWebSocket";

export function TopBar() {
  const { currentPage, setPage, sidebarOpen, toggleSidebar, theme, toggleTheme, approvals } = useStore();
  const { status } = useWebSocket("ws://localhost:8000/ws", "system.health");

  const pages = [
    { id: "mission-control" as const, label: "Mission Control", icon: "◆" },
    { id: "goals" as const, label: "Goals", icon: "◎" },
    { id: "memory" as const, label: "Memory", icon: "◈" },
    { id: "skills" as const, label: "Skills", icon: "⚙" },
    { id: "monitor" as const, label: "Monitor", icon: "◉" },
    { id: "approvals" as const, label: "Approvals", icon: "⚠" },
    { id: "chat" as const, label: "Chat", icon: "💬" },
  ];

  return (
    <header className="top-bar">
      <div className="top-bar-left">
        <button className="top-bar-btn" onClick={toggleSidebar} title="Toggle sidebar">
          ☰
        </button>
        <span className="top-bar-brand">◆ ETHAN</span>
        <span className={`top-bar-status ${status}`}>
          <span className="status-dot" />
          {status === "open" ? "ONLINE" : status === "connecting" ? "CONNECTING" : "OFFLINE"}
        </span>
      </div>

      <nav className="top-bar-nav">
        {pages.map((p) => (
          <button
            key={p.id}
            className={`top-bar-nav-item ${currentPage === p.id ? "active" : ""}`}
            onClick={() => setPage(p.id)}
          >
            {p.icon} {p.label}
            {p.id === "approvals" && approvals.length > 0 && (
              <span className="nav-badge">{approvals.length}</span>
            )}
          </button>
        ))}
      </nav>

      <div className="top-bar-right">
        <button className="top-bar-btn" onClick={toggleTheme} title="Toggle theme">
          {theme === "dark" ? "☀" : "☾"}
        </button>
      </div>
    </header>
  );
}