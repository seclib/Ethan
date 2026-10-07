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
	/**
	 * Identifiant du PROVIDER (service) qui sert ce modèle — jamais un
	 * identifiant de modèle. Vide si le Core ne connaît pas de provider
	 * pour cette entrée (fiche custom sans provider déclaré) : l'interface
	 * affiche alors « provider non déclaré » au lieu d'inventer un service.
	 */
	provider: string;
	context_length: number;
	is_local: boolean;
	is_private: boolean;
	quality_score: number;
	capabilities: string[];
	/**
	 * Joignabilité. Pour un modèle découvert = réellement servi par le
	 * provider. Pour une fiche custom = activation administrative
	 * (le Core ne peut pas tester la joignabilité d'une fiche) : lire
	 * `is_active` pour la notion d'activation.
	 */
	is_available: boolean;
	/**
	 * Activation locale. `null` pour un modèle découvert (aucune activation
	 * locale : l'état suit le provider), `boolean` pour une fiche custom.
	 */
	is_active?: boolean | null;
	is_custom: boolean;
	source: 'discovered' | 'custom';
	/** Tarifs déclarés par l'adapter Core (ex: {input, output}) — null si absents. */
	pricing?: Record<string, unknown> | null;
	/** Latence moyenne déclarée par l'adapter Core (ms) — null si absente. */
	avg_latency_ms?: number | null;
	/**
	 * Modèle découvert servant de base à une fiche custom. Ce n'est PAS un
	 * provider : à ne jamais afficher dans la colonne « Provider ».
	 */
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
	/** Provider (service) qui sert ce modèle — routage et filtre par provider. */
	provider?: string;
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

// ── Model Hub types ──────────────────────────────────────────────────────

export interface HubModelCompatibility {
	compatible: boolean;
	fit_level: string;
	reason: string;
	recommendation: string;
	recommended_runtime: string;
	supported_runtimes: string[];
	ram_required_gb: number;
	vram_required_gb: number;
	estimated_speed_tps: number | null;
	status: string;
	status_label: string;
	execution_method: string;
}

export interface HubModel {
	id: string;
	name: string;
	provider: string;
	repo_id?: string;
	params_b: number;
	description: string;
	use_case: string;
	quantization: string;
	source: string;
	formats_available: string[];
	is_installed: boolean;
	compatibility: HubModelCompatibility;
}

export interface ModelInspection {
	model_id: string;
	can_run: boolean;
	status: string;
	status_label: string;
	method: string;
	formats_available: string[];
	is_gated: boolean;
	params_b: number;
	conversion_supported: boolean;
	reason: string;
	recommendation: string;
	estimated_speed_tps: number | null;
	compatibility: HubModelCompatibility;
}

export interface InstalledModel {
	id: string;
	name: string;
	provider: string;
	is_local: boolean;
	source: string;
	context_length: number;
	capabilities: string[];
}

export interface HardwareInfo {
	total_ram_gb: number;
	available_ram_gb: number;
	cpu_cores: number;
	gpu_count: number;
	gpu_name: string;
	gpu_vram_gb: number;
	gpu_vram_free_gb: number;
	backend: string;
	memory_bandwidth_gb_s: number;
}

export interface RuntimeHealth {
	status: string;
	runtimes: Record<string, {
		enabled: boolean;
		reachable: boolean;
		latency_ms?: number;
	}>;
}

// ── Model Hub API functions ──────────────────────────────────────────────

/** Discover models from catalog + Hugging Face with hardware compatibility */
export async function discoverModels(params?: {
	q?: string;
	use_case?: string;
	source?: string;
}): Promise<HubModel[]> {
	const qs = new URLSearchParams();
	if (params?.q) qs.set('q', params.q);
	if (params?.use_case) qs.set('use_case', params.use_case);
	if (params?.source) qs.set('source', params.source);
	const suffix = qs.toString() ? `?${qs}` : '';
	return apiFetch<HubModel[]>(`/models/discover${suffix}`);
}

/** Inspect a model: can it run on this machine? By what method? */
export async function inspectModel(modelId: string): Promise<ModelInspection> {
	return apiFetch<ModelInspection>(`/models/inspect/${encodeURIComponent(modelId)}`);
}

/** Install a model via ETHAN Core (Ollama pull, HF download, etc.) */
export async function installModel(payload: {
	model: string;
	provider?: string;
}): Promise<{ success: boolean; message: string; provider?: string }> {
	return apiFetch<{ success: boolean; message: string; provider?: string }>('/models/install', {
		method: 'POST',
		body: JSON.stringify(payload),
	});
}

/** List all installed models */
export async function getInstalledModels(): Promise<InstalledModel[]> {
	return apiFetch<InstalledModel[]>('/models/installed');
}

/** Get hardware info for the host machine */
export async function getHardwareInfo(): Promise<HardwareInfo> {
	return apiFetch<HardwareInfo>('/models/hardware');
}

/** Check runtime health */
export async function getRuntimesHealth(): Promise<RuntimeHealth> {
	return apiFetch<RuntimeHealth>('/models/runtimes/health');
}

export interface DownloadItem {
	id: string;
	repo_id: string;
	runtime: string;
	status: 'starting' | 'downloading' | 'completed' | 'failed';
	percent: number;
	error?: string | null;
	created_at: number;
	updated_at: number;
}

/** List all active and past model downloads */
export async function getDownloads(): Promise<DownloadItem[]> {
	return apiFetch<DownloadItem[]>('/models/downloads');
}

