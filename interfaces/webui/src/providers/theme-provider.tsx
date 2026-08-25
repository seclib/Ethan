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

    // Helper : safely check a media query match (works in all environments)
  const matchMedia = (query: string): boolean => {
    if (typeof window === "undefined" || !window.matchMedia) return false;
    const result = window.matchMedia(query);
    return result.matches ?? false; // `.matches` is a boolean on MediaQueryList
  };

  // Resolve system theme — re-evaluated whenever the selected `theme` changes
  useEffect(() => {
    const resolveTheme = () => {
      if (theme === "system") {
        const systemTheme = matchMedia("(prefers-color-scheme: dark)")
          ? "dark"
          : "light";
        setResolvedTheme(systemTheme);
      } else {
        setResolvedTheme(theme);
      }
    };

    resolveTheme();

    // Listen for system theme changes (modern EventTarget API)
    if (typeof window === "undefined" || !("addEventListener" in (window as any))) return;
    const darkQuery = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = () => {
      if (theme === "system") {
        resolveTheme();
      }
    };
    // Modern browsers support addEventListener on MediaQueryList; fallback to
    // addListener for very old engines.
    if (typeof darkQuery.addEventListener === "function") {
      darkQuery.addEventListener("change", handler);
    } else if (typeof (darkQuery as any).addListener === "function") {
      (darkQuery as any).addListener(handler);
    }
    return () => {
      if (typeof darkQuery.removeEventListener === "function") {
        darkQuery.removeEventListener("change", handler);
      } else if (typeof (darkQuery as any).removeListener === "function") {
        (darkQuery as any).removeListener(handler);
      }
    };
  }, [theme]);

  // Detect high-contrast preference
  useEffect(() => {
    if (typeof window === "undefined") return;
    const hcQuery = window.matchMedia("(prefers-contrast: high)");
    const handler = (e: MediaQueryListEvent | Event) => {
      const target = e.target as MediaQueryList;
      if (target.matches && theme === "system") {
        setResolvedTheme("high-contrast");
      }
    };
    if (typeof hcQuery.addEventListener === "function") {
      hcQuery.addEventListener("change", handler);
    } else if (typeof (hcQuery as any).addListener === "function") {
      (hcQuery as any).addListener(handler);
    }
    return () => {
      if (typeof hcQuery.removeEventListener === "function") {
        hcQuery.removeEventListener("change", handler);
      } else if (typeof (hcQuery as any).removeListener === "function") {
        (hcQuery as any).removeListener(handler);
      }
    };
  }, [theme]);

  // Apply theme to document
  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove("light", "dark", "high-contrast", "oled");
    root.setAttribute("data-theme", resolvedTheme);
    // Add theme class so Tailwind `dark:` variants and Open-WebUI `.dark`
    // selectors activate correctly alongside the CSS-variable tokens.
    root.classList.add(resolvedTheme);
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