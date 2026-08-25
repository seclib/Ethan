"use client";

/**
 * useI18n — a dependency-free i18n hook for React/Next.js.
 *
 * Supports nested keys like "navigation.dashboard" and falls back to English.
 * No external library required — uses JSON imports + localStorage + a React context.
 */

import * as React from "react";
import en from "../locales/en.json";
import fr from "../locales/fr.json";

type Locale = "en" | "fr";
type Messages = Record<string, any>;

const messages: Record<Locale, Messages> = { en, fr };

interface I18nContextType {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string, fallback?: string) => string;
}

const I18nContext = React.createContext<I18nContextType | undefined>(undefined);

const LOCALE_STORAGE_KEY = "ethan_locale";

function getNestedValue(obj: Messages, path: string): any {
  return path.split(".").reduce<any>((acc, part) => (acc != null ? acc[part] : undefined), obj);
}

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = React.useState<Locale>(() => {
    if (typeof window !== "undefined") {
      return (localStorage.getItem(LOCALE_STORAGE_KEY) as Locale) || "en";
    }
    return "en";
  });

  const setLocale = React.useCallback((newLocale: Locale) => {
    setLocaleState(newLocale);
    if (typeof window !== "undefined") {
      localStorage.setItem(LOCALE_STORAGE_KEY, newLocale);
    }
  }, []);

  const t = React.useCallback(
    (key: string, fallback?: string): string => {
      const currentMessages = messages[locale];
      const value = getNestedValue(currentMessages, key);
      if (value != null) return String(value);
      // Fallback to English
      const fallbackValue = getNestedValue(messages.en, key);
      if (fallbackValue != null) return String(fallbackValue);
      // Ultimate fallback
      return fallback ?? key;
    },
    [locale],
  );

  const value = React.useMemo(
    () => ({ locale, setLocale, t }),
    [locale, setLocale, t],
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const context = React.useContext(I18nContext);
  if (context === undefined) {
    throw new Error("useI18n must be used within an I18nProvider");
  }
  return context;
}
