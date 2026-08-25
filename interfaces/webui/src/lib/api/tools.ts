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
	category: string;
	capabilities: string[];
	provider: "builtin" | "custom" | "mcp" | string;
	is_available: boolean;
	tags: string[];
}

/** List the Core tool catalogue (builtin, custom and discovered MCP tools). */
export async function listTools(): Promise<CoreTool[]> {
	return apiFetch<CoreTool[]>('/v1/tools');
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
