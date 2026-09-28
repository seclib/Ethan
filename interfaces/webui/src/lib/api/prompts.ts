"use client";

/**
 * ETHAN WebUI — Prompts client.
 *
 * Les prompts prédéfinis sont des enregistrements métier : ils vivent dans
 * ETHAN Core (PromptManager, core/config/prompts.py) et sont exposés par
 * /v1/prompts (routers/capabilities.py) :
 *   GET    /v1/prompts
 *   POST   /v1/prompts
 *   GET    /v1/prompts/{id}
 *   PUT    /v1/prompts/{id}
 *   DELETE /v1/prompts/{id}
 *
 * L'interface affiche et contrôle ; elle ne stocke aucun prompt.
 */

import { apiFetch } from "@/lib/api/client";

export interface Prompt {
  id: string;
  name: string;
  text: string;
  description: string;
  tags: string[];
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface PromptInput {
  name: string;
  text: string;
  description?: string;
  tags?: string[];
}

export async function listPrompts(): Promise<Prompt[]> {
  return apiFetch<Prompt[]>("/v1/prompts");
}

export async function createPrompt(input: PromptInput): Promise<Prompt> {
  return apiFetch<Prompt>("/v1/prompts", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function updatePrompt(id: string, data: Partial<PromptInput>): Promise<Prompt> {
  return apiFetch<Prompt>(`/v1/prompts/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function deletePrompt(id: string): Promise<{ status: string }> {
  return apiFetch<{ status: string }>(`/v1/prompts/${id}`, { method: "DELETE" });
}
