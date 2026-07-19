"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/core/store/ui.store";
import {
  LayoutDashboard,
  MessageSquare,
  Network,
  Database,
  FileText,
  Map,
  Bot,
  Wrench,
  Puzzle,
  Cpu,
  Key,
  Terminal as TerminalIcon,
  ScrollText,
  Settings,
  ChevronLeft,
  ChevronRight,
  User,
  Target
} from "lucide-react";

interface SidebarItem {
  id: string;
  label: string;
  icon: React.ElementType;
  href: string;
  group: string;
}

const navigationItems: SidebarItem[] = [
  // COGNITION & INTERACTION
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard, href: "/", group: "Cognition & Interaction" },
  { id: "assistant", label: "Assistant", icon: MessageSquare, href: "/assistant", group: "Cognition & Interaction" },
  { id: "memory", label: "Memory", icon: Network, href: "/memory", group: "Cognition & Interaction" },
  { id: "knowledge", label: "Knowledge", icon: Database, href: "/knowledge", group: "Cognition & Interaction" },
  { id: "documents", label: "Documents", icon: FileText, href: "/documents", group: "Cognition & Interaction" },
  
  // ORCHESTRATION & ENGINE
  { id: "planner", label: "Planner", icon: Map, href: "/planner", group: "Orchestration & Engine" },
  { id: "missions", label: "Missions", icon: Target, href: "/missions", group: "Orchestration & Engine" },
  { id: "agents", label: "Agents", icon: Bot, href: "/agents", group: "Orchestration & Engine" },
  { id: "tools", label: "Tools", icon: Wrench, href: "/tools", group: "Orchestration & Engine" },
  { id: "plugins", label: "Plugins", icon: Puzzle, href: "/plugins", group: "Orchestration & Engine" },

  // INFRASTRUCTURE & SYSTEM
  { id: "models", label: "Models", icon: Cpu, href: "/models", group: "Infrastructure & System" },
  { id: "providers", label: "Providers", icon: Key, href: "/providers", group: "Infrastructure & System" },
  { id: "terminal", label: "Terminal", icon: TerminalIcon, href: "/terminal", group: "Infrastructure & System" },
  { id: "logs", label: "Logs", icon: ScrollText, href: "/logs", group: "Infrastructure & System" },
  { id: "settings", label: "Settings", icon: Settings, href: "/settings", group: "Infrastructure & System" },
];

function Sidebar() {
  const { sidebarExpanded, toggleSidebar } = useUIStore();
  const pathname = usePathname();

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
            {sidebarExpanded ? <ChevronLeft size={18} /> : <ChevronRight size={18} />}
          </button>
        </div>

        <nav className="flex-1 overflow-y-auto py-3 custom-scrollbar">
          {(() => {
            const groups = navigationItems.reduce((acc, item) => {
              if (!acc[item.group]) acc[item.group] = [];
              acc[item.group].push(item);
              return acc;
            }, {} as Record<string, SidebarItem[]>);

            return Object.entries(groups).map(([group, items]) => (
              <div key={group} className="mb-6">
                {sidebarExpanded && (
                  <h3 className="mb-2 px-4 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/70">
                    {group}
                  </h3>
                )}
                <ul className="space-y-1 px-2">
                  {items.map((item) => {
                    const isActive = pathname === item.href || (item.href !== "/" && pathname?.startsWith(item.href));
                    const Icon = item.icon;
                    
                    return (
                      <li key={item.id}>
                        <Link
                          href={item.href}
                          className={cn(
                            "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors relative",
                            isActive
                              ? "bg-accent/15 text-accent font-medium"
                              : "hover:bg-accent/10 hover:text-accent text-muted-foreground",
                            !sidebarExpanded && "justify-center px-0"
                          )}
                          title={!sidebarExpanded ? item.label : undefined}
                        >
                          {isActive && (
                            <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-5 bg-accent rounded-r-md" />
                          )}
                          <Icon size={18} className={cn(isActive && "text-accent")} />
                          {sidebarExpanded && <span>{item.label}</span>}
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              </div>
            ));
          })()}
        </nav>

        <div className="border-t p-3">
          <div className="flex items-center gap-3 rounded-md px-3 py-2">
            <div className="h-8 w-8 rounded-full bg-accent/20 flex items-center justify-center flex-shrink-0">
              <User size={16} className="text-accent" />
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