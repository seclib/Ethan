/**
 * ETHAN WebUI — RAG engine API service
 *
 * Configuration et statut du moteur RAG ETHAN Core (core/rag/pipeline.py).
 * Seuls les paramètres réellement supportés par le moteur sont exposés :
 * chunking, top_k, borne de contexte, modèle d'embedding et stratégie de
 * recherche (catalogue fourni par le Core — aucune stratégie inventée ici).
 */

import { apiFetch } from '@/lib/api/client';

/** Stratégie de recherche exposée par le Core (core/rag/strategies.py). */
export interface RagStrategyOption {
	id: string;
	label: string;
	description: string;
	requires_embeddings: boolean;
}

/** Recommandation calculée par le Core sur les capacités réelles du moteur. */
export interface RagStrategyRecommendation {
	strategy_id: string;
	reason: string;
	has_real_embeddings: boolean;
}

export interface RagConfig {
	chunk_size: number;
	chunk_overlap: number;
	top_k: number;
	max_context_chars: number;
	embedding_model: string | null;
	/** Stratégie globale par défaut (auto | keyword | semantic | hybrid). */
	strategy: string;
}

export interface RagStats {
	documents: number;
	chunks: number;
	/** "llm" = embeddings réels via provider ; "textual-fallback" = recherche lexicale. */
	embedding_mode: 'llm' | 'textual-fallback';
	indexed_embeddings: boolean;
	embedding_model: string | null;
	strategy: string;
	strategies: RagStrategyOption[];
	recommendation?: RagStrategyRecommendation;
}

export interface RagConfigResponse {
	config: RagConfig;
	stats: RagStats;
}

export interface RagStrategiesResponse {
	default: string;
	strategies: RagStrategyOption[];
	recommendation: RagStrategyRecommendation;
}

/** Configuration + statut du moteur RAG */
export async function getRagConfig(): Promise<RagConfigResponse> {
	return apiFetch<RagConfigResponse>('/v1/rag/config');
}

/** Catalogue des stratégies réellement implémentées dans le Core */
export async function getRagStrategies(): Promise<RagStrategiesResponse> {
	return apiFetch<RagStrategiesResponse>('/v1/rag/strategies');
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
