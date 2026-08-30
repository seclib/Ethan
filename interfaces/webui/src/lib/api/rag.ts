/**
 * ETHAN WebUI — RAG engine API service
 *
 * Configuration et statut du moteur RAG ETHAN Core (core/rag/pipeline.py).
 * Seuls les paramètres réellement supportés par le moteur sont exposés :
 * chunking, top_k, borne de contexte, modèle d'embedding.
 * Pas de vector store externe : le moteur n'en utilise pas.
 */

import { apiFetch } from '@/lib/api/client';

export interface RagConfig {
	chunk_size: number;
	chunk_overlap: number;
	top_k: number;
	max_context_chars: number;
	embedding_model: string | null;
}

export interface RagStats {
	documents: number;
	chunks: number;
	/** "llm" = embeddings réels via provider ; "textual-fallback" = recherche lexicale. */
	embedding_mode: 'llm' | 'textual-fallback';
	indexed_embeddings: boolean;
	embedding_model: string | null;
}

export interface RagConfigResponse {
	config: RagConfig;
	stats: RagStats;
}

/** Configuration + statut du moteur RAG */
export async function getRagConfig(): Promise<RagConfigResponse> {
	return apiFetch<RagConfigResponse>('/v1/rag/config');
}

/** Statut d'indexation */
export async function getRagStatus(): Promise<RagStats> {
	return apiFetch<RagStats>('/v1/rag/status');
}

/** Applique et persiste la configuration du moteur */
export async function updateRagConfig(
	data: Partial<Omit<RagConfig, 'embedding_model'>> & { embedding_model?: string },
): Promise<RagConfigResponse> {
	return apiFetch<RagConfigResponse>('/v1/rag/config', {
		method: 'PUT',
		body: JSON.stringify(data),
	});
}
