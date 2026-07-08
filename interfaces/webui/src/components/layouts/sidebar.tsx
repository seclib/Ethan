"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/stores/ui.store";

interface SidebarItem {
  id: string;
  label: string;
  icon: string;
  href: string;
  group?: string;
}

const navigationItems: SidebarItem[] = [
  { id: "home", label: "Home", icon: "🏠", href: "/", group: "Core" },
  { id: "agents", label: "Agents", icon: "🤖", href: "/agents", group: "Core" },
  { id: "missions", label: "Missions", icon: "🎯", href: "/missions", group: "Core" },
  { id: "goals", label: "Goals", icon: "🏆", href: "/goals", group: "Core" },
  { id: "memory", label: "Memory", icon: "💾", href: "/memory", group: "Core" },
  { id: "skills", label: "Skills", icon: "⚡", href: "/skills/lab", group: "Core" },
  { id: "flux", label: "Flux", icon: "📊", href: "/flux", group: "Monitor" },
  { id: "settings", label: "Settings", icon: "⚙️", href: "/settings", group: "System" },
];

function Sidebar() {
  const { sidebarExpanded, toggleSidebar } = useUIStore();

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-40 h-screen border-r bg-background transition-all duration-300",
        sidebarExpanded ? "w-64" : "w-16"
      )}
    >
      <div className="flex h-full flex-col">
        <div className="flex h-14 items-center justify-between border-b px-4">
          {sidebarExpanded && (
            <span className="font-mono text-sm font-semibold text-accent">
              ETHAN
            </span>
          )}
          <button
            onClick={toggleSidebar}
            className="ml-auto rounded-md p-1.5 hover:bg-accent/10 transition-colors"
            aria-label="Toggle sidebar"
          >
            <span className="text-lg">{sidebarExpanded ? "◀" : "▶"}</span>
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto p-3">
          {(() => {
            const groups = navigationItems.reduce((acc, item) => {
              const group = item.group || "Other";
              if (!acc[group]) acc[group] = [];
              acc[group].push(item);
              return acc;
            }, {} as Record<string, SidebarItem[]>);

            return Object.entries(groups).map(([group, items]) => (
              <div key={group} className="mb-4">
                {sidebarExpanded && (
                  <h3 className="mb-2 px-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    {group}
                  </h3>
                )}
                <ul className="space-y-1">
                  {items.map((item) => (
                    <li key={item.id}>
                      <a
                        href={item.href}
                        className={cn(
                          "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                          "hover:bg-accent/10 hover:text-accent",
                          "text-muted-foreground"
                        )}
                        title={!sidebarExpanded ? item.label : undefined}
                      >
                        <span className="text-lg">{item.icon}</span>
                        {sidebarExpanded && (
                          <span className="font-medium">{item.label}</span>
                        )}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ));
          })()}
        </nav>

        <div className="border-t p-3">
          <div className="flex items-center gap-3 rounded-md px-3 py-2">
            <div className="h-8 w-8 rounded-full bg-accent/20 flex items-center justify-center">
              <span className="text-sm">👤</span>
            </div>
            {sidebarExpanded && (
              <div className="flex-1 overflow-hidden">
                <p className="text-sm font-medium truncate">User</p>
                <p className="text-xs text-muted-foreground truncate">user@ethan.ai</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </aside>
  );
}

export { Sidebar };