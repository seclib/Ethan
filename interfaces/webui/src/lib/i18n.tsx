"use client";

import * as React from "react";

export type Locale = "en" | "fr" | "ru" | "zh-CN" | "ja" | "ar";

export const SUPPORTED_LOCALES: Locale[] = ["en", "fr", "ru", "zh-CN", "ja", "ar"];

export const LOCALE_LABELS: Record<Locale, string> = {
  en: "English", fr: "Français", ru: "Русский", "zh-CN": "简体中文", ja: "日本語", ar: "العربية",
};

export const RTL_LOCALES: Set<Locale> = new Set(["ar"]);

export function isRTL(locale: Locale): boolean {
  return RTL_LOCALES.has(locale);
}

import en from "../locales/en.json";
import fr from "../locales/fr.json";
import ru from "../locales/ru.json";
import zhCN from "../locales/zh-CN.json";
import ja from "../locales/ja.json";
import ar from "../locales/ar.json";

type Messages = Record<string, any>;

const messages: Record<Locale, Messages> = { en, fr, ru, "zh-CN": zhCN, ja, ar };

function getNestedValue(obj: Messages, path: string): any {
  return path.split(".").reduce<any>((acc, part) => (acc != null ? acc[part] : undefined), obj);
}

const LOCALE_STORAGE_KEY = "ethan_locale";
const LOCALE_EXPLICIT_KEY = "ethan_locale_explicit";

function detectBrowserLocale(): Locale {
  if (typeof navigator === "undefined") return "en";
  const langs = navigator.languages && navigator.languages.length > 0 ? navigator.languages : [navigator.language || "en"];
  for (const raw of langs) {
    const lower = raw.toLowerCase();
    if (lower === "zh-cn" || lower === "zh-hans" || lower.startsWith("zh")) return "zh-CN";
    if (lower.startsWith("fr")) return "fr";
    if (lower.startsWith("ru")) return "ru";
    if (lower.startsWith("ja")) return "ja";
    if (lower.startsWith("ar")) return "ar";
    if (lower.startsWith("en")) return "en";
  }
  return "en";
}

function resolveInitialLocale(): Locale {
  if (typeof window === "undefined") return "en";
  const explicit = localStorage.getItem(LOCALE_EXPLICIT_KEY);
  if (explicit === "1") {
    const stored = localStorage.getItem(LOCALE_STORAGE_KEY) as Locale | null;
    if (stored && SUPPORTED_LOCALES.includes(stored)) return stored;
  }
  const detected = detectBrowserLocale();
  localStorage.setItem(LOCALE_STORAGE_KEY, detected);
  return detected;
}

function pluralCategory(locale: Locale, count: number): string {
  const n = Math.abs(count);
  switch (locale) {
    case "en": case "zh-CN": case "ja": return n === 1 ? "one" : "other";
    case "fr": return (n === 0 || n === 1) ? "one" : "other";
    case "ru": {
      const mod10 = n % 10; const mod100 = n % 100;
      if (mod10 === 1 && mod100 !== 11) return "one";
      if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return "few";
      return "many";
    }
    case "ar": {
      if (n === 0) return "zero"; if (n === 1) return "one"; if (n === 2) return "two";
      const mod100 = n % 100;
      if (mod100 >= 3 && mod100 <= 10) return "few";
      if (mod100 >= 11) return "many";
      return "other";
    }
    default: return n === 1 ? "one" : "other";
  }
}

function interpolate(template: string, vars?: Record<string, any>): string {
  if (!vars) return template;
  return template.replace(/\{(\w+)\}/g, (match, key) => {
    if (Object.prototype.hasOwnProperty.call(vars, key)) {
      const val = vars[key];
      return val != null ? String(val) : match;
    }
    return match;
  });
}

export function formatNumber(value: number, locale: Locale): string {
  try { return new Intl.NumberFormat(locale).format(value); }
  catch { return String(value); }
}

