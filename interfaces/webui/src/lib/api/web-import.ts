/**
 * ETHAN WebUI — Web Import API service
 *
 * Client passif du pipeline d'ingestion web Core (/v1/web-ingest).
 * Aucune logique ici : le scan (contrôlé), le preview, la validation et
 * l'indexation sont orchestrés par le Core ; la WebUI ne fait que
 * configurer, déclencher et visualiser la progression réelle.
 */

import { apiFetch } from "@/lib/api/client";

export interface WebScanPage {
	page_id: string;
	url: string;
	depth: number;
	status: "ok" | "disallowed" | "skipped" | "error";
	title: string;
	excerpt: string;
	text_length: number;
	content_hash: string | null;
	duplicate_of: string | null;
	error: string | null;
}

export interface WebScanPreview {
	scan_id: string;
	root_url: string;
	config: {
		max_pages: number;
		max_depth: number;
		use_sitemap: boolean;
		include_patterns: string[];
		exclude_patterns: string[];
	};
	sitemap_used: boolean;
	robots: { exists: boolean; crawl_delay: number };
	pages: WebScanPage[];
	created_at?: number;
}

export interface WebIngestResult {
	scan_id: string;
	target: "collection" | "knowledge";
	folder: { id: string; name: string } | null;
	collection: { id: string; name: string } | null;
	indexed: Array<{ document_id?: string; node_id?: string; url: string; title?: string }>;
	indexed_count: number;
	skipped_duplicates: Array<{ page_id: string; url: string; duplicate_of: string }>;
}

/** Scan contrôlé d'une URL → preview transient (aucune indexation). */
export async function scanWebUrl(data: {
	url: string;
	max_pages?: number;
	max_depth?: number;
	use_sitemap?: boolean;
	include_patterns?: string[];
	exclude_patterns?: string[];
}): Promise<WebScanPreview> {
	return apiFetch<WebScanPreview>("/v1/web-ingest/scan", {
		method: "POST",
		body: JSON.stringify(data),
	});
}

/** Re-affichage d'un preview (404 si inconnu ou expiré). */
export async function getWebScan(scanId: string): Promise<WebScanPreview> {
	return apiFetch<WebScanPreview>(`/v1/web-ingest/scans/${scanId}`);
}

/** Indexe les pages sélectionnées après validation utilisateur. */
export async function ingestWebPages(data: {
	scan_id: string;
	page_ids: string[];
	folder_id?: string | null;
	new_folder_name?: string;
	target: "collection" | "knowledge";
	collection_id?: string | null;
	new_collection_name?: string;
	retrieval_strategy?: string | null;
	embedding_model?: string | null;
	user_id?: string;
}): Promise<WebIngestResult> {
	return apiFetch<WebIngestResult>("/v1/web-ingest/ingest", {
		method: "POST",
		body: JSON.stringify(data),
	});
}