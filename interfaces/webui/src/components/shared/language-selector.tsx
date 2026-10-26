"use client";

import * as React from "react";
import { useI18n, SUPPORTED_LOCALES, LOCALE_LABELS } from "@/lib/i18n";
import { Globe } from "lucide-react";

export function LanguageSelector() {
  const { locale, setLocale } = useI18n();

  return (
    <div className="flex items-center gap-2">
      <Globe size={16} className="text-foreground-secondary" />
      <select
        value={locale}
        onChange={(e) => setLocale(e.target.value as any)}
        className="bg-panel border border-line-2 rounded-md px-2 py-1 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-accent"
        aria-label="Select language"
      >
        {SUPPORTED_LOCALES.map((loc) => (
          <option key={loc} value={loc}>
            {LOCALE_LABELS[loc]}
          </option>
        ))}
      </select>
    </div>
  );
}
