import { apiFetch } from '@/lib/api/client';

export interface ApplicationCatalogSource {
  source: string;
  root?: string;
}

export interface ApplicationCatalogEntry {
  app_id: string;
  instance_id: string;
  source: string;
  validated: boolean;
  manifest_digest: string;
  location: string;
  manifest?: Record<string, unknown>;
}

export async function listApplications(): Promise<ApplicationCatalogEntry[]> {
  return apiFetch<ApplicationCatalogEntry[]>('/v1/applications');
}

export async function getApplication(appId: string): Promise<ApplicationCatalogEntry> {
  return apiFetch<ApplicationCatalogEntry>(`/v1/applications/${encodeURIComponent(appId)}`);
}

export async function refreshApplications(): Promise<{ status: string; count: string }> {
  return apiFetch<{ status: string; count: string }>('/v1/applications/refresh', {
    method: 'POST',
  });
}

export interface RegisteredApplication {
  registration_id: string;
  app_id: string;
  instance_id: string;
  state: string;
  compliance_status: string;
  capabilities: string[];
  available: boolean;
}

export async function listRegisteredApplications(): Promise<RegisteredApplication[]> {
  return apiFetch<RegisteredApplication[]>('/v1/applications/registered');
}

export interface ApplicationRuntimeStatus {
  app_id: string;
  state: string;
  healthy: boolean | null;
  container_id: string | null;
  supported_operations?: string[];
  status?: Record<string, unknown>;
}

export async function getApplicationRuntime(appId: string): Promise<ApplicationRuntimeStatus> {
  return apiFetch<ApplicationRuntimeStatus>(`/v1/applications/${encodeURIComponent(appId)}/runtime`);
}

export async function startApplicationRuntime(appId: string): Promise<{ app_id: string; action: string; result: Record<string, unknown> }> {
  return apiFetch<{ app_id: string; action: string; result: Record<string, unknown> }>(
    `/v1/applications/${encodeURIComponent(appId)}/start`,
    { method: 'POST' },
  );
}

export async function stopApplicationRuntime(appId: string): Promise<{ app_id: string; action: string; result: Record<string, unknown> }> {
  return apiFetch<{ app_id: string; action: string; result: Record<string, unknown> }>(
    `/v1/applications/${encodeURIComponent(appId)}/stop`,
    { method: 'POST' },
  );
}
