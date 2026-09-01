"use client";

/**
 * ETHAN WebUI — Cookbook / Email / Research clients (RFC-0001/2/3).
 * Logique métier dans ETHAN Core ; ces clients ne font que sérialiser
 * les requêtes vers l'API.
 */

import { apiFetch } from "@/lib/api/client";

// ── Cookbook ────────────────────────────────────────────────────────────

export interface RecipeSummary {
  id: string;
  name: string;
  version: string;
  description: string;
  requires: Record<string, string[]>;
  installs_summary: Record<string, number>;
  installed: boolean;
}

export interface InstallRecord {
  recipe_id: string;
  version: string;
  created: { kind: string; id: string }[];
}

export interface RecipeInstallItem {
  name: string;
  description?: string;
  text?: string;
  content?: string;
  [key: string]: unknown;
}

export interface RecipeDetail {
  id: string;
  name: string;
  version: string;
  description: string;
  requires: Record<string, string[]>;
  tags: string[];
  installs_summary: Record<string, number>;
  installs: Record<string, RecipeInstallItem[]>;
  installed: boolean;
}

export const listRecipes = () => apiFetch<RecipeSummary[]>("/v1/cookbook/recipes");

export const getRecipeDetail = (id: string) =>
  apiFetch<RecipeDetail>(`/v1/cookbook/recipes/${id}`);

export const listInstalledRecipes = () =>
  apiFetch<InstallRecord[]>("/v1/cookbook/installed");

export const installRecipe = (id: string) =>
  apiFetch<InstallRecord>(`/v1/cookbook/install/${id}`, { method: "POST" });

export const uninstallRecipe = (id: string) =>
  apiFetch<{ status: string }>(`/v1/cookbook/install/${id}`, { method: "DELETE" });

// ── Email inbox ─────────────────────────────────────────────────────────

export interface EmailSummary {
  uid: string;
  from: string;
  from_name: string;
  subject: string;
  date: string;
}

export interface EmailDetail extends EmailSummary {
  to: string;
  body: string;
}

export const listEmailMessages = (limit = 20) =>
  apiFetch<EmailSummary[]>(`/v1/email/messages?limit=${limit}`);

export const getEmailMessage = (uid: string) =>
  apiFetch<EmailDetail>(`/v1/email/messages/${uid}`);

// ── Deep Research ───────────────────────────────────────────────────────

export interface ResearchResult {
  query: string;
  depth: number;
  steps: { step: number; query: string; sources_found: number }[];
  sources: { title: string; snippet: string; url: string }[];
  report: string;
}

export const runResearch = (query: string, depth = 2) =>
  apiFetch<ResearchResult>("/v1/research", {
    method: "POST",
    body: JSON.stringify({ query, depth }),
  });