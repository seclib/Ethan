"use client";

import * as React from "react";
import { AnimatePresence, motion } from "framer-motion";
import { usePathname } from "next/navigation";
import { ThemeProvider } from "@/providers/theme-provider";
import { QueryProvider } from "@/providers/query-provider";
import { AuthProvider } from "@/providers/auth-provider";
import { WebSocketProvider } from "@/providers/websocket-provider";
import { I18nProvider } from "@/lib/i18n";
import { ToastProvider } from "@/components/ui/toast-provider";
import { useUIStore } from "@/store/ui.store";
import { AppSidebar } from "@/components/layout/sidebar";
import { AppHeader } from "@/components/layout/app-header";
import { GlobalShortcuts } from "@/components/layout/global-shortcuts";
import { GlobalCommandPalette } from "@/components/layout/global-command-palette";
import { OverlayEscHandler } from "@/components/ui/overlay-esc-handler";
import { GlobalInspector } from "@/components/layout/global-inspector";
import { MissionControlOverlay } from "@/components/layout/mission-control-overlay";
import { AtmosphereLayer } from "@/components/layout/atmosphere-layer";
import { FloatingWindow } from "@/components/ui/floating-window";
import { MailPanel } from "@/components/features/flux/components/mail-panel";
import { Inbox } from "lucide-react";
import "./globals.css";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const { sidebarExpanded, toggleSidebar, mailPanelOpen, toggleMailPanel } = useUIStore();

  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
            <body className="antialiased" style={{ background: "var(--bg)", color: "var(--fg)", minHeight: "100dvh", margin: 0, overflowX: "hidden" }}>
                        <ThemeProvider>
          <QueryProvider>
            <AuthProvider>
              <I18nProvider>
                <WebSocketProvider>
                  <div style={{ display: "flex", width: "100%", height: "100dvh", overflow: "hidden" }}>
                  <GlobalShortcuts />
                  <GlobalCommandPalette />
                  <OverlayEscHandler />
                  <GlobalInspector />
                  <MissionControlOverlay />
                  <AtmosphereLayer />

                                    {/* AppSidebar — LA sidebar unique (chat + nav), repliable */ }
                  <AppSidebar expanded={sidebarExpanded} onToggle={toggleSidebar} />

                  {/* Main Content */}
                   <main
                    style={{ flex: 1, minWidth: 0, position: "relative", display: "flex", flexDirection: "column", background: "var(--bg)", overflow: "auto" }}
                  >
                  {/* App Header global — masqué sur "/" (top bar chat dédiée) */}
                                    {pathname !== "/" && <AppHeader />}

                    <AnimatePresence mode="wait" initial={false}>
                      <motion.div
                        key={pathname}
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -8 }}
                        transition={{ duration: 0.2, ease: [0.2, 0.8, 0.25, 1] }}
                        style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}
                      >
                        {children}
                      </motion.div>
                    </AnimatePresence>
                  </main>
                </div>
                <ToastProvider />

                {/* Fenêtre superposée Mail (pattern fenêtre flottante) */}
                <FloatingWindow
                  id="mail-panel"
                  title="Boîte de réception"
                  open={mailPanelOpen}
                  onOpenChange={(open) => { if (open) toggleMailPanel(); }}
                  defaultWidth={480}
                  defaultHeight={560}
                  defaultX={typeof window !== "undefined" ? window.innerWidth - 520 : 40}
                  defaultY={80}
                >
                  <MailPanel />
                </FloatingWindow>

                {/* Trigger flottant Mail — toujours accessible depuis n'importe quelle page */}
                <button
                  onClick={toggleMailPanel}
                  className="fixed bottom-20 right-4 z-[60] flex items-center justify-center w-11 h-11 rounded-full border border-line-2 bg-panel shadow-lg hover:bg-accent/10 transition-colors"
                  title="Boîte de réception (Mail)"
                  aria-label="Ouvrir la boîte de réception"
                >
                  <Inbox size={18} className="text-foreground-secondary" />
                </button>
                                </WebSocketProvider>
              </I18nProvider>
            </AuthProvider>
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}