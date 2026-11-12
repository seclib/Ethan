import { apiFetch } from "@/lib/api/client";

/**
 * Client API Web Research (/v1/web-research).
 *
 * La WebUI est un simple adaptateur : toute la logique (recherche
 * multi-moteurs, sélection bornée au plafond absolu de 50 pages, aperçu
 * transient contrôlé, import Knowledge/Collection) vit dans le Core
 * (core/knowledge/web_research_service.py). Ce client ne fait que sérialiser
 * les requêtes et désérialiser les réponses.
 */

export interface ResearchPage {
  title: string;
  url: string;
  domain: string;
  snippet: string;
  source_engine: string;
  rank: number;
  metadata?: Record<string, unknown>;
}

export interface ResearchResult {
  query: string;
  engines: string[];
  results: ResearchPage[];
  total_found: number;
  max_results_per_engine: number;
  truncated: boolean;
  errors: Record<string, string>;
}

export interface CollectResponse {
  research: ResearchResult;
  max_pages_per_collection: number;
}

export interface PreviewPage {
  url: string;
  title: string;
  status: string;
  text: string;
}

export interface PreviewResponse {
  scan_id?: string;
  pages: PreviewPage[];
  errors?: unknown;
}

export interface ImportReportPage {
  url: string;
  title: string;
  domain: string;
  status: string;
  error: string | null;
  indexed_count: number;
  knowledge_ids?: string[];
  collection?: { id: string; name?: string } | null;
  document?: { id: string; status?: string; error?: string | null } | null;
}

export interface ImportReport {
  target: string;
  collection: { id: string; name?: string } | null;
  project?: { id: string } | null;
  pages: ImportReportPage[];
  imported_count: number;
  unreachable_count: number;
  failed_count: number;
  skipped_duplicates: number;
  indexed_count: number;
}

export interface CollectParams {
  query: string;
  engines?: string[];
  max_results_per_engine?: number;
  /** Identifiant de profil réseau — credentials Core-only (core/network). */
  network_profile?: string;
}

export function collectResearch(params: CollectParams): Promise<CollectResponse> {
  return apiFetch<CollectResponse>("/v1/web-research/collect", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export function previewResearchPage(url: string): Promise<PreviewResponse> {
  return apiFetch<PreviewResponse>("/v1/web-research/preview", {
    method: "POST",
    body: JSON.stringify({ url }),
  });
}

export function importResearchPage(params: {
  url: string;
  title?: string;
  domain?: string;
  collection_name?: string;
  target?: "knowledge" | "collection" | "project";
  project_id?: string;
}): Promise<ImportReport> {
  return apiFetch<ImportReport>("/v1/web-research/import-page", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export function importResearchSelection(params: {
  urls: string[];
  target?: "knowledge" | "collection" | "project";
  collection_name?: string;
  collection_id?: string;
  project_id?: string;
}): Promise<ImportReport> {
  return apiFetch<ImportReport>("/v1/web-research/import-selection", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export function fetchResearchLimits(): Promise<{
  max_pages_per_collection: number;
}> {
  return apiFetch("/v1/web-research/limits");
}
