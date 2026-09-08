/**
 * ETHAN WebUI — Providers API service
 *
 * Maps Open-WebUI provider patterns to ETHAN API endpoints:
 *   OWUI: GET  /api/v1/providers         → ETHAN: GET  /providers
 *   OWUI: PUT  /api/v1/providers/{id}    → ETHAN: PUT  /providers/{id}
 *   OWUI: POST /api/v1/providers         → ETHAN: POST /providers
 *   OWUI: DEL  /api/v1/providers/{id}     → ETHAN: DELETE /providers/{id}
 *
 * Providers are Core-owned (core/llm/provider_manager.py).
 * The WebUI only displays and sends actions.
 */

import { apiFetch } from '@/lib/api/client';

export interface Provider {
	id: string;
	name: string;           // nom d'affichage (backend renvoie "name")
	type: string;
	enabled: boolean;
	status: string;
	default_model: string;
	is_default: boolean;
	base_url: string;
	models: string[];
	/** true si le Core a une clé/token configurée pour ce provider. */
	key_exists?: boolean;
	/** Capacités normalisées du modèle unifié (llm, vision, embedding, speech_to_text, transcription). */
	capabilities?: string[];
	/** true si une clé API est configurée (la clé elle-même n'est jamais renvoyée). */
	has_api_key?: boolean;
}

export interface ProviderUpdate {
	base_url?: string;
	api_key?: string;
	default_model?: string;
	display_name?: string;
	enabled?: boolean;
	options?: Record<string, unknown>;
}

export interface ProviderCreate {
	name: string;
	type: string;
	base_url?: string;
	api_key?: string;
	default_model?: string;
	display_name?: string;
	enabled?: boolean;
	options?: Record<string, unknown>;
}

/** List all providers */
// uses "name" as the display name field (display_name is write-only in ProviderCreate).

export interface TestConnectionResult {
	provider_id: string;
	connected: boolean;
	status: string;
	message: string;
}

/** List all providers */
export async function listProviders(): Promise<Provider[]> {
	return apiFetch<Provider[]>('/providers');
}

/** Get a single provider */
export async function getProvider(id: string): Promise<Provider> {
	return apiFetch<Provider>(`/providers/${id}`);
}

/** Create a new provider */
export async function createProvider(data: ProviderCreate): Promise<Provider> {
	return apiFetch<Provider>('/providers', {
		method: 'POST',
		body: JSON.stringify(data),
	});
}

/** Update a provider */
export async function updateProvider(
	id: string,
	data: ProviderUpdate,
): Promise<Provider> {
	return apiFetch<Provider>(`/providers/${id}`, {
		method: 'PUT',
		body: JSON.stringify(data),
	});
}

/** Delete a provider */
export async function deleteProvider(id: string): Promise<{ status: string; provider_id: string }> {
	return apiFetch<{ status: string; provider_id: string }>(`/providers/${id}`, {
		method: 'DELETE',
	});
}

/** Test connection to a provider */
export async function testProviderConnection(id: string): Promise<TestConnectionResult> {
	return apiFetch<TestConnectionResult>(`/providers/${id}/test`, {
		method: 'POST',
	});
}

/** Set a provider as default */
export async function setDefaultProvider(id: string): Promise<Provider> {
	return apiFetch<Provider>(`/providers/${id}/default`, {
		method: 'PUT',
	});
}

/** List models for a specific provider */
export async function listProviderModels(id: string): Promise<unknown[]> {
	return apiFetch<unknown[]>(`/providers/${id}/models`);
}

/** Provider capabilities (vision, transcription, embedding, speech_to_text) */
export interface ProviderCapabilities {
	provider_id: string;
	name: string;
	/** Capacités normalisées du modèle unifié. */
	capabilities: string[];
	supports_vision: boolean;
	supports_transcription: boolean;
	supports_speech_to_text: boolean;
	supports_embedding: boolean;
}

/** Get provider capabilities */
export async function getProviderCapabilities(id: string): Promise<ProviderCapabilities> {
	return apiFetch<ProviderCapabilities>(`/providers/${id}/capabilities`);
}

/** Supported provider types for the create dialog */
export const SUPPORTED_PROVIDER_TYPES = [
	'ollama',
	'openai',
	'azure',
	'anthropic',
	'vllm',
	'llamacpp',
	'lmstudio',
	'gemini',
	'openai-compatible',
	'openrouter',
	'custom',
] as const;

export type ProviderType = (typeof SUPPORTED_PROVIDER_TYPES)[number];

/** Default base URLs per provider type */
export const PROVIDER_DEFAULT_URLS: Record<string, string> = {
	ollama: 'http://localhost:11434',
	vllm: 'http://localhost:8000',
	llamacpp: 'http://localhost:8080',
	lmstudio: 'http://localhost:1234',
	'openai-compatible': 'http://localhost:8000/v1',
};

