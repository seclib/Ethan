/**
 * ETHAN WebUI — Models API service
 *
 * Maps Open-WebUI model patterns to ETHAN API endpoints:
 *   OWUI: GET  /api/v1/models           → ETHAN: GET  /models
 *   OWUI: POST /api/v1/models            → ETHAN: POST /models
 *   OWUI: GET  /api/v1/models/{id}       → ETHAN: GET  /models/{id}
 *   OWUI: PUT  /api/v1/models/{id}       → ETHAN: PUT  /models/{id}
 *   OWUI: DEL  /api/v1/models/{id}       → ETHAN: DELETE /models/{id}
 *
 * Models are Core-owned (core/llm/model_store.py + core/llm/provider_manager.py).
 * The WebUI only displays and sends actions.
 */

import { apiFetch } from '@/lib/api/client';

export interface ModelInfo {
	id: string;
	name: string;
	/** Exact identifier sent to the selected provider. */
	model: string;
	provider: string;
	context_length: number;
	is_local: boolean;
	is_private: boolean;
	quality_score: number;
	capabilities: string[];
	is_available: boolean;
	is_custom: boolean;
	source: 'discovered' | 'custom';
	base_model_id?: string;
	params?: Record<string, unknown>;
	meta?: Record<string, unknown>;
	acl?: string[];
	created_at?: string;
	updated_at?: string;
}

/** List all models (discovered + custom) */
export async function listModels(params?: {
	provider_id?: string;
	include_custom?: boolean;
}): Promise<ModelInfo[]> {
	const qs = new URLSearchParams();
	if (params?.provider_id) qs.set('provider_id', params.provider_id);
	if (params?.include_custom !== undefined) qs.set('include_custom', String(params.include_custom));
	const suffix = qs.toString() ? `?${qs}` : '';
	return apiFetch<ModelInfo[]>(`/models${suffix}`);
}

/** Search models */
export async function searchModels(query: string): Promise<ModelInfo[]> {
	return apiFetch<ModelInfo[]>(`/models/search?q=${encodeURIComponent(query)}`);
}

/** Get a single model */
export async function getModel(id: string): Promise<ModelInfo> {
	return apiFetch<ModelInfo>(`/models/${id}`);
}

/** Create a custom model card */
export async function createModel(data: {
	name: string;
	model?: string;
	base_model_id?: string;
	params?: Record<string, unknown>;
	meta?: Record<string, unknown>;
	is_active?: boolean;
	acl?: string[];
}): Promise<ModelInfo> {
	return apiFetch<ModelInfo>('/models', {
		method: 'POST',
		body: JSON.stringify(data),
	});
}

/** Update a custom model card */
export async function updateModel(id: string, data: Record<string, unknown>): Promise<ModelInfo> {
	return apiFetch<ModelInfo>(`/models/${id}`, {
		method: 'PUT',
		body: JSON.stringify(data),
	});
}

/** Delete a custom model card */
export async function deleteModel(id: string): Promise<{ status: string; model_id: string }> {
	return apiFetch<{ status: string; model_id: string }>(`/models/${id}`, {
		method: 'DELETE',
	});
}

/** Toggle model active state */
export async function toggleModel(id: string): Promise<ModelInfo> {
	return apiFetch<ModelInfo>(`/models/${id}/toggle`, {
		method: 'POST',
	});
}
