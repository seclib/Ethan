/**
 * ETHAN WebUI — Agents API service
 *
 * Maps Open-WebUI agent patterns to ETHAN API endpoints:
 *   OWUI: /api/v1/agents         → ETHAN: /v1/agents
 *
 * Agents are Core-owned (core/agents). The WebUI only displays and sends actions.
 * Types are the canonical ones from @/types.
 */

import { apiFetch } from '@/lib/api/client';
import type { Agent } from '@/types';

export async function listAgents(): Promise<Agent[]> {
	return apiFetch<Agent[]>('/v1/agents');
}

export async function getAgent(id: string): Promise<Agent> {
	return apiFetch<Agent>(`/v1/agents/${id}`);
}

export async function createAgent(data: {
	name: string;
	description?: string;
	capabilities?: string[];
	model?: string;
	provider?: string;
	skill_ids?: string[];
	knowledge_collection_ids?: string[];
	knowledge_ids?: string[];
	tool_ids?: string[];
	folder_ids?: string[];
	metadata?: Record<string, unknown>;
}): Promise<Agent> {
	return apiFetch<Agent>('/v1/agents', {
		method: 'POST',
		body: JSON.stringify(data),
	});
}

/** Arbre des ressources effectivement autorisées à un agent (résolu par le Core). */
export interface AgentResources {
	agent_id: string;
	folders: Array<{
		id: string;
		name: string;
		resources: Array<{ resource_type: string; resource_id: string; name: string }>;
	}>;
	knowledge: Array<{ id: string; name: string; source: string }>;
	collections: Array<{ id: string; name: string; source: string }>;
	skills: Array<{ id: string; name: string; source: string }>;
	tools: Array<{ id: string; name: string; provider: string; source: string }>;
	ghosts: Array<{ resource_type: string; resource_id: string }>;
}

export async function getAgentResources(id: string): Promise<AgentResources> {
	return apiFetch<AgentResources>(`/v1/agents/${id}/resources`);
}

export async function updateAgent(id: string, data: Record<string, unknown>): Promise<Agent> {
	return apiFetch<Agent>(`/v1/agents/${id}`, {
		method: 'PUT',
		body: JSON.stringify(data),
	});
}

export async function deleteAgent(id: string): Promise<{ status: string }> {
	return apiFetch<{ status: string }>(`/v1/agents/${id}`, {
		method: 'DELETE',
	});
}

export interface AgentExecutionResult {
	id: string;
	agent_id: string;
	task: string;
	status: string;
	result?: unknown;
	error?: string | null;
	skill_id?: string | null;
	created_at: string;
	completed_at?: string | null;
}

/** Execute a task through the Core agent executor (real LLM). */
export async function executeAgent(
	id: string,
	data: { task: string; context?: Record<string, unknown>; skill_id?: string },
): Promise<AgentExecutionResult> {
	return apiFetch<AgentExecutionResult>(`/v1/agents/${id}/execute`, {
		method: 'POST',
		body: JSON.stringify(data),
	});
}

export type { Agent };