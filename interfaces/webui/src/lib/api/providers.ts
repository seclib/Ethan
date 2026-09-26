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
	/** Méthodes d'authentification supportées ("api_key", "user_account") — source de vérité : Core. */
	auth_methods?: string[];
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

/**
 * Catalogue des types de providers — renvoyé par ETHAN Core
 * (GET /providers/catalog). Le WebUI ne maintient AUCUNE liste parallèle :
 * types, URLs par défaut, méthodes d'authentification et capacités
 * proviennent du Core.
 */
export interface ProviderTypeCatalogEntry {
	id: string;
	/** URL par défaut du type ("" si aucun endpoint imposé — providers cloud). */
	default_base_url: string;
	/** Méthodes d'authentification déclarées par le Core (api_key, …). */
	auth_methods: string[];
	/** Capacités canoniques déclarées par le Core pour ce type. */
	capabilities: string[];
}

export interface ProviderCatalog {
	types: ProviderTypeCatalogEntry[];
	/** Vocabulaire canonique des capacités provider (ProviderCapability). */
	provider_capabilities: string[];
}

/** Get the Core provider catalog (types, default URLs, auth, capabilities) */
export async function getProviderCatalog(): Promise<ProviderCatalog> {
	return apiFetch<ProviderCatalog>('/providers/catalog');
}

