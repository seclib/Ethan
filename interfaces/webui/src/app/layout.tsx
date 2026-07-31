import * as React from "react";
import { ThemeProvider } from "@/core/providers/theme-provider";
import { QueryProvider } from "@/core/providers/query-provider";
import { AuthProvider } from "@/core/providers/auth-provider";
import { ToastProvider } from "@/components/ui/toast-provider";
import "./globals.css";

export const metadata = {
  title: "ETHAN — Cognitive Runtime",
  description: "Web interface for the ETHAN Cognitive Runtime",
  icons: "/favicon.ico",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body className="min-h-screen bg-background text-foreground antialiased">
        <ThemeProvider>
          <QueryProvider>
            <AuthProvider>
              {children}
              <ToastProvider />
            </AuthProvider>
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
