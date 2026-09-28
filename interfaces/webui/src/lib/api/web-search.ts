import { apiFetch } from "@/lib/api/client";

export interface SearchEngine {
  id: string;
  label: string;
}

/** Vue publique d'un profil réseau (core/network) — aucun secret exposé. */
export interface NetworkProfileView {
  id: string;
  type: string;
  host: string | null;
  port: number | null;
  timeout_seconds: number;
  enabled: boolean;
  has_credentials: boolean;
}

export interface SearchResult {
  title: string;
  url: string;
  domain: string;
  snippet: string;
  source_engine: string;
  rank: number;
  metadata?: Record<string, unknown>;
}

export interface SearchResponse {
  query: string;
  engine: string;
  total_found: number;
  search_time_ms: number;
  results: SearchResult[];
  metadata?: Record<string, unknown>;
}

export interface SearchParams {
  query: string;
  engine?: string;
  max_results?: number;
  /** Identifiant de profil réseau (Direct | proxy | VPN) — les credentials
   * restent dans le Core (variables d'environnement, cf. core/network). */
  network_profile?: string;
}

export async function listSearchEngines(): Promise<SearchEngine[]> {
  const res = await apiFetch<{ engines: SearchEngine[] }>("/v1/web-search/engines");
  return res.engines;
}

export async function listNetworkProfiles(): Promise<NetworkProfileView[]> {
  const res = await apiFetch<{ profiles: NetworkProfileView[] }>(
    "/v1/web-search/network-profiles",
  );
  return res.profiles;
}

export async function searchWeb(params: SearchParams): Promise<SearchResponse> {
  return apiFetch<SearchResponse>("/v1/web-search/search", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export async function searchWebMulti(
  params: SearchParams & { engines?: string[] },
): Promise<Record<string, SearchResponse>> {
  return apiFetch<Record<string, SearchResponse>>("/v1/web-search/search/multi", {
    method: "POST",
    body: JSON.stringify(params),
  });
}
