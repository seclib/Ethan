"use client";

import { useStore } from "@/lib/store";
import { cn } from "@/lib/utils";
import { useMediaQuery } from "@/hooks/useMediaQuery";
import {
  LayoutDashboard,
  MessageSquare,
  Radio,
  Target,
  Bug,
  FileText,
  DollarSign,
  Lightbulb,
  CheckSquare,
  FlaskConical,
  Menu,
  X,
  Sun,
  Moon,
} from "lucide-react";

const navItems = [
  { id: "mission-control" as const, label: "Mission Control", icon: LayoutDashboard },
  { id: "chat" as const, label: "Chat", icon: MessageSquare },
  { id: "goals" as const, label: "Goals", icon: Target },
  { id: "memory" as const, label: "Memory", icon: Lightbulb },
  { id: "skills" as const, label: "Skills", icon: FlaskConical },
  { id: "monitor" as const, label: "Monitor", icon: Radio },
  { id: "approvals" as const, label: "Approvals", icon: CheckSquare },
];

export function Sidebar() {
  const isMobile = useMediaQuery("(max-width: 1023px)");
  const { sidebarOpen, toggleSidebar, currentPage, setPage, theme, toggleTheme } = useStore();

  return (
    <>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={toggleSidebar}
        />
      )}

      <aside
        className={cn(
          "fixed left-0 top-0 z-40 flex h-screen flex-col border-r border-border bg-surface transition-all duration-300",
          sidebarOpen ? "w-60 translate-x-0" : "-translate-x-full lg:w-16 lg:translate-x-0"
        )}
      >
        {/* Header */}
        <div className="flex h-14 items-center justify-between border-b border-border px-4">
          {sidebarOpen && (
            <span className="text-lg font-bold text-ethan-400">
              ETHAN <span className="text-text-dim font-normal">OS</span>
            </span>
          )}
          <button
            onClick={toggleSidebar}
            className="rounded-lg p-1.5 text-text-dim hover:bg-surface-2 hover:text-text transition-colors"
          >
            {sidebarOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto p-2 space-y-1">
          {navItems.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setPage(id)}
              className={cn(
                "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                currentPage === id
                  ? "bg-ethan-500/20 text-ethan-400"
                  : "text-text-dim hover:bg-surface-2 hover:text-text"
              )}
              title={sidebarOpen ? undefined : label}
            >
              <Icon size={18} />
              {sidebarOpen && <span>{label}</span>}
            </button>
          ))}
        </nav>

        {/* Footer */}
        <div className="border-t border-border p-3 space-y-2">
          <button
            onClick={toggleTheme}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-text-dim hover:bg-surface-2 hover:text-text transition-colors"
            title={sidebarOpen ? undefined : "Theme"}
          >
            {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
            {sidebarOpen && <span>{theme === "dark" ? "Light mode" : "Dark mode"}</span>}
          </button>
          {sidebarOpen && (
            <p className="text-xs text-text-dim px-3">ETHAN Cognitive OS v0.1</p>
          )}
        </div>
      </aside>
    </>
  );
}