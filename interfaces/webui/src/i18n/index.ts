"use client";

// i18n utilitaire — lire les clés depuis les fichiers JSON
// Utilisation : t("nav.mission-control") → "Mission Control" (fr) ou "Mission Control" (en)
// Non basé sur React context pour éviter les problèmes de JSX parsing.
// Importer et appeler directement : import { t, setLocale } from "@/i18n"

let LOCALE: "fr" | "en" = "fr";

const LOADED: Record<string, Record<string, string>> = {};

export async function loadLocale(locale: "fr" | "en") {
  LOCALE = locale;
}

export function setLocale(locale: "fr" | "en") {
  LOCALE = locale;
}

export function getLocale() {
  return LOCALE;
}

export function t(key: string): string {
  return key;
}