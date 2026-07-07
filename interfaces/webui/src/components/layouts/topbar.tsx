"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/stores/ui.store";
import { useAuth } from "@/providers/auth-provider";

function Topbar() {
  const { toggleInspector, openCommandPalette } = useUIStore();
  const { user, logout } = useAuth();

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-4">
      {/* Left section */}
      <div className="flex items-center gap-4">
        <h1 className="text-lg font-semibold">ETHAN</h1>
        <span className="text-xs text-muted-foreground">Cognitive Runtime</span>
      </div>

      {/* Center section - Breadcrumb or page title can go here */}
      <div className="flex-1" />

      {/* Right section */}
      <div className="flex items-center gap-2">
        {/* Command Palette trigger */}
        <button
          onClick={openCommandPalette}
          className={cn(
            "flex items-center gap-2 rounded-md border px-3 py-1.5",
            "text-sm text-muted-foreground hover:text-foreground",
            "transition-colors"
          )}
        >
          <span>⌘</span>
          <span>K</span>
        </button>

        {/* Inspector toggle */}
        <button
          onClick={toggleInspector}
          className={cn(
            "rounded-md p-2 hover:bg-accent/10 transition-colors",
            "text-muted-foreground hover:text-foreground"
          )}
          aria-label="Toggle inspector"
        >
          <span className="text-lg">🔍</span>
        </button>

        {/* User menu */}
        {user && (
          <div className="flex items-center gap-3 ml-2 pl-2 border-l">
            <div className="text-right hidden sm:block">
              <p className="text-sm font-medium">{user.name}</p>
              <p className="text-xs text-muted-foreground">{user.email}</p>
            </div>
            <button
              onClick={logout}
              className={cn(
                "rounded-md px-3 py-1.5 text-sm",
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