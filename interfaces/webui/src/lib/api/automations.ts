"use client";

/**
 * ETHAN WebUI — Automations client.
 *
 * La logique métier vit dans ETHAN Core (AutomationManager,
 * core/scheduler/automations.py) ; ce client ne fait que sérialiser les
 * requêtes sur /v1/automations (routers/capabilities.py) :
 *   GET    /v1/automations[?enabled=]
 *   POST   /v1/automations
 *   PUT    /v1/automations/{id}
 *   DELETE /v1/automations/{id}
 *   POST   /v1/automations/{id}/trigger
 *
 * Aucune donnée simulée : l'interface affiche exactement ce que le Core
 * renvoie. Déclencher une règle publie `automation.triggered` sur le bus ;
 * l'exécution des actions reste du ressort du Runtime.
 */

import { apiFetch } from "@/lib/api/client";

export interface Automation {
  id: string;
  name: string;
  description: string;
  trigger: Record<string, unknown>;
  actions: Array<Record<string, unknown>>;
  enabled: boolean;
  last_triggered_at: string | null;
  trigger_count: number;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface CreateAutomationInput {
  name: string;
  description?: string;
  trigger?: Record<string, unknown>;
  actions?: Array<Record<string, unknown>>;
  enabled?: boolean;
}

/** Liste les règles, éventuellement filtrées par état (filtre délégué au Core). */
export async function listAutomations(enabled?: boolean): Promise<Automation[]> {
  const qs = enabled === undefined ? "" : `?enabled=${enabled ? "true" : "false"}`;
  return apiFetch<Automation[]>(`/v1/automations${qs}`);
}

export async function createAutomation(input: CreateAutomationInput): Promise<Automation> {
  return apiFetch<Automation>("/v1/automations", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function updateAutomation(
  id: string,
  data: Partial<CreateAutomationInput>,
): Promise<Automation> {
  return apiFetch<Automation>(`/v1/automations/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function deleteAutomation(id: string): Promise<{ status: string }> {
  return apiFetch<{ status: string }>(`/v1/automations/${id}`, { method: "DELETE" });
}

/**
 * Déclenchement manuel d'une règle active — le Core met à jour
 * `last_triggered_at` / `trigger_count` et publie l'événement.
 * Une règle désactivée renvoie 404 côté Core (aucun déclenchement forcé).
 */
export async function triggerAutomation(id: string): Promise<Automation> {
  return apiFetch<Automation>(`/v1/automations/${id}/trigger`, { method: "POST" });
}
