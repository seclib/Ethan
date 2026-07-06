"use client";

import { useCallback } from "react";
import { useStore, NAV_ITEMS, GROUP_LABELS, type AppPage, type NavGroup } from "@/lib/store";
import { useMediaQuery } from "@/hooks/useMediaQuery";

export function Sidebar() {
  const isMobile = useMediaQuery("(max-width: 1023px)");
  const { sidebarOpen, toggleSidebar, currentPage, setPage, openContextMenu } = useStore();

  const handleContext = useCallback(
    (e: React.MouseEvent, page: AppPage) => {
      e.preventDefault();
      openContextMenu(e.clientX, e.clientY, page);
    },
    [openContextMenu]
  );

  return (
    <>
      {/* Mobile overlay */}
      {sidebarOpen && isMobile && (
        <div className="sidebar-mobile-overlay" onClick={toggleSidebar} />
      )}

      <aside
        className="sidebar"
        data-expanded={sidebarOpen || undefined}
        data-mobile={isMobile || undefined}
      >
        {/* Header */}
        <div className="sidebar-header">
          <span className="sidebar-brand">◆ ETHAN</span>
          <button className="sidebar-toggle" onClick={toggleSidebar} title="Toggle (⌘B)">
            {sidebarOpen ? "✕" : "☰"}
          </button>
        </div>

        {/* Nav list (flat) */}
        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => {
            const active = currentPage === item.id;
            return (
              <button
                key={item.id}
                className="sidebar-item"
                data-active={active || undefined}
                onClick={() => setPage(item.id)}
                onContextMenu={(e) => handleContext(e, item.id)}
                title={sidebarOpen ? undefined : item.label}
              >
                <span className="sidebar-item-icon">{item.icon}</span>
                {sidebarOpen && (
                  <>
                    <span className="sidebar-item-label">{item.label}</span>
                    <span className="sidebar-item-shortcut">{item.shortcut}</span>
                  </>
                )}
              </button>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="sidebar-footer">
          <span className="sidebar-status online">●</span>
          {sidebarOpen && (
            <>
              <span className="sidebar-version">ETHAN v2.4.1</span>
              <span className="sidebar-help" onClick={() => setPage("settings")}>⚙</span>
            </>
          )}
        </div>
      </aside>
    </>
  );
}