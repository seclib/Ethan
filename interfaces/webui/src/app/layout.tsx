import * as React from "react";
import { ThemeProvider } from "@/providers/theme-provider";
import { QueryProvider } from "@/providers/query-provider";
import { WebSocketProvider } from "@/providers/websocket-provider";
import type { Metadata } from "next";

// Import global styles
import "./globals.css";

export const metadata: Metadata = {
  title: "ETHAN — Cognitive Runtime",
  description: "Web interface for the ETHAN Cognitive Runtime",
  icons: "/favicon.ico",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body className="min-h-screen bg-background text-foreground antialiased">
        <ThemeProvider>
          <QueryProvider>
            <WebSocketProvider>
              {children}
            </WebSocketProvider>
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}