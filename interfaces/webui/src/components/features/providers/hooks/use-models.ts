"use client";

/**
 * useModels — Catalogue de modèles partagé (chat + workspace).
 *
 * Source unique : ETHAN Core.
 * - ``GET /models`` fournit le catalogue agrégé (modèles découverts des
 *   providers actifs + fiches custom du ModelStore) ;
 * - ``GET /providers`` fournit l'état des providers (activation, statut).
 *
 * Le catalogue est chargé une fois puis filtré côté client (recherche,
 * capacités) — aucune logique métier, aucun registre parallèle.
 * L'épinglage est une préférence UI locale (localStorage).
 */

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listProviders, type Provider } from "@/lib/api/providers";
import { listModels, type ModelInfo } from "@/lib/api/models";

const STORAGE_PINNED = "ethan.pinned-models";

export interface PinnedModel {
	providerId: string;
	modelId: string;
	pinnedAt: string;
}

const PROVIDERS_QUERY_KEY = ["providers"] as const;
const MODELS_QUERY_KEY = ["models", "catalog"] as const;
const PINNED_QUERY_KEY = ["pinned-models"] as const;

export function useModels() {
	const queryClient = useQueryClient();

	const {
		data: providers = [],
		isLoading: providersLoading,
		error: providersErrorObj,
	} = useQuery<Provider[]>({
		queryKey: PROVIDERS_QUERY_KEY,
		queryFn: () => listProviders(),
		staleTime: 30_000,
	});

	const {
		data: models = [],
		isLoading: modelsLoading,
		error: modelsErrorObj,
		refetch: refetchModels,
	} = useQuery<ModelInfo[]>({
		queryKey: MODELS_QUERY_KEY,
		queryFn: () => listModels({ include_custom: true }),
		staleTime: 30_000,
	});

	const enabledProviders = providers.filter((p) => p.enabled);

	const { data: pinned = [] } = useQuery<PinnedModel[]>({
		queryKey: PINNED_QUERY_KEY,
		queryFn: () => {
			if (typeof window === "undefined") return [];
			const raw = window.localStorage.getItem(STORAGE_PINNED);
			return raw ? (JSON.parse(raw) as PinnedModel[]) : [];
		},
		staleTime: Infinity,
	});

	const setPinnedMutation = useMutation({
		mutationFn: (next: PinnedModel[]) => {
			if (typeof window === "undefined") return Promise.resolve();
			window.localStorage.setItem(STORAGE_PINNED, JSON.stringify(next));
			return Promise.resolve();
		},
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: PINNED_QUERY_KEY });
		},
	});

	const pinModel = (providerId: string, modelId: string) => {
		const current = queryClient.getQueryData<PinnedModel[]>(PINNED_QUERY_KEY) || [];
		const exists = current.some(
			(p) => p.providerId === providerId && p.modelId === modelId,
		);
		if (exists) return;
		const next = [...current, { providerId, modelId, pinnedAt: new Date().toISOString() }];
		setPinnedMutation.mutate(next);
	};

	const unpinModel = (providerId: string, modelId: string) => {
		const current = queryClient.getQueryData<PinnedModel[]>(PINNED_QUERY_KEY) || [];
		const next = current.filter(
			(p) => !(p.providerId === providerId && p.modelId === modelId),
		);
		setPinnedMutation.mutate(next);
	};

	const isPinned = (providerId: string, modelId: string) => {
		return pinned.some((p) => p.providerId === providerId && p.modelId === modelId);
	};

	/** Recherche locale (nom, id technique, provider, capacités réelles). */
	const searchModels = (query: string): ModelInfo[] => {
		const q = query.toLowerCase().trim();
		if (!q) return models;
		return models.filter(
			(m) =>
				m.name.toLowerCase().includes(q) ||
				m.id.toLowerCase().includes(q) ||
				m.model.toLowerCase().includes(q) ||
				m.provider.toLowerCase().includes(q) ||
				(m.capabilities || []).some((c) => c.toLowerCase().includes(q)),
		);
	};

	// Sélection locale (workspace) — le chat utilise useActiveModel/model.store.
	const [selectedModel, setSelectedModel] = useState<ModelInfo | null>(null);

	return {
		// Providers (état Core)
		providers,
		enabledProviders,
		providersLoading,
		providersError: providersErrorObj?.message ?? null,

		// Catalogue de modèles (Core)
		models,
		modelsLoading,
		modelsError: modelsErrorObj?.message ?? null,
		refetchModels,
		/** @deprecated compat : consommé par model-selector.tsx */
		isLoading: providersLoading || modelsLoading,

		// Sélection locale (workspace)
		selectedModel,
		setSelectedModel,

		// Épinglage (préférence UI locale)
		pinned,
		pinModel,
		unpinModel,
		isPinned,

		// Recherche locale
		searchModels,
	};
}