export function formatDate(value: Date | string | number, locale: Locale, options?: Intl.DateTimeFormatOptions): string {
  try { const date = value instanceof Date ? value : new Date(value); return new Intl.DateTimeFormat(locale, options).format(date); }
  catch { return String(value); }
}

interface I18nContextType {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string, vars?: Record<string, any>) => string;
  isRTL: boolean;
  formatNumber: (value: number) => string;
  formatDate: (value: Date | string | number, options?: Intl.DateTimeFormatOptions) => string;
}

const I18nContext = React.createContext<I18nContextType | undefined>(undefined);

const missingKeys = new Set<string>();

function warnMissingKey(key: string, locale: Locale) {
  if (process.env.NODE_ENV === "development") {
    if (!missingKeys.has(locale + ":" + key)) {
      missingKeys.add(locale + ":" + key);
      console.warn("[i18n] Missing translation key \"" + key + "\" for locale \"" + locale + "\"");
    }
  }
}

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = React.useState<Locale>("en");

  React.useEffect(() => { setLocaleState(resolveInitialLocale()); }, []);

  const setLocale = React.useCallback((newLocale: Locale) => {
    if (!SUPPORTED_LOCALES.includes(newLocale)) return;
    setLocaleState(newLocale);
    if (typeof window !== "undefined") {
      localStorage.setItem(LOCALE_STORAGE_KEY, newLocale);
      localStorage.setItem(LOCALE_EXPLICIT_KEY, "1");
      document.documentElement.lang = newLocale;
      document.documentElement.dir = isRTL(newLocale) ? "rtl" : "ltr";
    }
  }, []);

  React.useEffect(() => {
    if (typeof document !== "undefined") {
      document.documentElement.lang = locale;
      document.documentElement.dir = isRTL(locale) ? "rtl" : "ltr";
    }
  }, [locale]);

  const t = React.useCallback((key: string, vars?: Record<string, any>): string => {
    const currentMessages = messages[locale];
    let resolvedKey = key;
    if (vars && typeof vars.count === "number") {
      const cat = pluralCategory(locale, vars.count);
      const pluralKey = key + "_" + cat;
      const pluralValue = getNestedValue(currentMessages, pluralKey);
      if (pluralValue != null) resolvedKey = pluralKey;
      else { const otherValue = getNestedValue(currentMessages, key + "_other"); if (otherValue != null) resolvedKey = key + "_other"; }
    }
    let value = getNestedValue(currentMessages, resolvedKey);
    if (value == null && locale !== "en") {
      value = getNestedValue(messages.en, resolvedKey);
      if (value == null && vars && typeof vars.count === "number") {
        const cat = pluralCategory("en", vars.count);
        value = getNestedValue(messages.en, key + "_" + cat);
        if (value == null) value = getNestedValue(messages.en, key + "_other");
      }
    }
    if (value == null && vars && typeof vars.count === "number") {
      value = getNestedValue(currentMessages, key);
      if (value == null && locale !== "en") value = getNestedValue(messages.en, key);
    }
    if (value == null) { warnMissingKey(key, locale); return key; }
    const str = String(value);
    if (str.trim() === "") {
      warnMissingKey(key, locale);
      const enVal = getNestedValue(messages.en, resolvedKey);
      if (enVal != null && String(enVal).trim() !== "") return interpolate(String(enVal), vars);
      return key;
    }
    return interpolate(str, vars);
  }, [locale]);

  const fmtNumber = React.useCallback((value: number) => formatNumber(value, locale), [locale]);
  const fmtDate = React.useCallback((value: Date | string | number, options?: Intl.DateTimeFormatOptions) => formatDate(value, locale, options), [locale]);

  const value = React.useMemo(() => ({ locale, setLocale, t, isRTL: isRTL(locale), formatNumber: fmtNumber, formatDate: fmtDate }), [locale, setLocale, t, fmtNumber, fmtDate]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const context = React.useContext(I18nContext);
  if (context === undefined) throw new Error("useI18n must be used within an I18nProvider");
  return context;
}

export { messages, getNestedValue };
