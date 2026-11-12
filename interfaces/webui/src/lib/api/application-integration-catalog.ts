import { apiFetch } from '@/lib/api/client';

export type CatalogState =
  | boolean
  | null
  | string;

export interface ApplicationCatalogState {
  discovered: boolean;
  validated: CatalogState;
  registered: boolean;
  installed: string;
  available: string;
  running: string;
  authorized: string;
}

export interface ApplicationCatalogItem {
  repository_path: string;
  repository_name: string;
  analysis: Record<string, unknown>;
  manifest_availability: string;
  manifest_validation_status: string;
  application_type: string;
  declared_capabilities: string[];
  declared_dependencies: string[];
  declared_permissions: string[];
  required_permissions: string[];
  integration_preview: Record<string, unknown> | null;
  registration_status: string;
  registered_identity: Record<string, unknown> | null;
  manifest_fingerprint: string | null;
  sources: Record<string, string>;
  states: ApplicationCatalogState;
  errors: string[];
}

export interface ApplicationCatalogResponse {
  root: string;
  items: ApplicationCatalogItem[];
  source_errors: string[];
}

export async function listApplicationIntegrationCatalog(): Promise<ApplicationCatalogResponse> {
  return apiFetch<ApplicationCatalogResponse>('/v1/application-integration/catalog');
}
