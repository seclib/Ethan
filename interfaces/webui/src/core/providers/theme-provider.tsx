"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

type Theme = "dark" | "light" | "high-contrast" | "oled" | "system";

interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  resolvedTheme: "dark" | "light" | "high-contrast" | "oled";
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>("dark");
  const [resolvedTheme, setResolvedTheme] = useState<"dark" | "light" | "high-contrast" | "oled">("dark");

  // Load theme from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem("ethan_theme") as Theme | null;
    if (stored) {
      setTheme(stored);
    }
  }, []);

  // Resolve system theme
  useEffect(() => {
    const resolveTheme = () => {
      if (theme === "system") {
        const systemTheme = window.matchMedia("(prefers-color-scheme: dark)").matches
          ? "dark"
          : "light";
        setResolvedTheme(systemTheme);
      } else {
        setResolvedTheme(theme);
      }
    };

    resolveTheme();

    // Listen for system theme changes
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = () => {
      if (theme === "system") {
        resolveTheme();
      }
    };
    mediaQuery.addEventListener("change", handler);

    return () => mediaQuery.removeEventListener("change", handler);
  }, [theme]);

  // Detect high contrast preference
  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-contrast: high)");
    const handler = (e: MediaQueryListEvent) => {
      if (e.matches && theme === "system") {
        setResolvedTheme("high-contrast");
      }
    };
    mediaQuery.addEventListener("change", handler);
    return () => mediaQuery.removeEventListener("change", handler);
  }, [theme]);

  // Apply theme to document
  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove("light", "dark", "high-contrast", "oled");
    root.setAttribute("data-theme", resolvedTheme);
  }, [resolvedTheme]);

  const value = {
    theme,
    setTheme: (newTheme: Theme) => {
      localStorage.setItem("ethan_theme", newTheme);
      setTheme(newTheme);
    },
    resolvedTheme,
    isDark: resolvedTheme === "dark",
    isLight: resolvedTheme === "light",
    isHighContrast: resolvedTheme === "high-contrast",
    isOLED: resolvedTheme === "oled",
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}