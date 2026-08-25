"use client";

import { useState, useEffect, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listProviders, setDefaultProvider, type Provider } from "@/lib/api/providers";
import { listProviderModels } from "@/lib/api/providers";
import { useUIStore } from "@/store/ui.store";

const STORAGE_PROVIDER = "ethan.active-provider";
const STORAGE_MODEL = "ethan.active-model";

/**
 * Hook centralisé de sélection du moteur IA actif.
 * - Charge les providers via /providers (ProviderManager Core)
 * - Restaure la préférence utilisateur (localStorage) sans rechargement
 * - Synchronise le provider par défaut côté backend (PUT /providers/{id}/default)
 * - Expose le modèle actif pour le chat (commande /model, footer des réponses)
 */
export function useActiveModel() {
	const queryClient = useQueryClient();
	const addToast = useUIStore((s) => s.addToast);

	const { data: providers = [] } = useQuery<Provider[]>({
		queryKey: ["providers"],
		queryFn: () => listProviders(),
	});

	const defaultProvider = providers.find((p) => p.is_default) || providers.find((p) => p.enabled);

	const [selectedProviderId, setSelectedProviderId] = useState<string>(() => {
		if (typeof window === "undefined") return "";
		return window.localStorage.getItem(STORAGE_PROVIDER) || "";
	});

	const [selectedModel, setSelectedModel] = useState<string>(() => {
		if (typeof window === "undefined") return "";
		return window.localStorage.getItem(STORAGE_MODEL) || "";
	});

	// Résolution du provider par défaut une fois les providers chargés
	useEffect(() => {
		if (defaultProvider && !selectedProviderId) {
			setSelectedProviderId(defaultProvider.id);
			setSelectedModel(defaultProvider.default_model || "");
		}
	}, [defaultProvider, selectedProviderId]);

	// Persistance de la préférence utilisateur
	useEffect(() => {
		if (selectedProviderId) window.localStorage.setItem(STORAGE_PROVIDER, selectedProviderId);
	}, [selectedProviderId]);

	useEffect(() => {
		if (selectedModel) window.localStorage.setItem(STORAGE_MODEL, selectedModel);
	}, [selectedModel]);

	const activeProvider = providers.find((p) => p.id === selectedProviderId) || defaultProvider;

	const { data: models = [] } = useQuery<unknown[]>({
		queryKey: ["provider-models", selectedProviderId],
		queryFn: () => listProviderModels(selectedProviderId),
		enabled: !!selectedProviderId,
	});

	const setDefaultMutation = useMutation({
		mutationFn: (id: string) => setDefaultProvider(id),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ["providers"] });
			addToast({ type: "success", message: "Active engine updated" });
		},
		onError: (err) => {
			addToast({
				type: "error",
				message: err instanceof Error ? err.message : "Failed to switch engine",
			});
		},
	});

	const setProvider = useCallback(
		(id: string) => {
			setSelectedProviderId(id);
			const p = providers.find((x) => x.id === id);
			setSelectedModel(p?.default_model || "");
			if (p && !p.is_default) setDefaultMutation.mutate(id);
		},
		[providers, setDefaultMutation],
	);

	const setModel = useCallback((model: string) => {
		setSelectedModel(model);
	}, []);

	return {
		providers,
		models,
		activeProvider,
		enabledProviders: providers.filter((p) => p.enabled),
		selectedProviderId,
		selectedModel,
		setProvider,
		setModel,
		isPending: setDefaultMutation.isPending,
	};
}