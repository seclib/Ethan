import type { Metadata, Viewport } from "next";
import "./globals.css";

if (typeof window !== "undefined") {
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("/sw.js").catch(() => {});
    });
  }
}
import { TopBar } from "@/components/layout/top-bar";
import { Sidebar } from "@/components/layout/sidebar";
import { ContextMenu } from "@/components/layout/context-menu";
import { AppShell } from "@/components/layout/app-shell";
import { ErrorBoundary } from "@/components/error-boundary";
import { CommandPalette } from "@/components/ui/command-palette";
import { Atmosphere } from "@/components/ui/atmosphere";
import { ToastProvider } from "@/components/ui/toast";
import { KeyboardListener } from "@/components/layout/keyboard-listener";

export const metadata: Metadata = {
  title: "ETHAN Cognitive OS",
  description: "Dashboard cognitif ETHAN",
  manifest: "/manifest.json",
};

export const viewport: Viewport = {
  themeColor: "#2563eb",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr" className="dark">
      <body className="antialiased">
        <ErrorBoundary>
          <Atmosphere />
          <TopBar />
          <div className="app-layout">
            <Sidebar />
            <div className="app-layout-body">
              <ToastProvider>
                <AppShell>{children}</AppShell>
              </ToastProvider>
            </div>
          </div>
          <CommandPalette />
          <ContextMenu />
          <KeyboardListener />
        </ErrorBoundary>
      </body>
    </html>
  );
}

