/**
 * ETHAN WebUI — MCP Servers API service
 *
 * Contrat Core réel (core/tools/servers.py` + `interfaces/api/routers/capabilities.py`) :
 *   - GET/POST /v1/tools/servers · GET/PUT/DELETE /v1/tools/servers/{id}
 *   - POST /v1/tools/servers/{id}/sync   (connexion réelle + découverte)
 *   - PUT /status = statut de connexion ; l'activation/désactivation passe
 *     par PUT /v1/tools/servers/{id} { enabled }.
 *   - Secrets : le Core ne renvoie jamais tokens/headers (auth_config =
 *     { token_set }, metadata.header_keys). Les payloads d'envoi portent
 *     `auth_config.token` et `headers` — jamais relus depuis le serveur.

 *   - `transport` / `command` / `args` / `headers` sont fusionnés dans
 *     `metadata` par le routeur (les réponses les exposent donc sous metadata).
 */

import { apiFetch } from '@/lib/api/client';

export type McpTransport = "http" | "sse" | "stdio";
export type McpStatus = "connected" | "disconnected" | "error" | "unknown" | string;

export interface McpServer {
  id: string;
  name: string;
  url?: string;
  description?: string;
  auth_type?: "none" | "bearer" | "api_key" | string;
  /** Version publique : le token n'est jamais renvoyé — juste le fait qu'il existe. */
  auth_config?: { token_set?: boolean };
  enabled: boolean;
  status: McpStatus;
  last_connected_at?: string | null;
  metadata?: {
    transport?: McpTransport;
    command?: string;
    args?: string[];
    /** Clés des en-têtes HTTP configurés (jamais leurs valeurs). */
    header_keys?: string[];
  };
  created_at?: string;
  updated_at?: string;
}

export interface CreateMcpServerInput {
  name: string;
  description?: string;
  transport: McpTransport;
  url?: string;
  command?: string;
  args?: string[];
  /** En-têtes à envoyer au moment de la création (clé : valeur). */
  headers?: Record<string, string>;
  auth_type?: "none" | "bearer" | "api_key";
  /** Token à envoyer — jamais renvoyé par le Core après stockage. */
  auth_config?: { token?: string };
  enabled?: boolean;
}

export interface UpdateMcpServerInput {
  name?: string;
  description?: string;
  transport?: McpTransport;
  url?: string;
  command?: string;
  args?: string[];
  headers?: Record<string, string>;
  auth_type?: "none" | "bearer" | "api_key";
  /** Optionnel : si absent, le token existant est conservé côté Core. */
  auth_config?: { token?: string };
  enabled?: boolean;
}

export async function getMcpServers(): Promise<McpServer[]> {
	return apiFetch<McpServer[]>('/v1/tools/servers');
}

export async function getMcpServer(serverId: string): Promise<McpServer> {
	return apiFetch<McpServer>(`/v1/tools/servers/${serverId}`);
}

export async function addMcpServer(data: CreateMcpServerInput): Promise<McpServer> {
	return apiFetch<McpServer>('/v1/tools/servers', {
		method: 'POST',
		body: JSON.stringify(data),
	});
}

export async function updateMcpServer(serverId: string, data: UpdateMcpServerInput): Promise<McpServer> {
	return apiFetch<McpServer>(`/v1/tools/servers/${serverId}`, {
		method: 'PUT',
		body: JSON.stringify(data),
	});
}

/** Activer/désactiver un serveur — passe par update ({ enabled }), pas par /status. */
export async function toggleMcpServer(serverId: string, enabled: boolean): Promise<McpServer> {
	return updateMcpServer(serverId, { enabled });
}

export async function deleteMcpServer(serverId: string): Promise<{ status: string }> {
	return apiFetch<{ status: string }>(`/v1/tools/servers/${serverId}`, {
		method: 'DELETE',
	});
}

export interface McpSyncResult {
  status: string;
  tools_discovered: number;
  tools: Array<{ name: string; description: string; parameters: unknown }>;
  error?: string;
}

/**
 * Synchronise = teste la connexion réelle au serveur MCP et découvre ses tools.

 * Le Core connecte via le SDK officiel mcp (http/stdio), met à jour le statut
 * (connected/error) et enregistre les tools découverts dans le registre.

 * Cas réel défendu : avec un faux serveur MCP et un client MCP réels (et
 * non direct) — le Core connecte au serveur candidat par le protocole.

 * Remarque sur le SDK : l'enregistrement du tool MCP passe par le Core
 * (metadata.mcp_server_id) — le WebUI ne lit que le catalogue.

 * La réponse exposes `tools_discovered` (pas tool_count) et la liste tool.

 */
export async function syncMcpServer(serverId: string): Promise<McpSyncResult> {
	return apiFetch<McpSyncResult>(`/v1/tools/servers/${serverId}/sync`, {
		method: 'POST',
	});
}