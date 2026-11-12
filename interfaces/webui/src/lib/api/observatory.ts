/**
 * ETHAN WebUI — Observatory API client
 *
 * Couche fine au-dessus des routes Engineering Memory du Core
 * (`interfaces/api/routers/engineering_memory.py`). Tous les appels sont
 * en lecture seule, lecture documentaire incluse — le vault d'archives
 * n'est jamais modifié depuis l'interface.
 */

import { apiFetch } from '@/lib/api/client';

/** Nœud d'arborescence du vault. */
export interface VaultNode {
	type: 'directory' | 'file';
	name: string;
	/** Chemin relatif à la racine du vault (fichiers). */
	path: string;
	children?: VaultNode[];
	/** Champs présents uniquement pour les fichiers. */
	extension?: string;
	size_bytes?: number;
	modified_at?: string;
	markdown?: boolean;
}

/** Fichier du vault avec contenu. */
export interface VaultFile extends VaultNode {
	content: string;
	line_count: number;
	markdown: boolean;
}

export interface VaultSearchHit {
	path: string;
	line: number;
	snippet: string;
}

export interface VaultSearchResponse {
	query: string;
	hits: VaultSearchHit[];
}

export interface VaultBacklink {
	path: string;
	name: string;
	excerpts: string[];
}

export interface VaultBacklinkResponse {
	path: string;
	backlinks: VaultBacklink[];
}

export interface VaultGraphNode {
	id: string;
	label: string;
	path: string;
}

export interface VaultGraphResponse {
	nodes: VaultGraphNode[];
	edges: Array<{ source: string; target: string }>;
}

/** Enregistrement Engineering Memory (champs principaux). */
export interface EngineeringRecord {
	id: string;
	record_type: string;
	title: string;
	status: string;
	source_of_fact: string;
	provenance_level: string;
	components: string[];
	created_at: string;
	updated_at: string;
	evidence_refs: string[];
	authors: string[];
	origin: string;
	confidence: string;
	notes: string;
	tags: string[];
}

export interface EngineeringRecordsResponse {
	results: EngineeringRecord[];
}

export interface EngineeringMemoryIntegrity {
	root: string;
	markdown_files: number;
	valid_records: number;
	invalid_records: string[];
	registry_destination: string;
}

export interface ComponentHistoryResponse {
	component: string;
	history: EngineeringRecord[];
}

export async function listVaultTree(): Promise<VaultNode> {
	return apiFetch<VaultNode>('/v1/memory/vault/tree');
}

export async function readVaultFile(path: string): Promise<VaultFile> {
	const params = new URLSearchParams({ path });
	return apiFetch<VaultFile>(`/v1/memory/vault/file?${params}`);
}

export async function searchVault(
	query: string,
	options?: { limit?: number; extensions?: string },
): Promise<VaultSearchResponse> {
	const params = new URLSearchParams({ q: query });
	if (options?.limit) params.set('limit', String(options.limit));
	if (options?.extensions) params.set('extensions', options.extensions);
	return apiFetch<VaultSearchResponse>(`/v1/memory/vault/search?${params}`);
}

export async function listVaultBacklinks(path: string): Promise<VaultBacklinkResponse> {
	const params = new URLSearchParams({ path });
	return apiFetch<VaultBacklinkResponse>(`/v1/memory/vault/backlinks?${params}`);
}

export async function resolveVaultWikilink(wikilink: string): Promise<{ resolved: string | null; raw: string }> {
	const params = new URLSearchParams({ wikilink });
	return apiFetch<{ resolved: string | null; raw: string }>(`/v1/memory/vault/resolve?${params}`);
}

export async function writeVaultFile(path: string, content: string): Promise<VaultFile> {
	return apiFetch<VaultFile>('/v1/memory/vault/file', {
		method: 'POST',
		body: JSON.stringify({ path, content }),
	});
}

export async function getVaultGraph(limitNodes = 150): Promise<VaultGraphResponse> {
	const params = new URLSearchParams({ limit_nodes: String(limitNodes) });
	return apiFetch<VaultGraphResponse>(`/v1/memory/vault/graph?${params}`);
}

export async function listEngineeringRecords(options?: {
	record_type?: string;
	component?: string;
	status?: string;
	limit?: number;
}): Promise<EngineeringRecord[]> {
	const params = new URLSearchParams();
	if (options?.record_type) params.set('record_type', options.record_type);
	if (options?.component) params.set('component', options.component);
	if (options?.status) params.set('status', options.status);
	if (options?.limit) params.set('limit', String(options.limit));
	const suffix = params.size ? `?${params}` : '';
	const response = await apiFetch<EngineeringRecordsResponse>(`/v1/memory/records${suffix}`);
	return response.results ?? [];
}

export async function getComponentHistory(component: string): Promise<ComponentHistoryResponse> {
	return apiFetch<ComponentHistoryResponse>(`/v1/memory/components/${encodeURIComponent(component)}/history`);
}

export async function getMemoryIntegrity(): Promise<EngineeringMemoryIntegrity> {
	return apiFetch<EngineeringMemoryIntegrity>('/v1/memory/health');
}
