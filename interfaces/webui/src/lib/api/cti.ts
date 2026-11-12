import { apiFetch } from "@/lib/api/client";

export interface CtiManifest {
  id: string;
  name: string;
  version: string;
  description: string;
  route: string;
  api_base: string;
  model: string;
  capabilities: string[];
}

export interface CtiStatus {
  status: string;
  service: string;
  model: string;
  object_count: number;
  object_count_limit: number;
}

export interface CtiRecord {
  id: string;
  owner_id: string;
  stix_object: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export async function getCtiManifest(): Promise<CtiManifest> {
  return apiFetch<CtiManifest>("/v1/cti/manifest");
}

export async function getCtiStatus(): Promise<CtiStatus> {
  return apiFetch<CtiStatus>("/v1/cti/status");
}

export async function listCtiObjects(): Promise<{ items: CtiRecord[]; count: number }> {
  return apiFetch<{ items: CtiRecord[]; count: number }>("/v1/cti/objects?limit=200");
}

export async function createCtiObject(stixObject: Record<string, unknown>): Promise<CtiRecord> {
  return apiFetch<CtiRecord>("/v1/cti/objects", {
    method: "POST",
    body: JSON.stringify(stixObject),
  });
}
