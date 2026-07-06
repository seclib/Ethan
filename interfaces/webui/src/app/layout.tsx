import type { Metadata, Viewport } from "next";
import "./globals.css";

if (typeof window !== "undefined") {
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("/sw.js").catch(() => {});
    });
  }
}
import { TopNav } from "@/components/layout/top-nav";
import { AppShell } from "@/components/layout/app-shell";
import { ErrorBoundary } from "@/components/error-boundary";
import { CommandPalette } from "@/components/ui/command-palette";
import { Atmosphere } from "@/components/ui/atmosphere";
import { ChapterIndicator } from "@/components/ui/chapter-indicator";
import { MissionControlTrigger } from "@/components/ui/mission-control-trigger";
import { RoomsNavigation } from "@/components/navigation/rooms-navigation";
import { MissionControl } from "@/components/navigation/mission-control";
import { ToastProvider } from "@/components/ui/toast";

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
          <TopNav />
          <ToastProvider>
          <AppShell>{children}</AppShell>
        </ToastProvider>
          <CommandPalette />
          <ChapterIndicator />
          <MissionControlTrigger />
          <RoomsNavigation />
          <MissionControl />
        </ErrorBoundary>
      </body>
    </html>
  );
}

