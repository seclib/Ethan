"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/core/store/ui.store";
import { useAuth } from "@/core/providers/auth-provider";
import { ChevronRight, Command, Search, Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";

function Topbar() {
  const { toggleInspector, openCommandPalette } = useUIStore();
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const { theme, setTheme } = useTheme();

  // Generate breadcrumbs from pathname
  const paths = pathname === "/" ? ["dashboard"] : pathname.split("/").filter(Boolean);

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-6">
      {/* Breadcrumbs */}
      <div className="flex items-center gap-2 font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
        <Link href="/" className="hover:text-foreground transition-colors">ETHAN</Link>
        {paths.map((path, index) => {
          const href = "/" + paths.slice(0, index + 1).join("/");
          return (
            <React.Fragment key={path}>
              <ChevronRight size={14} className="text-muted-foreground/50" />
              <Link 
                href={href} 
                className={cn(
                  "hover:text-foreground transition-colors",
                  index === paths.length - 1 && "text-accent font-semibold"
                )}
              >
                {path.replace("-", " ")}
              </Link>
            </React.Fragment>
          );
        })}
      </div>

      {/* Right section */}
      <div className="flex items-center gap-3">
        {/* Status indicator (Mock) */}
        <div className="hidden sm:flex items-center gap-2 mr-4 text-[11px] font-mono tracking-wider">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
          </span>
          <span className="text-muted-foreground">KERNEL ONLINE</span>
        </div>

        {/* Command Palette trigger */}
        <button
          onClick={openCommandPalette}
          className={cn(
            "flex items-center gap-2 rounded-md border border-line-2 bg-background px-2.5 py-1.5",
            "text-xs text-muted-foreground hover:text-foreground hover:border-line-3",
            "transition-colors"
          )}
          title="Search (⌘K)"
        >
          <Search size={14} />
          <span>Search...</span>
          <div className="flex items-center gap-0.5 px-1 py-0.5 rounded bg-muted/50 ml-2">
            <Command size={10} />
            <span className="text-[9px]">K</span>
          </div>
        </button>

        {/* Theme toggle */}
        <button
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          className="rounded-md p-2 hover:bg-accent/10 text-muted-foreground hover:text-foreground transition-colors"
          aria-label="Toggle theme"
        >
          {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
        </button>

        {/* Inspector toggle */}
        <button
          onClick={toggleInspector}
          className={cn(
            "rounded-md p-2 hover:bg-accent/10 transition-colors",
            "text-muted-foreground hover:text-foreground"
          )}
          title="Toggle Inspector"
        >
          <Search size={18} />
        </button>

        {/* User menu */}
        {user && (
          <div className="flex items-center gap-3 ml-2 pl-4 border-l border-line-2">
            <div className="text-right hidden sm:block">
              <p className="text-xs font-medium">{user.name}</p>
              <p className="text-[10px] text-muted-foreground">{user.email}</p>
            </div>
            <button
              onClick={logout}
              className={cn(
                "rounded-md px-3 py-1.5 text-xs font-medium",
                "bg-accent/10 text-accent hover:bg-accent/20",
                "transition-colors"
              )}
            >
              Logout
            </button>
          </div>
        )}
      </div>
    </header>
  );
}

export { Topbar };