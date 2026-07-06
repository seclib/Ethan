// ETHAN — Persistance des données utilisateur
// Sauvegarde/restauration automatique via localStorage

const PREFIX = "ethan:";

export function persist<T>(key: string, value: T): void {
  try {
    localStorage.setItem(PREFIX + key, JSON.stringify(value));
  } catch {
    // localStorage plein ou désactivé — silencieux
  }
}

export function restore<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(PREFIX + key);
    if (raw === null) return fallback;
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

export function remove(key: string): void {
  try {
    localStorage.removeItem(PREFIX + key);
  } catch {
    // silencieux
  }
}

// ───────── Hooks simplifiés ─────────

import { useState, useCallback, useEffect } from "react";

export function usePersistentState<T>(key: string, initial: T) {
  const [value, setValue] = useState<T>(() => restore(key, initial));

  useEffect(() => {
    persist(key, value);
  }, [key, value]);

  const reset = useCallback(() => {
    remove(key);
    setValue(initial);
  }, [key, initial]);

  return [value, setValue, reset] as const;
}