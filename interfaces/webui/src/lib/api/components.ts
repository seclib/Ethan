"use client";

/**
 * ETHAN WebUI — client des composants optionnels (/v1/components).
 *
 * PASSERELLE PASSIVE : toute la logique de cycle de vie (détection,
 * installation, santé, désinstallation) vit dans ETHAN Core
 * (core/capability_manager). Ce client ne fait que sérialiser les requêtes
 * et typer les réponses — aucune progression n'est inventée côté frontend :
 * elle provient du suivi d'opérations du Core.
 */

import { apiFetch } from "@/lib/api/client";

// ── Types (miroir du Core — section 2 : états explicites) ───────────────

/** États normalisés renvoyés par Core (jamais un simple booléen). */
export type ComponentState =
  | "SUPPORTED"
  | "NOT_INSTALLED"
  | "INSTALLING"
  | "INSTALLED"
  | "STARTING"
  | "RUNNING"
  | "STOPPED"
  | "UNHEALTHY"
  | "CONFIGURATION_REQUIRED"
  | "READY"
  | "UNINSTALLING"
  | "ERROR";

export interface ComponentDependency {
  id: string;
  kind: string;
  description: string;
  optional: boolean;
}

export interface ConfigSchemaField {
  name: string;
  type: string;
  required: boolean;
  default?: unknown;
  description: string;
  min_value?: number | null;
  max_value?: number | null;
  choices?: string[] | null;
}

export interface DataResource {
  kind: string;
  name: string;
  description: string;
}

/**
 * Provenance d'un composant (miroir du Core — core/capability_manager/types.py).
 * `source` : "builtin" | "official" | "community" | "custom" ; une valeur
 * inconnue est affichée telle quelle, jamais réinventée côté interface.
 */
export interface ComponentProvenance {
  source: string;
  author: string;
  url: string;
  license: string;
  /** SHA256 quand disponible — vide sinon (jamais un faux checksum). */
  checksum: string;
  /** Signature PGP/cosign quand disponible. */
  signature: string;
}

export interface ComponentStatus {
  id: string;
  name: string;
  description: string;
  type: string;
  version: string;
  backend: string;
  state: ComponentState;
  enabled: boolean;
  installed_version: string | null;
  last_error: string | null;
  config_keys: string[];
  updated_at: string | null;
  requires_confirmation: boolean;
  dependencies: ComponentDependency[];
  config_schema: ConfigSchemaField[];
  data_resources: DataResource[];
  /**
   * Provenance révélée par le Core. Optionnel : une API antérieure peut ne pas
   * la fournir — l'interface l'omet alors au lieu de l'inventer.
   */
  provenance?: ComponentProvenance;
}

export interface PlanStep {
  description: string;
  kind: string;
  destructive?: boolean;
}

export interface MutationPlan {
  capability_id: string;
  operation: string;
  steps: PlanStep[];
  requires_confirmation: boolean;
}

export interface OperationStatus {
  operation_id: string;
  capability_id: string;
  operation: string;
  progress: number;
  cancel_requested: boolean;
  started_at?: number;
  finished_at?: number;
  steps_done: [string, boolean, string][];
  done: boolean;
  error: string | null;
}

export interface HealthTestResult {
  ok: boolean;
  level: string;
  checks: { kind: string; ok: boolean; detail: string; level?: string }[];
}

// ── Requêtes (toutes passent par l'API Core) ────────────────────────────

export function listComponents(refresh = false): Promise<{ capabilities: ComponentStatus[] }> {
  return apiFetch(`/v1/components${refresh ? "?refresh=true" : ""}`);
}

export function getComponent(capabilityId: string): Promise<ComponentStatus> {
  return apiFetch(`/v1/components/${encodeURIComponent(capabilityId)}`);
}

/** Détection Core complète (support, dépendances, installation, santé). */
export function detectComponents(): Promise<{ states: Record<string, string> }> {
  return apiFetch("/v1/components/detect", { method: "POST" });
}

export function getInstallPlan(capabilityId: string): Promise<MutationPlan> {
  return apiFetch(`/v1/components/${encodeURIComponent(capabilityId)}/plan`);
}

export function getUninstallPlan(
  capabilityId: string,
  deleteData: boolean,
): Promise<MutationPlan> {
  return apiFetch(
    `/v1/components/${encodeURIComponent(capabilityId)}/plan/uninstall?delete_data=${deleteData}`,
  );
}

/** 202 : opération asynchrone — suivre via getOperation. */
export function installComponent(
  capabilityId: string,
  config?: Record<string, unknown>,
): Promise<{ operation_id: string }> {
  return apiFetch(`/v1/components/${encodeURIComponent(capabilityId)}/install`, {
    method: "POST",
    body: JSON.stringify({ config: config ?? {} }),
  });
}

export function configureComponent(
  capabilityId: string,
  config: Record<string, unknown>,
): Promise<{ capability_id: string; config_keys: string[] }> {
  return apiFetch(`/v1/components/${encodeURIComponent(capabilityId)}/configure`, {
    method: "POST",
    body: JSON.stringify({ config }),
  });
}

export function testComponent(capabilityId: string): Promise<HealthTestResult> {
  return apiFetch(`/v1/components/${encodeURIComponent(capabilityId)}/test`, {
    method: "POST",
  });
}

export function enableComponent(
  capabilityId: string,
): Promise<{ capability_id: string; enabled: boolean }> {
  return apiFetch(`/v1/components/${encodeURIComponent(capabilityId)}/enable`, {
    method: "POST",
  });
}

export function disableComponent(
  capabilityId: string,
): Promise<{ capability_id: string; enabled: boolean }> {
  return apiFetch(`/v1/components/${encodeURIComponent(capabilityId)}/disable`, {
    method: "POST",
  });
}

/** Démarre un composant installé et arrêté (santé vérifiée par le Core). */
export function startComponent(capabilityId: string): Promise<ComponentStatus> {
  return apiFetch(`/v1/components/${encodeURIComponent(capabilityId)}/start`, {
    method: "POST",
  });
}

/** Arrête un composant actif — les données sont toujours conservées. */
export function stopComponent(capabilityId: string): Promise<ComponentStatus> {
  return apiFetch(`/v1/components/${encodeURIComponent(capabilityId)}/stop`, {
    method: "POST",
  });
}

/** Suppression de données : double confirmation exigée par le Core. */
export function uninstallComponent(
  capabilityId: string,
  deleteData: boolean,
): Promise<{ operation_id: string; delete_data: boolean }> {
  return apiFetch(`/v1/components/${encodeURIComponent(capabilityId)}/uninstall`, {
    method: "POST",
    body: JSON.stringify({
      delete_data: deleteData,
      confirm_delete_data: deleteData,
    }),
  });
}

export function listOperations(): Promise<{ operations: OperationStatus[] }> {
  return apiFetch("/v1/components/operations");
}

export function getOperation(operationId: string): Promise<OperationStatus> {
  return apiFetch(`/v1/components/operations/${encodeURIComponent(operationId)}`);
}

export function cancelOperation(operationId: string): Promise<{ cancelled: boolean }> {
  return apiFetch(
    `/v1/components/operations/${encodeURIComponent(operationId)}/cancel`,
    { method: "POST" },
  );
}
