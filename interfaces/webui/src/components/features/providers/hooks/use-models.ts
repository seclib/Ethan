"use client";

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
 * - Recherche par nom/capabilities
 * - Épinglage des modèles favoris (localStorage)
 * - Filtrage par provider
 */
export function useModels() {
	const queryClient = useQueryClient();
	const addToast = useUIStore((s) => s.addToast);

	const { data: providers = [], isLoading: providersLoading } = useQuery<Provider[]>({
		queryKey: ["providers"],
		queryFn: () => listProviders(),
	});

	const { data: models = [], isLoading: modelsLoading } = useQuery<ModelInfo[]>({
		queryKey: ["models"],
		queryFn: () => listModels(),
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

	return {
		providers,
		enabledProviders,
		models,
		isLoading: providersLoading || modelsLoading,
		pinned,
		pinModel,
		unpinModel,
		isPinned,
		searchModels,
	};
}
