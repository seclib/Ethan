/**
 * ETHAN WebUI — Tools / MCP API service
 *
 * Maps Open-WebUI tool server patterns to ETHAN API endpoints:
 *   OWUI: /api/v1/tools/servers         → ETHAN: /v1/tools/servers
 *
 * Tool servers are Core-owned (core/tools/servers.py). The WebUI only
 * displays and sends actions.
 */

import { apiFetch } from '@/lib/api/client';

export interface ToolServer {
	id: string;
	name: string;
	description?: string;
	enabled: boolean;
	status?: string;
	url?: string;
	metadata?: Record<string, unknown>;
	created_at?: string;
	updated_at?: string;
}

export interface CoreTool {
	id: string;
	name: string;
	description: string;
	parameters: Record<string, unknown>;
	version?: string;
	category: string;
	capabilities: string[];
	provider: "builtin" | "custom" | "mcp" | string;
	is_available: boolean;
	tags: string[];
	/** Champs du record Core (core/tools/manager.py `_tool_record`). */
	risk_level?: string;
	required_permissions?: string[];
	sandbox_required?: boolean;
	total_calls?: number;
	success_count?: number;
	metadata?: Record<string, unknown>;
	created_at?: string;
}

export interface CreateToolInput {
	name: string;
	description?: string;
	/** Schéma JSON des paramètres (objet). */
	parameters?: Record<string, unknown>;
	/** Définition seule : stockée en metadata, jamais exécutée par le Core. */
	code?: string;
	category?: string;
	capabilities?: string[];
	tags?: string[];
}

/** List the Core tool catalogue (builtin, custom and discovered MCP tools). */
export async function listTools(): Promise<CoreTool[]> {
	return apiFetch<CoreTool[]>('/v1/tools');
}

/**
 * Create a persistent custom Tool in ETHAN Core (POST /v1/tools).
 * Le Core valide : name requis, parameters = objet JSON (422 sinon).
 * `code` est stocké comme métadonnée — l'exécution reste dans le Core/Runtime.
 */
export async function createTool(data: CreateToolInput): Promise<CoreTool> {
	return apiFetch<CoreTool>('/v1/tools', {
		method: 'POST',
		body: JSON.stringify(data),
	});
}

/** Delete a custom tool — builtins et MCP sont refusés par le Core (422). */
export async function deleteTool(id: string): Promise<{ status: string }> {
	return apiFetch<{ status: string }>(`/v1/tools/${id}`, {
		method: 'DELETE',
	});
}

/** List all tool servers */
export async function listToolServers(enabled?: boolean): Promise<ToolServer[]> {
	const qs = enabled !== undefined ? `?enabled=${enabled}` : '';
	return apiFetch<ToolServer[]>(`/v1/tools/servers${qs}`);
}

/** Register a tool server */
export async function registerToolServer(data: Record<string, unknown>): Promise<ToolServer> {
	return apiFetch<ToolServer>('/v1/tools/servers', {
		method: 'POST',
		body: JSON.stringify(data),
	});
}

/** Get a single tool server */
export async function getToolServer(id: string): Promise<ToolServer> {
	return apiFetch<ToolServer>(`/v1/tools/servers/${id}`);
}

/** Update a tool server */
export async function updateToolServer(id: string, data: Record<string, unknown>): Promise<ToolServer> {
	return apiFetch<ToolServer>(`/v1/tools/servers/${id}`, {
		method: 'PUT',
		body: JSON.stringify(data),
	});
}

/** Set tool server status */
export async function setToolServerStatus(id: string, status: string): Promise<ToolServer> {
	return apiFetch<ToolServer>(`/v1/tools/servers/${id}/status`, {
		method: 'PUT',
		body: JSON.stringify({ status }),
	});
}

/** Delete a tool server */
export async function deleteToolServer(id: string): Promise<{ status: string }> {
	return apiFetch<{ status: string }>(`/v1/tools/servers/${id}`, {
		method: 'DELETE',
	});
}
