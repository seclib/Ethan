"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listProviders, type Provider } from "@/lib/api/providers";
import { listModels, type ModelInfo } from "@/lib/api/models";
import { useUIStore } from "@/store/ui.store";

const STORAGE_PINNED = "ethan.pinned-models";

export interface PinnedModel {
	providerId: string;
	modelId: string;
	pinnedAt: string;
}

/**
 * Hook avancé pour la gestion des modèles.
 * - Sélection d'un provider (clic souris) → lazy-load des modèles
 * - Recherche par nom/capabilities
 * - Épinglage des modèles favoris (localStorage)
 * - Filtrage par provider
 */
export function useModels() {
	const queryClient = useQueryClient();
	const addToast = useUIStore((s) => s.addToast);

	// Provider sélectionné — null = aucun provider choisi (Vue principale)
	const [selectedProvider, setSelectedProvider] = useState<string | null>(null);

	const {
		data: providers = [],
		isLoading: providersLoading,
		error: providersErrorObj,
	} = useQuery<Provider[]>({
		queryKey: ["providers"],
		queryFn: () => listProviders(),
		staleTime: 30_000,
	});

	// Lazy-load des modèles UNIQUEMENT quand un provider est sélectionné
	const {
		data: models = [],
		isLoading: modelsLoading,
		error: modelsErrorObj,
		refetch: refetchModels,
	} = useQuery<ModelInfo[]>({
		queryKey: ["models", selectedProvider],
		queryFn: () => listModels(selectedProvider ? { provider_id: selectedProvider } : undefined),
		staleTime: 30_000,
	});

	const enabledProviders = providers.filter((p) => p.enabled);

	const { data: pinned = [] } = useQuery<PinnedModel[]>({
		queryKey: ["pinned-models"],
		queryFn: () => {
			if (typeof window === "undefined") return [];
			const raw = window.localStorage.getItem(STORAGE_PINNED);
			return raw ? JSON.parse(raw) : [];
		},
		staleTime: Infinity,
	});

	const setPinnedMutation = useMutation({
		mutationFn: (pinned: PinnedModel[]) => {
			if (typeof window === "undefined") return Promise.resolve();
			window.localStorage.setItem(STORAGE_PINNED, JSON.stringify(pinned));
			return Promise.resolve();
		},
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ["pinned-models"] });
		},
	});

	const pinModel = (providerId: string, modelId: string) => {
		const current = queryClient.getQueryData<PinnedModel[]>(["pinned-models"]) || [];
		const exists = current.some(
			(p) => p.providerId === providerId && p.modelId === modelId,
		);
		if (exists) return;
		const next = [...current, { providerId, modelId, pinnedAt: new Date().toISOString() }];
		setPinnedMutation.mutate(next);
	};

	const unpinModel = (providerId: string, modelId: string) => {
		const current = queryClient.getQueryData<PinnedModel[]>(["pinned-models"]) || [];
		const next = current.filter(
			(p) => !(p.providerId === providerId && p.modelId === modelId),
		);
		setPinnedMutation.mutate(next);
	};

	const isPinned = (providerId: string, modelId: string) => {
		return pinned.some((p) => p.providerId === providerId && p.modelId === modelId);
	};

	const searchModels = (query: string): ModelInfo[] => {
		const q = query.toLowerCase().trim();
		if (!q) return models;
		return models.filter(
			(m) =>
				m.name.toLowerCase().includes(q) ||
				m.id.toLowerCase().includes(q) ||
				m.provider.toLowerCase().includes(q) ||
				(m.capabilities || []).some((c) => c.toLowerCase().includes(q)),
		);
	};

	// Modèle sélectionné (pour configuration)
	const [selectedModel, setSelectedModel] = useState<ModelInfo | null>(null);

	return {
		// Providers
		providers,
		enabledProviders,
		providersLoading,
		providersError: providersErrorObj?.message ?? null,
		selectedProvider,
		setSelectedProvider,

		// Models (liés au provider sélectionné ; tous si aucun provider choisi)
		models,
		/** @deprecated compat : consommé par model-selector.tsx */
		isLoading: providersLoading || modelsLoading,
		modelsLoading,
		modelsError: modelsErrorObj?.message ?? null,
		refetchModels,

		// Sélection de modèle
		selectedModel,
		setSelectedModel,

		// Actions
		pinned,
		pinModel,
		unpinModel,
		isPinned,
		searchModels,
	};
}
