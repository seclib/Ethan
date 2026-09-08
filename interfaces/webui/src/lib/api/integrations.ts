/**
 * ETHAN WebUI — Integrations API service
 *
 * Maps to ETHAN API endpoints:
 *   GET    /v1/integrations                     → listIntegrations
 *   GET    /v1/integrations/{id}                → getIntegration
 *   POST   /v1/integrations                     → createIntegration
 *   PUT    /v1/integrations/{id}                → updateIntegration
 *   DELETE /v1/integrations/{id}                → deleteIntegration
 *   POST   /v1/integrations/{id}/connect        → connectIntegration
 *   POST   /v1/integrations/{id}/disconnect     → disconnectIntegration
 *   POST   /v1/integrations/{id}/test           → testIntegration
 *
 * The WebUI only manages configuration. Secrets are never displayed.
 */

import { apiFetch } from '@/lib/api/client';

export type IntegrationKind =
  | 'mcp'
  | 'web-search'
  | 'storage'
  | 'automation'
  | 'developer'
  | 'external-app';

export type IntegrationStatus = 'disconnected' | 'connected' | 'error' | 'unknown';

export const INTEGRATION_KINDS: IntegrationKind[] = [
  'mcp',
  'web-search',
  'storage',
  'automation',
  'developer',
  'external-app',
];

export const INTEGRATION_STATUSES: IntegrationStatus[] = [
  'disconnected',
  'connected',
  'error',
  'unknown',
];

export interface Integration {
  id: string;
  name: string;
  kind: IntegrationKind;
  description: string;
  config: Record<string, unknown>;
  capabilities: string[];
  required_permissions: string[];
  status: IntegrationStatus;
  enabled: boolean;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  last_connected_at: string | null;
  credential_keys: string[];
  has_credentials: boolean;
}

export interface IntegrationCreate {
  name: string;
  kind: IntegrationKind;
  description?: string;
  config?: Record<string, unknown>;
  credentials?: Record<string, string>;
  capabilities?: string[];
  required_permissions?: string[];
  enabled?: boolean;
  metadata?: Record<string, unknown>;
}

export interface IntegrationUpdate {
  name?: string;
  description?: string;
  config?: Record<string, unknown>;
  credentials?: Record<string, string>;
  capabilities?: string[];
  required_permissions?: string[];
  enabled?: boolean;
  metadata?: Record<string, unknown>;
}

// ── List & Read ─────────────────────────────────────────────────────

export async function listIntegrations(kind?: IntegrationKind): Promise<Integration[]> {
  const qs = kind ? `?kind=${encodeURIComponent(kind)}` : '';
  return apiFetch<Integration[]>(`/v1/integrations${qs}`);
}

export async function getIntegration(id: string): Promise<Integration> {
  return apiFetch<Integration>(`/v1/integrations/${id}`);
}

// ── Mutations ───────────────────────────────────────────────────────

export async function createIntegration(data: IntegrationCreate): Promise<Integration> {
  return apiFetch<Integration>('/v1/integrations', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateIntegration(
  id: string,
  data: IntegrationUpdate,
): Promise<Integration> {
  return apiFetch<Integration>(`/v1/integrations/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteIntegration(id: string): Promise<{ status: string; integration_id: string }> {
  return apiFetch<{ status: string; integration_id: string }>(`/v1/integrations/${id}`, {
    method: 'DELETE',
  });
}

// ── Lifecycle ───────────────────────────────────────────────────────

export async function connectIntegration(id: string): Promise<Integration> {
  return apiFetch<Integration>(`/v1/integrations/${id}/connect`, {
    method: 'POST',
  });
}

export async function disconnectIntegration(id: string): Promise<Integration> {
  return apiFetch<Integration>(`/v1/integrations/${id}/disconnect`, {
    method: 'POST',
  });
}

export async function testIntegration(id: string): Promise<{ status: IntegrationStatus; message: string }> {
  return apiFetch<{ status: IntegrationStatus; message: string }>(
    `/v1/integrations/${id}/test`,
    { method: 'POST' },
  );
}
